<?php
/**
 * Worker Routes
 * Used by DreamHost worker scripts to communicate with the API
 * All routes require HMAC signature verification
 * 
 * GET  /api/worker/sources - Get sources to scrape
 * POST /api/worker/ingest - Submit scraped content
 * GET  /api/worker/digests - Get digest payloads for all users
 * POST /api/worker/digest-sent - Mark digest as sent
 */

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

// Route handling
switch (true) {
    case $uri === '/worker/sources' && $method === 'GET':
        handle_worker_sources();
        break;

    case $uri === '/worker/ingest' && $method === 'POST':
        handle_worker_ingest();
        break;

    case $uri === '/worker/digests' && $method === 'GET':
        handle_worker_digests();
        break;

    case $uri === '/worker/digest-sent' && $method === 'POST':
        handle_worker_digest_sent();
        break;

    default:
        error_response('Not found', 404);
}

/**
 * Verify worker HMAC signature
 */
function verify_worker_signature(): void
{
    $auth_header = $_SERVER['HTTP_X_WORKER_SIGNATURE'] ?? '';

    if (empty($auth_header)) {
        error_response('Worker signature required', 401);
    }

    // Format: "timestamp:signature"
    $parts = explode(':', $auth_header);
    if (count($parts) !== 2) {
        error_response('Invalid signature format', 401);
    }

    [$timestamp, $signature] = $parts;

    // Check timestamp is within 5 minutes
    if (abs(time() - (int) $timestamp) > 300) {
        error_response('Signature expired', 401);
    }

    // Verify signature
    $secret = getenv('SECRET_KEY');
    if (!$secret) {
        error_log('WARNING: SECRET_KEY not set for worker signature verification');
        error_response('Server configuration error', 500);
    }
    $expected = hash_hmac('sha256', $timestamp, $secret);

    if (!hash_equals($expected, $signature)) {
        error_response('Invalid signature', 401);
    }
}

/**
 * GET /api/worker/sources
 */
function handle_worker_sources(): void
{
    verify_worker_signature();

    $db = Database::getConnection();
    $stmt = $db->query("SELECT * FROM sources WHERE is_approved = 1");
    $sources = $stmt->fetchAll();

    json_response([
        'sources' => array_map(function ($s) {
            return [
                'id' => (int) $s['id'],
                'name' => $s['name'],
                'url' => $s['url'],
                'source_type' => $s['source_type'],
                'last_scraped' => $s['last_scraped']
            ];
        }, $sources)
    ]);
}

/**
 * POST /api/worker/ingest
 */
