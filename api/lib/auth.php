<?php
/**
 * Password and Authentication Helpers
 */

/**
 * Hash a password using bcrypt (PHP default, compatible with Python bcrypt)
 */
function hash_password(string $password): string
{
    return password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
}

/**
 * Verify a password against a hash
 * Works with both PHP and Python bcrypt hashes
 */
function verify_password(string $password, string $hash): bool
{
    return password_verify($password, $hash);
}

/**
 * Verify Cloudflare Turnstile CAPTCHA token
 */
function verify_turnstile(string $token): bool
{
    $secret = getenv('TURNSTILE_SECRET_KEY');

    if (!$secret) {
        // Skip verification if not configured (development mode)
        error_log("Warning: Turnstile not configured, skipping verification");
        return true;
    }

    if (empty($token)) {
        return false;
    }

    $response = file_get_contents('https://challenges.cloudflare.com/turnstile/v0/siteverify', false, stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/x-www-form-urlencoded',
            'content' => http_build_query([
                'secret' => $secret,
                'response' => $token
            ]),
            'timeout' => 10
        ]
    ]));

    if ($response === false) {
        error_log("Turnstile verification failed: could not reach Cloudflare");
        return false;
    }

    $result = json_decode($response, true);
    return $result['success'] ?? false;
}
