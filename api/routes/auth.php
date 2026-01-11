<?php
/**
 * Authentication Routes
 * 
 * POST /api/auth/register - Register new user
 * POST /api/auth/login - Login user
 * POST /api/auth/logout - Logout user (client-side)
 * POST /api/auth/forgot-password - Submit password reset request
 * GET  /api/auth/me - Get current user
 * PATCH /api/auth/me - Update current user settings
 * DELETE /api/auth/me - Delete account
 */

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
 */
function handle_forgot_password(): void
{
    $data = get_json_body();

    if (!$data || empty($data['email'])) {
        error_response('Email required', 400);
    }

    $email = strtolower(trim($data['email']));
    $message = trim($data['message'] ?? '');

    $db = Database::getConnection();

    // Find user (optional - we still create feedback even if user doesn't exist)
    $stmt = $db->prepare("SELECT id FROM users WHERE email = ?");
    $stmt->execute([$email]);
    $user = $stmt->fetch();
    $user_id = $user ? (int) $user['id'] : null;

    // Create feedback entry for admin to review
    $stmt = $db->prepare("
        INSERT INTO feedback (user_id, email, message, feedback_type, status, created_at)
        VALUES (?, ?, ?, 'password_reset', 'pending', NOW())
    ");
    $stmt->execute([
        $user_id,
        $email,
        $message ?: 'Password reset requested'
    ]);

    json_response([
        'message' => 'Your password reset request has been submitted. An administrator will review it and contact you.'
    ]);
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
