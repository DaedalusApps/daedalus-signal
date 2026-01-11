<?php
/**
 * Sources Routes
 * 
 * GET    /api/sources - Get user's sources
 * GET    /api/sources/defaults - Get default sources
 * POST   /api/sources - Add source to user
 * DELETE /api/sources/:id - Remove source from user
 */

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

// Config
define('MAX_SOURCES_PER_USER', 20);

// Route handling
switch (true) {
    case $uri === '/sources' && $method === 'GET':
        handle_get_sources();
        break;

    case $uri === '/sources/defaults' && $method === 'GET':
        handle_get_default_sources();
        break;

    case $uri === '/sources' && $method === 'POST':
        handle_add_source();
        break;

    case preg_match('#^/sources/(\d+)$#', $uri, $matches) && $method === 'DELETE':
        handle_remove_source((int) $matches[1]);
        break;

    default:
        error_response('Not found', 404);
}

/**
 * GET /api/sources
 */
function handle_get_sources(): void
{
    $user_id = require_auth();

    $db = Database::getConnection();

    $stmt = $db->prepare("
        SELECT s.* FROM sources s
        JOIN user_sources us ON s.id = us.source_id
        WHERE us.user_id = ?
        ORDER BY s.name
    ");
    $stmt->execute([$user_id]);
    $sources = $stmt->fetchAll();

    json_response(['sources' => array_map('format_source', $sources)]);
}

/**
 * GET /api/sources/defaults
 */
function handle_get_default_sources(): void
{
    $db = Database::getConnection();

    $stmt = $db->prepare("
        SELECT * FROM sources 
        WHERE is_default = 1 AND is_approved = 1
        ORDER BY name
    ");
    $stmt->execute();
    $sources = $stmt->fetchAll();

    json_response(['sources' => array_map('format_source', $sources)]);
}

/**
 * POST /api/sources
 */
function handle_add_source(): void
{
    $user_id = require_auth();
    $data = get_json_body();

    if (!$data || empty($data['name']) || empty($data['url']) || empty($data['source_type'])) {
        error_response('Name, URL, and source_type required', 400);
    }

    $source_type = $data['source_type'];

    // Validate source type
    if (in_array($source_type, ['linkedin', 'github'])) {
        error_response(ucfirst($source_type) . ' sources coming soon!', 400);
    }

    if (!in_array($source_type, ['youtube', 'twitter'])) {
        error_response('Invalid source type. Supported: youtube, twitter', 400);
    }

    $db = Database::getConnection();

    // Check user's source count
    $stmt = $db->prepare("SELECT COUNT(*) as count FROM user_sources WHERE user_id = ?");
    $stmt->execute([$user_id]);
    $count = $stmt->fetch()['count'];

    if ($count >= MAX_SOURCES_PER_USER) {
        error_response("Maximum " . MAX_SOURCES_PER_USER . " sources allowed", 400);
    }

    // Check if source already exists by URL
    $stmt = $db->prepare("SELECT * FROM sources WHERE url = ?");
    $stmt->execute([$data['url']]);
    $existing = $stmt->fetch();

    if ($existing) {
        // Check if user already has this source
        $stmt = $db->prepare("SELECT 1 FROM user_sources WHERE user_id = ? AND source_id = ?");
        $stmt->execute([$user_id, $existing['id']]);

        if (!$stmt->fetch()) {
            // Add association
            $stmt = $db->prepare("INSERT INTO user_sources (user_id, source_id) VALUES (?, ?)");
            $stmt->execute([$user_id, $existing['id']]);
        }

        json_response(['source' => format_source($existing)]);
        return;
    }

    // Create new source
    $stmt = $db->prepare("
        INSERT INTO sources (name, url, source_type, created_at) 
        VALUES (?, ?, ?, NOW())
    ");
    $stmt->execute([$data['name'], $data['url'], $source_type]);
    $source_id = (int) $db->lastInsertId();

    // Add association
    $stmt = $db->prepare("INSERT INTO user_sources (user_id, source_id) VALUES (?, ?)");
    $stmt->execute([$user_id, $source_id]);

    // Get created source
    $stmt = $db->prepare("SELECT * FROM sources WHERE id = ?");
    $stmt->execute([$source_id]);
    $source = $stmt->fetch();

    json_response(['source' => format_source($source)], 201);
}

/**
 * DELETE /api/sources/:id
 */
function handle_remove_source(int $source_id): void
{
    $user_id = require_auth();

    $db = Database::getConnection();

    // Check source exists
    $stmt = $db->prepare("SELECT * FROM sources WHERE id = ?");
    $stmt->execute([$source_id]);
    if (!$stmt->fetch()) {
        error_response('Source not found', 404);
    }

    // Remove association
    $stmt = $db->prepare("DELETE FROM user_sources WHERE user_id = ? AND source_id = ?");
    $stmt->execute([$user_id, $source_id]);

    json_response(['message' => 'Source removed']);
}

/**
 * Format source for response
 */
function format_source(array $source): array
{
    return [
        'id' => (int) $source['id'],
        'name' => $source['name'],
        'url' => $source['url'],
        'source_type' => $source['source_type'],
        'is_default' => (bool) ($source['is_default'] ?? false),
        'last_scraped' => $source['last_scraped']
    ];
}
