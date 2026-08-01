<?php
/**
 * Unsubscribe Routes
 * 
 * GET /api/unsubscribe/:token?email=... - Unsubscribe from digest emails
 */

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

if (preg_match('#^/unsubscribe/([a-f0-9]+)$#', $uri, $matches) && $method === 'GET') {
    handle_unsubscribe($matches[1]);
} else {
    error_response('Not found', 404);
}

/**
 * GET /api/unsubscribe/:token
 */
function handle_unsubscribe(string $token): void
{
    $email = strtolower(trim($_GET['email'] ?? ''));

    if (empty($email)) {
        error_response('Email required', 400);
    }

    // Verify token
    if (!verify_unsubscribe_token($email, $token)) {
        error_response('Invalid or expired unsubscribe link', 403);
    }

    $db = Database::getConnection();

    // Check if already blocked
    $stmt = $db->prepare("SELECT id FROM email_blocklist WHERE email = ?");
    $stmt->execute([$email]);
    if ($stmt->fetch()) {
        json_response(['message' => "$email is already unsubscribed"]);
        return;
    }

    // Add to blocklist
    $stmt = $db->prepare("
        INSERT INTO email_blocklist (email, reason, blocked_at)
        VALUES (?, 'user_unsubscribed', NOW())
    ");
    $stmt->execute([$email]);

    // Disable digest for user if they have an account
    $db->prepare("UPDATE users SET digest_enabled = 0 WHERE email = ?")->execute([$email]);

    json_response([
        'message' => "$email has been unsubscribed from digest emails",
        'email' => $email
    ]);
}

/**
 * Generate unsubscribe token
 */
function generate_unsubscribe_token(string $email): string
{
    $secret = getenv('SECRET_KEY');
    if (!$secret) {
        error_log('WARNING: SECRET_KEY not set for unsubscribe token generation');
        error_response('Server configuration error', 500);
    }
    return substr(hash_hmac('sha256', $email, $secret), 0, 32);
}

/**
 * Verify unsubscribe token
 */
function verify_unsubscribe_token(string $email, string $token): bool
{
    $expected = generate_unsubscribe_token($email);
    return hash_equals($expected, $token);
}
