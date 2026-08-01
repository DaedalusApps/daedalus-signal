<?php
/**
 * Content Routes
 * 
 * GET /api/content - Get paginated content for user's sources
 * GET /api/content/feed - Get latest content feed
 * GET /api/content/digest - Get top items for digest
 * GET /api/content/new-count - Get count of new items since timestamp
 */

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

// Route handling
switch (true) {
    case $uri === '/content' && $method === 'GET':
        handle_get_content();
        break;

    case $uri === '/content/feed' && $method === 'GET':
        handle_get_feed();
        break;

    case $uri === '/content/digest' && $method === 'GET':
        handle_get_digest();
        break;

    case $uri === '/content/new-count' && $method === 'GET':
        handle_get_new_count();
        break;

    default:
        error_response('Not found', 404);
}

/**
 * GET /api/content
 */
function handle_get_content(): void
{
    $user_id = require_auth();

    $page = max(1, (int) ($_GET['page'] ?? 1));
    $per_page = min(50, max(1, (int) ($_GET['per_page'] ?? 20)));
    $source_type = $_GET['source_type'] ?? null;

    $db = Database::getConnection();

    // Get user's source IDs
    $source_ids = get_user_source_ids($db, $user_id);

    if (empty($source_ids)) {
        json_response(['content' => [], 'total' => 0, 'page' => $page, 'per_page' => $per_page, 'pages' => 0]);
        return;
    }

    $placeholders = implode(',', array_fill(0, count($source_ids), '?'));
    $params = $source_ids;

    // Build query
    $where = "c.source_id IN ($placeholders)";
    if ($source_type) {
        $where .= " AND s.source_type = ?";
        $params[] = $source_type;
    }

    // Get total count
    $count_sql = "SELECT COUNT(*) as total FROM contents c JOIN sources s ON c.source_id = s.id WHERE $where";
    $stmt = $db->prepare($count_sql);
    $stmt->execute($params);
    $total = (int) $stmt->fetch()['total'];

    // Get paginated content
    $offset = ($page - 1) * $per_page;
    $sql = "
        SELECT c.*, s.name as source_name, s.url as source_url, s.source_type 
        FROM contents c 
        JOIN sources s ON c.source_id = s.id 
        WHERE $where
        ORDER BY c.relevance_score DESC, c.scraped_at DESC
        LIMIT $per_page OFFSET $offset
    ";
    $stmt = $db->prepare($sql);
    $stmt->execute($params);
    $contents = $stmt->fetchAll();

    json_response([
        'content' => array_map('format_content', $contents),
        'total' => $total,
        'page' => $page,
        'per_page' => $per_page,
        'pages' => (int) ceil($total / $per_page)
    ]);
}

/**
 * GET /api/content/feed
 */
function handle_get_feed(): void
{
    $user_id = require_auth();

    $limit = min(50, max(1, (int) ($_GET['limit'] ?? 10)));

    $db = Database::getConnection();
    $source_ids = get_user_source_ids($db, $user_id);

    if (empty($source_ids)) {
        json_response(['feed' => []]);
        return;
    }

    $placeholders = implode(',', array_fill(0, count($source_ids), '?'));

    $stmt = $db->prepare("
        SELECT c.*, s.name as source_name, s.url as source_url, s.source_type 
        FROM contents c 
        JOIN sources s ON c.source_id = s.id 
        WHERE c.source_id IN ($placeholders)
        ORDER BY c.scraped_at DESC
        LIMIT $limit
    ");
    $stmt->execute($source_ids);
    $contents = $stmt->fetchAll();

    json_response(['feed' => array_map('format_content', $contents)]);
}

/**
 * GET /api/content/digest
 */
function handle_get_digest(): void
{
    $user_id = require_auth();

    $db = Database::getConnection();
    $source_ids = get_user_source_ids($db, $user_id);

    if (empty($source_ids)) {
        json_response(['digest' => []]);
        return;
    }

    $placeholders = implode(',', array_fill(0, count($source_ids), '?'));

    $stmt = $db->prepare("
        SELECT c.*, s.name as source_name, s.url as source_url, s.source_type 
        FROM contents c 
        JOIN sources s ON c.source_id = s.id 
        WHERE c.source_id IN ($placeholders)
        ORDER BY c.relevance_score DESC
        LIMIT 10
    ");
    $stmt->execute($source_ids);
    $contents = $stmt->fetchAll();

    json_response(['digest' => array_map('format_content', $contents)]);
}

/**
 * GET /api/content/new-count
 */
function handle_get_new_count(): void
{
    $user_id = require_auth();

    $since = $_GET['since'] ?? null;
    if (!$since) {
        json_response(['count' => 0]);
        return;
    }

    // Parse ISO timestamp and normalize to UTC (MariaDB warns/truncates
    // on offset-suffixed values compared against a DATETIME column).
    try {
        $since_dt = (new DateTime($since))->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d H:i:s');
    } catch (Exception $e) {
        error_response('Invalid since parameter', 400);
    }

    $db = Database::getConnection();
    $source_ids = get_user_source_ids($db, $user_id);

    if (empty($source_ids)) {
        json_response(['count' => 0]);
        return;
    }

    $placeholders = implode(',', array_fill(0, count($source_ids), '?'));
    $params = $source_ids;
    $params[] = $since_dt;

    $stmt = $db->prepare("
        SELECT COUNT(*) as count FROM contents 
        WHERE source_id IN ($placeholders) AND scraped_at > ?
    ");
    $stmt->execute($params);
    $count = (int) $stmt->fetch()['count'];

    json_response(['count' => $count]);
}

/**
 * Get user's source IDs
 */
function get_user_source_ids(PDO $db, int $user_id): array
{
    $stmt = $db->prepare("SELECT source_id FROM user_sources WHERE user_id = ?");
    $stmt->execute([$user_id]);
    return array_column($stmt->fetchAll(), 'source_id');
}

/**
 * Format content for response
 */
function format_content(array $content): array
{
    return [
        'id' => (int) $content['id'],
        'title' => $content['title'],
        'description' => $content['description'],
        'url' => $content['url'],
        'content_type' => $content['content_type'],
        'source' => [
            'id' => (int) $content['source_id'],
            'name' => $content['source_name'] ?? null,
            'url' => $content['source_url'] ?? null,
            'source_type' => $content['source_type'] ?? null
        ],
        'relevance_score' => (int) $content['relevance_score'],
        'tags' => [], // Could fetch if needed
        'published_at' => $content['published_at'],
        'scraped_at' => $content['scraped_at']
    ];
}
