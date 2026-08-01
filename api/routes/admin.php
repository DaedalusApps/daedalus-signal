<?php
/**
 * Admin Routes
 * All routes require admin JWT
 * 
 * GET    /api/admin/stats - System statistics
 * GET    /api/admin/users - List all users
 * DELETE /api/admin/users/:id - Delete user
 * GET    /api/admin/sources - All sources with approval status
 * POST   /api/admin/sources/:id/approve - Approve source as default
 * GET    /api/admin/tags - All tags
 * POST   /api/admin/tags/:id/approve - Approve tag as default
 * GET    /api/admin/feedback - All feedback
 * GET    /api/admin/blocklist - Blocked emails
 * DELETE /api/admin/blocklist/:id - Unblock email
 * GET    /api/admin/test-email-payload - Signed payload for test email
 * GET    /api/admin/trigger-scrape-payload - Signed payload for scraper
 * GET    /api/admin/trigger-mailer-payload - Signed payload for mailer
 * GET    /api/admin/logs-payload - Signed payload for logs
 */

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

// Route handling
switch (true) {
    case $uri === '/admin/stats' && $method === 'GET':
        handle_stats();
        break;

    case $uri === '/admin/users' && $method === 'GET':
        handle_get_users();
        break;

    case preg_match('#^/admin/users/(\d+)$#', $uri, $matches) && $method === 'DELETE':
        handle_delete_user((int) $matches[1]);
        break;

    case $uri === '/admin/sources' && $method === 'GET':
        handle_get_all_sources();
        break;

    case preg_match('#^/admin/sources/(\d+)/approve$#', $uri, $matches) && $method === 'POST':
        handle_approve_source((int) $matches[1]);
        break;

    case $uri === '/admin/tags' && $method === 'GET':
        handle_get_all_tags();
        break;

    case preg_match('#^/admin/tags/(\d+)/approve$#', $uri, $matches) && $method === 'POST':
        handle_approve_tag((int) $matches[1]);
        break;

    case $uri === '/admin/feedback' && $method === 'GET':
        handle_get_feedback();
        break;

    case $uri === '/admin/blocklist' && $method === 'GET':
        handle_get_blocklist();
        break;

    case preg_match('#^/admin/blocklist/(\d+)$#', $uri, $matches) && $method === 'DELETE':
        handle_unblock_email((int) $matches[1]);
        break;

    case $uri === '/admin/test-email-payload' && $method === 'GET':
        handle_test_email_payload();
        break;

    case $uri === '/admin/trigger-scrape-payload' && $method === 'GET':
        handle_trigger_scrape_payload();
        break;

    case $uri === '/admin/trigger-mailer-payload' && $method === 'GET':
        handle_trigger_mailer_payload();
        break;

    case $uri === '/admin/get-logs-payload' && $method === 'GET':
        handle_logs_payload();
        break;

    default:
        error_response('Not found', 404);
}

/**
 * GET /api/admin/stats
 */
function handle_stats(): void
{
    require_admin();

    $db = Database::getConnection();

    $stats = [
        'users' => (int) $db->query("SELECT COUNT(*) FROM users")->fetchColumn(),
        'sources' => (int) $db->query("SELECT COUNT(*) FROM sources")->fetchColumn(),
        'tags' => (int) $db->query("SELECT COUNT(*) FROM tags")->fetchColumn(),
        'contents' => (int) $db->query("SELECT COUNT(*) FROM contents")->fetchColumn(),
        'feedback_pending' => (int) $db->query("SELECT COUNT(*) FROM feedback WHERE status = 'pending'")->fetchColumn()
    ];

    json_response(['stats' => $stats]);
}

/**
 * GET /api/admin/users
 */
function handle_get_users(): void
{
    require_admin();

    $db = Database::getConnection();
    $stmt = $db->query("SELECT * FROM users ORDER BY created_at DESC");
    $users = $stmt->fetchAll();

    json_response(['users' => array_map('format_admin_user', $users)]);
}

/**
 * DELETE /api/admin/users/:id
 */