function handle_worker_ingest(): void
{
    verify_worker_signature();

    $data = get_json_body();

    if (!$data) {
        error_response('No data provided', 400);
    }

    $source_id = $data['source_id'] ?? null;
    $content_list = $data['content'] ?? [];

    if (!$source_id) {
        error_response('source_id required', 400);
    }

    $db = Database::getConnection();

    // Verify source exists
    $stmt = $db->prepare("SELECT * FROM sources WHERE id = ?");
    $stmt->execute([$source_id]);
    if (!$stmt->fetch()) {
        error_response('Source not found', 404);
    }

    $added = 0;
    $skipped = 0;

    foreach ($content_list as $item) {
        $url = $item['url'] ?? null;
        if (!$url) {
            $skipped++;
            continue;
        }

        // Deduplication: check if URL exists
        $stmt = $db->prepare("SELECT id FROM contents WHERE url = ?");
        $stmt->execute([$url]);
        if ($stmt->fetch()) {
            $skipped++;
            continue;
        }

        $relevance_score = $item['relevance_score'] ?? 50; // Default score

        // Skip low-relevance content
        if ($relevance_score < 10) {
            $skipped++;
            continue;
        }

        // Parse published_at
        $published_at = null;
        if (!empty($item['published_at'])) {
            $published_at = str_replace('Z', '', $item['published_at']);
        }

        $stmt = $db->prepare("
            INSERT INTO contents (title, description, url, content_type, source_id, relevance_score, published_at, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, NOW())
        ");
        $stmt->execute([
            mb_substr($item['title'] ?? 'Untitled', 0, 500),
            mb_substr($item['description'] ?? '', 0, 2000),
            $url,
            $item['content_type'] ?? 'article',
            $source_id,
            $relevance_score,
            $published_at
        ]);
        $added++;
    }

    // Update source last_scraped
    $db->prepare("UPDATE sources SET last_scraped = NOW() WHERE id = ?")->execute([$source_id]);

    json_response([
        'message' => 'Content ingested successfully',
        'added' => $added,
        'skipped' => $skipped,
        'source_id' => $source_id
    ]);
}

/**
 * GET /api/worker/digests
 */
function handle_worker_digests(): void
{
    verify_worker_signature();

    $db = Database::getConnection();

    // Get blocked emails
    $blocked = [];
    $stmt = $db->query("SELECT email FROM email_blocklist");
    while ($row = $stmt->fetch()) {
        $blocked[$row['email']] = true;
    }

    // Get users with digest enabled
    $stmt = $db->query("SELECT * FROM users WHERE digest_enabled = 1 AND is_active = 1");
    $users = $stmt->fetchAll();

    $digests = [];
    $yesterday = date('Y-m-d H:i:s', strtotime('-1 day'));

    foreach ($users as $user) {
        if (isset($blocked[$user['email']])) {
            continue;
        }

        // Get user's source IDs
        $stmt = $db->prepare("SELECT source_id FROM user_sources WHERE user_id = ?");
        $stmt->execute([$user['id']]);
        $source_ids = array_column($stmt->fetchAll(), 'source_id');

        if (empty($source_ids)) {
            continue;
        }

        $placeholders = implode(',', array_fill(0, count($source_ids), '?'));
        $params = $source_ids;
        $params[] = $yesterday;

        // Get top content from last 24 hours
        $stmt = $db->prepare("
            SELECT * FROM contents 
            WHERE source_id IN ($placeholders) AND scraped_at >= ?
            ORDER BY relevance_score DESC
            LIMIT 10
        ");
        $stmt->execute($params);
        $contents = $stmt->fetchAll();

        if (empty($contents)) {
            continue;
        }

        // Generate simple digest HTML (you could import a template here)
        $digest_html = generate_simple_digest_html($user['email'], $contents);

        $digests[] = [
            'email' => $user['email'],
            'digest_html' => $digest_html,
            'content_count' => count($contents),
            'content_ids' => array_column($contents, 'id')
        ];
    }

    json_response(['digests' => $digests]);
}

/**
 * POST /api/worker/digest-sent
 */
function handle_worker_digest_sent(): void
{
    verify_worker_signature();

    $data = get_json_body();

    if (!$data || empty($data['email'])) {
        error_response('Email required', 400);
    }

    $db = Database::getConnection();

    // Find user
    $stmt = $db->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([$data['email']]);
    $user = $stmt->fetch();

    if (!$user) {
        error_response('User not found', 404);
    }

    $content_ids = implode(',', $data['content_ids'] ?? []);

    // Record digest
    $stmt = $db->prepare("
        INSERT INTO digests (user_id, content_ids, delivery_method, sent_at)
        VALUES (?, ?, 'email', NOW())
    ");
    $stmt->execute([$user['id'], $content_ids]);

    json_response(['message' => 'Digest recorded']);
}

/**
 * Generate simple digest HTML
 */
function generate_simple_digest_html(string $email, array $contents): string
{
    $html = "<html><body>";
    $html .= "<h1>Your Daily Signal Digest</h1>";
    $html .= "<p>Here are your top items for today:</p>";

    foreach ($contents as $content) {
        $html .= "<div style='margin-bottom: 20px; padding: 10px; border-left: 3px solid #007bff;'>";
        $html .= "<h3><a href='" . htmlspecialchars($content['url']) . "'>" . htmlspecialchars($content['title']) . "</a></h3>";
        if ($content['description']) {
            $html .= "<p>" . htmlspecialchars(substr($content['description'], 0, 200)) . "...</p>";
        }
        $html .= "</div>";
    }

    // Unsubscribe link
    $secret = getenv('SECRET_KEY');
    if (!$secret) {
        error_log('WARNING: SECRET_KEY not set for unsubscribe token generation');
        error_response('Server configuration error', 500);
    }
    $token = substr(hash_hmac('sha256', $email, $secret), 0, 32);
    $html .= "<hr><p style='font-size: 12px; color: #666;'>";
    $html .= "<a href='https://signal.daedalusapps.com/api/unsubscribe/$token?email=" . urlencode($email) . "'>Unsubscribe</a>";
    $html .= "</p>";

    $html .= "</body></html>";
    return $html;
}
