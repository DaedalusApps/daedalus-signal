<?php
/**
 * Tags Routes
 * 
 * GET    /api/tags - Get user's tags
 * GET    /api/tags/defaults - Get default tags
 * POST   /api/tags - Add tag to user
 * DELETE /api/tags/:id - Remove tag from user
 */

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

// Config
define('MAX_TAGS_PER_USER', 50);

// Route handling
switch (true) {
    case $uri === '/tags' && $method === 'GET':
        handle_get_tags();
        break;

    case $uri === '/tags/defaults' && $method === 'GET':
        handle_get_default_tags();
        break;

    case $uri === '/tags' && $method === 'POST':
        handle_add_tag();
        break;

    case preg_match('#^/tags/(\d+)$#', $uri, $matches) && $method === 'DELETE':
        handle_remove_tag((int) $matches[1]);
        break;

    default:
        error_response('Not found', 404);
}

/**
 * GET /api/tags
 */
function handle_get_tags(): void
{
    $user_id = require_auth();

    $db = Database::getConnection();

    $stmt = $db->prepare("
        SELECT t.* FROM tags t
        JOIN user_tags ut ON t.id = ut.tag_id
        WHERE ut.user_id = ?
        ORDER BY t.name
    ");
    $stmt->execute([$user_id]);
    $tags = $stmt->fetchAll();

    json_response(['tags' => array_map('format_tag', $tags)]);
}

/**
 * GET /api/tags/defaults
 */
function handle_get_default_tags(): void
{
    $db = Database::getConnection();

    $stmt = $db->prepare("SELECT * FROM tags WHERE is_default = 1 ORDER BY name");
    $stmt->execute();
    $tags = $stmt->fetchAll();

    json_response(['tags' => array_map('format_tag', $tags)]);
}

/**
 * POST /api/tags
 */
function handle_add_tag(): void
{
    $user_id = require_auth();
    $data = get_json_body();

    if (!$data || empty($data['name'])) {
        error_response('Tag name required', 400);
    }

    $db = Database::getConnection();

    // Check user's tag count
    $stmt = $db->prepare("SELECT COUNT(*) as count FROM user_tags WHERE user_id = ?");
    $stmt->execute([$user_id]);
    $count = $stmt->fetch()['count'];

    if ($count >= MAX_TAGS_PER_USER) {
        error_response("Maximum " . MAX_TAGS_PER_USER . " tags allowed", 400);
    }

    $tag_name = strtolower(trim($data['name']));

    // Check if tag already exists
    $stmt = $db->prepare("SELECT * FROM tags WHERE name = ?");
    $stmt->execute([$tag_name]);
    $existing = $stmt->fetch();

    if ($existing) {
        // Check if user already has this tag
        $stmt = $db->prepare("SELECT 1 FROM user_tags WHERE user_id = ? AND tag_id = ?");
        $stmt->execute([$user_id, $existing['id']]);

        if (!$stmt->fetch()) {
            // Add association
            $stmt = $db->prepare("INSERT INTO user_tags (user_id, tag_id) VALUES (?, ?)");
            $stmt->execute([$user_id, $existing['id']]);
        }

        json_response(['tag' => format_tag($existing)]);
        return;
    }

    // Create new tag
    $stmt = $db->prepare("
        INSERT INTO tags (name, category, created_at) 
        VALUES (?, ?, NOW())
    ");
    $stmt->execute([$tag_name, $data['category'] ?? null]);
    $tag_id = (int) $db->lastInsertId();

    // Add association
    $stmt = $db->prepare("INSERT INTO user_tags (user_id, tag_id) VALUES (?, ?)");
    $stmt->execute([$user_id, $tag_id]);

    // Get created tag
    $stmt = $db->prepare("SELECT * FROM tags WHERE id = ?");
    $stmt->execute([$tag_id]);
    $tag = $stmt->fetch();

    json_response(['tag' => format_tag($tag)], 201);
}

/**
 * DELETE /api/tags/:id
 */
function handle_remove_tag(int $tag_id): void
{
    $user_id = require_auth();

    $db = Database::getConnection();

    // Check tag exists
    $stmt = $db->prepare("SELECT * FROM tags WHERE id = ?");
    $stmt->execute([$tag_id]);
    if (!$stmt->fetch()) {
        error_response('Tag not found', 404);
    }

    // Remove association
    $stmt = $db->prepare("DELETE FROM user_tags WHERE user_id = ? AND tag_id = ?");
    $stmt->execute([$user_id, $tag_id]);

    json_response(['message' => 'Tag removed']);
}

/**
 * Format tag for response
 */
function format_tag(array $tag): array
{
    return [
        'id' => (int) $tag['id'],
        'name' => $tag['name'],
        'category' => $tag['category'],
        'is_default' => (bool) ($tag['is_default'] ?? false)
    ];
}