function handle_delete_user(int $user_id): void
{
    require_admin();

    $db = Database::getConnection();

    // Get user
    $stmt = $db->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();

    if (!$user) {
        error_response('User not found', 404);
    }

    if ($user['is_admin']) {
        error_response('Cannot delete admin users', 400);
    }

    // Delete associations and related data
    $db->prepare("DELETE FROM user_sources WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM user_tags WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM digests WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM feedback WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM verification_codes WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM users WHERE id = ?")->execute([$user_id]);

    json_response(['message' => 'User deleted']);
}

/**
 * GET /api/admin/sources
 */
function handle_get_all_sources(): void
{
    require_admin();

    $db = Database::getConnection();
    $stmt = $db->query("SELECT * FROM sources ORDER BY created_at DESC");
    $sources = $stmt->fetchAll();

    json_response(['sources' => array_map('format_admin_source', $sources)]);
}

/**
 * POST /api/admin/sources/:id/approve
 */
function handle_approve_source(int $source_id): void
{
    require_admin();
    $data = get_json_body() ?? [];

    $db = Database::getConnection();

    $is_default = isset($data['is_default']) ? ($data['is_default'] ? 1 : 0) : 1;
    $is_approved = isset($data['is_approved']) ? ($data['is_approved'] ? 1 : 0) : 1;

    $stmt = $db->prepare("UPDATE sources SET is_default = ?, is_approved = ? WHERE id = ?");
    $stmt->execute([$is_default, $is_approved, $source_id]);

    if ($stmt->rowCount() === 0) {
        error_response('Source not found', 404);
    }

    json_response(['message' => 'Source updated']);
}

/**
 * GET /api/admin/tags
 */
function handle_get_all_tags(): void
{
    require_admin();

    $db = Database::getConnection();
    $stmt = $db->query("SELECT * FROM tags ORDER BY name");
    $tags = $stmt->fetchAll();

    json_response(['tags' => array_map('format_admin_tag', $tags)]);
}

/**
 * POST /api/admin/tags/:id/approve
 */
function handle_approve_tag(int $tag_id): void
{
    require_admin();
    $data = get_json_body() ?? [];

    $db = Database::getConnection();

    $is_default = isset($data['is_default']) ? ($data['is_default'] ? 1 : 0) : 1;

    $stmt = $db->prepare("UPDATE tags SET is_default = ? WHERE id = ?");
    $stmt->execute([$is_default, $tag_id]);

    if ($stmt->rowCount() === 0) {
        error_response('Tag not found', 404);
    }

    json_response(['message' => 'Tag updated']);
}

/**
 * GET /api/admin/feedback
 */
function handle_get_feedback(): void
{
    require_admin();

    $db = Database::getConnection();
    $stmt = $db->query("SELECT * FROM feedback ORDER BY created_at DESC");
    $feedback = $stmt->fetchAll();

    json_response(['feedback' => $feedback]);
}

/**
 * GET /api/admin/blocklist
 */
function handle_get_blocklist(): void
{
    require_admin();

    $db = Database::getConnection();
    $stmt = $db->query("SELECT * FROM email_blocklist ORDER BY blocked_at DESC");
    $blocklist = $stmt->fetchAll();

    json_response(['blocklist' => $blocklist]);
}

/**
 * DELETE /api/admin/blocklist/:id
 */
function handle_unblock_email(int $blocklist_id): void
{
    require_admin();

    $db = Database::getConnection();

    // Get the email first
    $stmt = $db->prepare("SELECT email FROM email_blocklist WHERE id = ?");
    $stmt->execute([$blocklist_id]);
    $entry = $stmt->fetch();

    if (!$entry) {
        error_response('Blocklist entry not found', 404);
    }

    // Delete from blocklist
    $db->prepare("DELETE FROM email_blocklist WHERE id = ?")->execute([$blocklist_id]);

    // Re-enable digest for user if they exist
    $db->prepare("UPDATE users SET digest_enabled = 1 WHERE email = ?")->execute([$entry['email']]);

    json_response(['message' => 'Email unblocked', 'email' => $entry['email']]);
}

/**
 * Generate HMAC signature for worker payloads
 */
