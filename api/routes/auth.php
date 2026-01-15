<?php
/**
 * Authentication Routes
 *
 * POST /api/auth/register - Register new user
 * POST /api/auth/login - Login user
 * POST /api/auth/logout - Logout user (client-side)
 * POST /api/auth/forgot-password - Request password reset (sends magic link)
 * GET  /api/auth/reset-password/:token - Validate reset token
 * POST /api/auth/reset-password - Reset password with token
 * GET  /api/auth/me - Get current user
 * PATCH /api/auth/me - Update current user settings
 * DELETE /api/auth/me - Delete account
 */

require_once __DIR__ . '/../lib/email.php';

$uri = preg_replace('#^/api#', '', parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
$method = $_SERVER['REQUEST_METHOD'];

// Route handling
switch (true) {
    case $uri === '/auth/register' && $method === 'POST':
        handle_register();
        break;

    case $uri === '/auth/login' && $method === 'POST':
        handle_login();
        break;

    case $uri === '/auth/logout' && $method === 'POST':
        handle_logout();
        break;

    case $uri === '/auth/forgot-password' && $method === 'POST':
        handle_forgot_password();
        break;

    case preg_match('#^/auth/reset-password/([a-f0-9]+)$#', $uri, $matches) && $method === 'GET':
        handle_validate_reset_token($matches[1]);
        break;

    case $uri === '/auth/reset-password' && $method === 'POST':
        handle_reset_password();
        break;

    case $uri === '/auth/me' && $method === 'GET':
        handle_get_me();
        break;

    case $uri === '/auth/me' && $method === 'PATCH':
        handle_update_me();
        break;

    case $uri === '/auth/me' && $method === 'DELETE':
        handle_delete_account();
        break;

    default:
        error_response('Not found', 404);
}

/**
 * POST /api/auth/register
 */
function handle_register(): void
{
    $data = get_json_body();

    if (!$data || empty($data['email']) || empty($data['password'])) {
        error_response('Email and password required', 400);
    }

    $email = strtolower(trim($data['email']));
    $password = $data['password'];
    $turnstile_token = $data['turnstile_token'] ?? '';

    // Verify Turnstile CAPTCHA
    if (getenv('TURNSTILE_SECRET_KEY') && empty($turnstile_token)) {
        error_response('CAPTCHA verification required', 400);
    }

    if (!verify_turnstile($turnstile_token)) {
        error_response('CAPTCHA verification failed', 400);
    }

    if (strlen($password) < 8) {
        error_response('Password must be at least 8 characters', 400);
    }

    $db = Database::getConnection();

    // Check if email already exists
    $stmt = $db->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([$email]);
    if ($stmt->fetch()) {
        error_response('Email already registered', 409);
    }

    // Create user
    $stmt = $db->prepare("
        INSERT INTO users (email, password_hash, email_verified, created_at, updated_at) 
        VALUES (?, ?, 1, NOW(), NOW())
    ");
    $stmt->execute([$email, hash_password($password)]);
    $user_id = (int) $db->lastInsertId();

    // Get user data
    $stmt = $db->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();

    // Create JWT token
    $token = create_access_token($user_id, (bool) $user['is_admin']);

    json_response([
        'message' => 'Registration successful',
        'token' => $token,
        'user' => format_user($user)
    ], 201);
}

/**
 * POST /api/auth/login
 */
function handle_login(): void
{
    $data = get_json_body();

    if (!$data || empty($data['email']) || empty($data['password'])) {
        error_response('Email and password required', 400);
    }

    $email = strtolower(trim($data['email']));
    $password = $data['password'];

    $db = Database::getConnection();

    $stmt = $db->prepare("SELECT * FROM users WHERE email = ?");
    $stmt->execute([$email]);
    $user = $stmt->fetch();

    if (!$user || !verify_password($password, $user['password_hash'])) {
        error_response('Invalid credentials', 401);
    }

    if (!$user['is_active']) {
        error_response('Account is disabled', 403);
    }

    // Create JWT token
    $token = create_access_token((int) $user['id'], (bool) $user['is_admin']);

    json_response([
        'token' => $token,
        'user' => format_user($user)
    ]);
}

/**
 * POST /api/auth/logout
 */
function handle_logout(): void
{
    // JWT is stateless - logout is handled client-side by removing the token
    json_response(['message' => 'Logged out successfully']);
}

/**
 * POST /api/auth/forgot-password
 * Request password reset - sends magic link via email
 */
function handle_forgot_password(): void
{
    $data = get_json_body();

    if (!$data || empty($data['email'])) {
        error_response('Email required', 400);
    }

    $email = strtolower(trim($data['email']));

    $db = Database::getConnection();

    // Lookup user by email
    $stmt = $db->prepare("SELECT id, email FROM users WHERE email = ?");
    $stmt->execute([$email]);
    $user = $stmt->fetch();

    // Always return success for security (don't reveal if email exists)
    if (!$user) {
        json_response([
            'message' => 'If an account exists with this email, a reset link has been sent'
        ]);
        return;
    }

    // Delete any existing tokens for this user
    $stmt = $db->prepare("DELETE FROM password_reset_tokens WHERE user_id = ?");
    $stmt->execute([$user['id']]);

    // Generate token using selector+verifier pattern for efficient indexed lookup
    // Selector: 16 hex chars (8 bytes) - stored plaintext for indexed lookup
    // Verifier: 48 hex chars (24 bytes) - stored as hash for security
    $selector = bin2hex(random_bytes(8));
    $verifier = bin2hex(random_bytes(24));
    $token = $selector . $verifier;
    $verifier_hash = hash_password($verifier);
    $expires_at = date('Y-m-d H:i:s', strtotime('+15 minutes'));

    // Store token in database
    $stmt = $db->prepare("
        INSERT INTO password_reset_tokens (user_id, selector, verifier_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?, NOW())
    ");
    $stmt->execute([$user['id'], $selector, $verifier_hash, $expires_at]);

    // Build reset link
    $frontend_url = getenv('FRONTEND_URL') ?: 'https://signal.daedalusapps.com';
    $reset_link = "{$frontend_url}/reset-password?token={$token}";

    // Send email (use email prefix as name)
    $name = explode('@', $user['email'])[0];
    $email_sent = send_password_reset_email($user['email'], $name, $reset_link);

    if (!$email_sent) {
        error_log("Failed to send password reset email to: {$user['email']}");
    }

    json_response([
        'message' => 'If an account exists with this email, a reset link has been sent'
    ]);
}

/**
 * GET /api/auth/reset-password/:token
 * Validate if a password reset token is valid and not expired
 */
function handle_validate_reset_token(string $token): void
{
    // Token must be 64 hex chars (16 selector + 48 verifier)
    if (strlen($token) !== 64) {
        json_response(['valid' => false]);
        return;
    }

    $selector = substr($token, 0, 16);
    $verifier = substr($token, 16);

    $db = Database::getConnection();

    // Lookup by selector (indexed) - only fetch one row
    $stmt = $db->prepare("
        SELECT * FROM password_reset_tokens
        WHERE selector = ? AND expires_at > NOW() AND used_at IS NULL
    ");
    $stmt->execute([$selector]);
    $reset_token = $stmt->fetch();

    if (!$reset_token || !verify_password($verifier, $reset_token['verifier_hash'])) {
        json_response(['valid' => false]);
        return;
    }

    json_response(['valid' => true]);
}

/**
 * POST /api/auth/reset-password
 * Reset password using valid token
 */
function handle_reset_password(): void
{
    $data = get_json_body();

    if (!$data || empty($data['token']) || empty($data['password'])) {
        error_response('Token and password are required', 400);
    }

    $token = $data['token'];
    $password = $data['password'];

    // Token must be 64 hex chars (16 selector + 48 verifier)
    if (strlen($token) !== 64) {
        error_response('Invalid or expired reset token', 400);
    }

    // Validate password strength
    if (strlen($password) < 8) {
        error_response('Password must be at least 8 characters', 400);
    }

    $selector = substr($token, 0, 16);
    $verifier = substr($token, 16);

    $db = Database::getConnection();

    // Lookup by selector (indexed) - only fetch one row
    $stmt = $db->prepare("
        SELECT * FROM password_reset_tokens
        WHERE selector = ? AND expires_at > NOW() AND used_at IS NULL
    ");
    $stmt->execute([$selector]);
    $matched_token = $stmt->fetch();

    if (!$matched_token || !verify_password($verifier, $matched_token['verifier_hash'])) {
        error_response('Invalid or expired reset token', 400);
    }

    // Update user's password (CASCADE ensures token's user_id is valid)
    $stmt = $db->prepare("UPDATE users SET password_hash = ?, updated_at = NOW() WHERE id = ?");
    $stmt->execute([hash_password($password), $matched_token['user_id']]);

    // Mark token as used
    $stmt = $db->prepare("UPDATE password_reset_tokens SET used_at = NOW() WHERE id = ?");
    $stmt->execute([$matched_token['id']]);

    // Delete all other tokens for this user
    $stmt = $db->prepare("DELETE FROM password_reset_tokens WHERE user_id = ? AND id != ?");
    $stmt->execute([$matched_token['user_id'], $matched_token['id']]);

    json_response(['message' => 'Password reset successful']);
}

/**
 * GET /api/auth/me
 */
function handle_get_me(): void
{
    $user_id = require_auth();

    $db = Database::getConnection();
    $stmt = $db->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();

    if (!$user) {
        error_response('User not found', 404);
    }

    json_response(['user' => format_user($user)]);
}

/**
 * PATCH /api/auth/me
 */
function handle_update_me(): void
{
    $user_id = require_auth();
    $data = get_json_body();

    $db = Database::getConnection();

    // Get current user
    $stmt = $db->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();

    if (!$user) {
        error_response('User not found', 404);
    }

    // Build update query
    $updates = [];
    $params = [];

    if (isset($data['digest_enabled'])) {
        $updates[] = "digest_enabled = ?";
        $params[] = $data['digest_enabled'] ? 1 : 0;
    }

    if (isset($data['onboarding_complete'])) {
        $updates[] = "onboarding_complete = ?";
        $params[] = $data['onboarding_complete'] ? 1 : 0;
    }

    if (!empty($updates)) {
        $updates[] = "updated_at = NOW()";
        $params[] = $user_id;

        $sql = "UPDATE users SET " . implode(', ', $updates) . " WHERE id = ?";
        $stmt = $db->prepare($sql);
        $stmt->execute($params);
    }

    // Return updated user
    $stmt = $db->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();

    json_response(['user' => format_user($user)]);
}

/**
 * DELETE /api/auth/me
 */
function handle_delete_account(): void
{
    $user_id = require_auth();

    $db = Database::getConnection();

    // Get user
    $stmt = $db->prepare("SELECT * FROM users WHERE id = ?");
    $stmt->execute([$user_id]);
    $user = $stmt->fetch();

    if (!$user) {
        error_response('User not found', 404);
    }

    if ($user['is_admin']) {
        error_response('Admin accounts cannot be deleted this way', 400);
    }

    $email = $user['email'];

    // Delete associations
    $db->prepare("DELETE FROM user_sources WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM user_tags WHERE user_id = ?")->execute([$user_id]);

    // Delete related records
    $db->prepare("DELETE FROM digests WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM feedback WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM verification_codes WHERE user_id = ?")->execute([$user_id]);
    $db->prepare("DELETE FROM password_reset_tokens WHERE user_id = ?")->execute([$user_id]);

    // Delete user
    $db->prepare("DELETE FROM users WHERE id = ?")->execute([$user_id]);

    json_response(['message' => "Account $email deleted successfully"]);
}

/**
 * Format user array for response (exclude sensitive data)
 */
function format_user(array $user): array
{
    return [
        'id' => (int) $user['id'],
        'email' => $user['email'],
        'is_admin' => (bool) $user['is_admin'],
        'email_verified' => (bool) $user['email_verified'],
        'digest_enabled' => (bool) $user['digest_enabled'],
        'onboarding_complete' => (bool) $user['onboarding_complete'],
        'created_at' => $user['created_at']
    ];
}
