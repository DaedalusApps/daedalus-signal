<?php
/**
 * CORS Header Configuration
 * Call handle_cors() at the start of api.php
 */

function handle_cors(): void
{
    $allowed_origins = [
        'https://signal.daedalusapps.com',
        'http://localhost:3000',  // dev
        'http://127.0.0.1:3000'   // dev
    ];

    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';

    if (in_array($origin, $allowed_origins)) {
        header("Access-Control-Allow-Origin: $origin");
        header("Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS");
        header("Access-Control-Allow-Headers: Content-Type, Authorization");
        header("Access-Control-Allow-Credentials: true");
        header("Access-Control-Max-Age: 86400"); // 24 hours cache
    }

    // Handle preflight requests
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(204);
        exit;
    }
}