function generate_hmac(string $data): string
{
    $secret = getenv('SECRET_KEY');
    if (!$secret) {
        error_log('WARNING: SECRET_KEY not set for admin HMAC generation');
        error_response('Server configuration error', 500);
    }
    return hash_hmac('sha256', $data, $secret);
}

/**
 * GET /api/admin/test-email-payload
 */
function handle_test_email_payload(): void
{
    $user_id = require_admin();

    // Get admin email from database
    $db = Database::getConnection();
    $stmt = $db->prepare("SELECT email FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();

    if (!$user) {
        error_response('Admin user not found', 404);
    }

    $timestamp = time();
    $payload = [
        'action' => 'test_email',
        'email' => $user['email'],
        'timestamp' => $timestamp
    ];
    $payload_json = json_encode($payload);
    // Worker verifies: hash_hmac('sha256', "$timestamp:$payload_json", $secret)
    $signature = generate_hmac($timestamp . ':' . $payload_json);

    json_response([
        'payload' => $payload,
        'payload_json' => $payload_json,
        'signature' => $signature
    ]);
}

/**
 * GET /api/admin/trigger-scrape-payload
 */
function handle_trigger_scrape_payload(): void
{
    require_admin();

    $timestamp = time();
    $payload = [
        'action' => 'run_scrapers',
        'timestamp' => $timestamp
    ];
    $payload_json = json_encode($payload);
    $signature = generate_hmac($timestamp . ':' . $payload_json);

    json_response([
        'payload' => $payload,
        'payload_json' => $payload_json,
        'signature' => $signature
    ]);
}

/**
 * GET /api/admin/trigger-mailer-payload
 */
function handle_trigger_mailer_payload(): void
{
    require_admin();

    $timestamp = time();
    $payload = [
        'action' => 'run_mailer',
        'timestamp' => $timestamp
    ];
    $payload_json = json_encode($payload);
    $signature = generate_hmac($timestamp . ':' . $payload_json);

    json_response([
        'payload' => $payload,
        'payload_json' => $payload_json,
        'signature' => $signature
    ]);
}

/**
 * GET /api/admin/get-logs-payload
 */
function handle_logs_payload(): void
{
    require_admin();

    $log_type = $_GET['log_type'] ?? 'scraper';
    if (!in_array($log_type, ['scraper', 'mailer'])) {
        error_response('Invalid log_type. Must be scraper or mailer', 400);
    }

    $timestamp = time();
    $payload = [
        'action' => 'get_logs',
        'log_type' => $log_type,
        'timestamp' => $timestamp
    ];
    $payload_json = json_encode($payload);
    $signature = generate_hmac($timestamp . ':' . $payload_json);

    json_response([
        'payload' => $payload,
        'payload_json' => $payload_json,
        'signature' => $signature
    ]);
}

/**
 * Format user for admin response
 */
function format_admin_user(array $user): array
{
    return [
        'id' => (int) $user['id'],
        'email' => $user['email'],
        'is_admin' => (bool) $user['is_admin'],
        'is_active' => (bool) $user['is_active'],
        'email_verified' => (bool) $user['email_verified'],
        'digest_enabled' => (bool) $user['digest_enabled'],
        'onboarding_complete' => (bool) $user['onboarding_complete'],
        'created_at' => $user['created_at'],
        'updated_at' => $user['updated_at']
    ];
}

/**
 * Format source for admin response
 */
function format_admin_source(array $source): array
{
    return [
        'id' => (int) $source['id'],
        'name' => $source['name'],
        'url' => $source['url'],
        'source_type' => $source['source_type'],
        'is_default' => (bool) $source['is_default'],
        'is_approved' => (bool) $source['is_approved'],
        'last_scraped' => $source['last_scraped'],
        'created_at' => $source['created_at']
    ];
}

/**
 * Format tag for admin response
 */
function format_admin_tag(array $tag): array
{
    return [
        'id' => (int) $tag['id'],
        'name' => $tag['name'],
        'category' => $tag['category'],
        'is_default' => (bool) $tag['is_default'],
        'created_at' => $tag['created_at']
    ];
}
