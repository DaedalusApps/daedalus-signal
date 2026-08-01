<?php
/**
 * JWT Token Management
 * Using firebase/php-jwt library
 */

require_once __DIR__ . '/../vendor/autoload.php';

use Firebase\JWT\JWT;
use Firebase\JWT\Key;
use Firebase\JWT\ExpiredException;

define('JWT_SECRET', getenv('JWT_SECRET'));
define('JWT_ALGORITHM', 'HS256');
define('ACCESS_TOKEN_EXPIRY', 3600);      // 1 hour
define('REFRESH_TOKEN_EXPIRY', 604800);   // 7 days

// Validate JWT_SECRET is set - refuse to sign/verify tokens without it
if (!JWT_SECRET) {
    error_log('CRITICAL: JWT_SECRET environment variable not set');
    throw new RuntimeException('JWT_SECRET environment variable must be set');
}

/**
 * Create an access token for a user
 */
function create_access_token(int $user_id, bool $is_admin = false): string
{
    $payload = [
        'iss' => 'api.signal.daedalusapps.com',
        'sub' => $user_id,
        'iat' => time(),
        'exp' => time() + ACCESS_TOKEN_EXPIRY,
        'admin' => $is_admin
    ];
    return JWT::encode($payload, JWT_SECRET, JWT_ALGORITHM);
}

/**
 * Create a refresh token for a user
 */
function create_refresh_token(int $user_id): string
{
    $payload = [
        'iss' => 'api.signal.daedalusapps.com',
        'sub' => $user_id,
        'iat' => time(),
        'exp' => time() + REFRESH_TOKEN_EXPIRY,
        'type' => 'refresh'
    ];
    return JWT::encode($payload, JWT_SECRET, JWT_ALGORITHM);
}

/**
 * Verify and decode an access token
 * Returns the decoded payload or null if invalid/expired
 */
function verify_access_token(string $token): ?object
{
    try {
        return JWT::decode($token, new Key(JWT_SECRET, JWT_ALGORITHM));
    } catch (ExpiredException $e) {
        return null; // Token expired
    } catch (Exception $e) {
        return null; // Invalid token
    }
}

/**
 * Get user ID from Authorization header
 * Returns user_id or null if not authenticated
 */
function get_user_from_request(): ?int
{
    $auth_header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';

    // Also check for Apache's workaround
    if (empty($auth_header) && function_exists('apache_request_headers')) {
        $headers = apache_request_headers();
        $auth_header = $headers['Authorization'] ?? '';
    }

    if (preg_match('/Bearer\s+(\S+)/', $auth_header, $matches)) {
        $decoded = verify_access_token($matches[1]);
        return $decoded ? (int) $decoded->sub : null;
    }
    return null;
}

/**
 * Check if user is admin from Authorization header
 */
function is_admin_from_request(): bool
{
    $auth_header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';

    if (empty($auth_header) && function_exists('apache_request_headers')) {
        $headers = apache_request_headers();
        $auth_header = $headers['Authorization'] ?? '';
    }

    if (preg_match('/Bearer\s+(\S+)/', $auth_header, $matches)) {
        $decoded = verify_access_token($matches[1]);
        return $decoded && isset($decoded->admin) && $decoded->admin === true;
    }
    return false;
}

/**
 * Require authentication - returns user_id or sends 401 response
 */
function require_auth(): int
{
    $user_id = get_user_from_request();
    if (!$user_id) {
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Authentication required']);
        exit;
    }
    return $user_id;
}

/**
 * Require admin - returns user_id or sends 403 response
 */
function require_admin(): int
{
    $user_id = require_auth();
    if (!is_admin_from_request()) {
        http_response_code(403);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Admin access required']);
        exit;
    }
    return $user_id;
}
