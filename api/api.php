<?php
/**
 * DaedalusSignal API Router
 * Main entry point for all API requests
 */

// Load libraries
require_once __DIR__ . '/lib/cors.php';
require_once __DIR__ . '/lib/response.php';
require_once __DIR__ . '/lib/database.php';
require_once __DIR__ . '/lib/jwt.php';
require_once __DIR__ . '/lib/auth.php';

// Handle CORS
handle_cors();

// Set content type
header('Content-Type: application/json');

// Parse request
$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];

// Remove /api prefix if present
$uri = preg_replace('#^/api#', '', $uri);

// Route to appropriate handler
try {
    switch (true) {
        // Auth routes
        case preg_match('#^/auth/register$#', $uri) && $method === 'POST':
        case preg_match('#^/auth/login$#', $uri) && $method === 'POST':
        case preg_match('#^/auth/logout$#', $uri) && $method === 'POST':
        case preg_match('#^/auth/forgot-password$#', $uri) && $method === 'POST':
        case preg_match('#^/auth/me$#', $uri):
            require __DIR__ . '/routes/auth.php';
            break;

        // Sources routes
        case preg_match('#^/sources#', $uri):
            require __DIR__ . '/routes/sources.php';
            break;

        // Tags routes
        case preg_match('#^/tags#', $uri):
            require __DIR__ . '/routes/tags.php';
            break;

        // Content routes
        case preg_match('#^/content#', $uri):
            require __DIR__ . '/routes/content.php';
            break;

        // Admin routes
        case preg_match('#^/admin#', $uri):
            require __DIR__ . '/routes/admin.php';
            break;

        // Worker routes
        case preg_match('#^/worker#', $uri):
            require __DIR__ . '/routes/worker.php';
            break;

        // Feedback
        case preg_match('#^/feedback$#', $uri) && $method === 'POST':
            require __DIR__ . '/routes/feedback.php';
            break;

        // Unsubscribe
        case preg_match('#^/unsubscribe#', $uri):
            require __DIR__ . '/routes/unsubscribe.php';
            break;

        // Health check
        case preg_match('#^/health$#', $uri) && $method === 'GET':
            json_response(['status' => 'ok', 'timestamp' => date('c')]);
            break;

        default:
            error_response('Not found', 404);
    }
} catch (PDOException $e) {
    error_log("Database error: " . $e->getMessage());
    error_response('Database error', 500);
} catch (Exception $e) {
    error_log("Server error: " . $e->getMessage());
    error_response('Internal server error', 500);
}
