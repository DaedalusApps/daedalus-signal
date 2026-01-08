<?php
/**
 * DreamHost PHP Shim for browser-triggered test emails
 * Receives signed payload from frontend, sends email via local PHP mail
 *
 * Deployment:
 * 1. Upload this file to your DreamHost web directory
 * 2. Set SECRET_KEY environment variable (must match PA's SECRET_KEY)
 * 3. Configure allowed origins below
 */

// Configuration
$ALLOWED_ORIGINS = [
    'https://signal.daedalusapps.com',
    'http://localhost:3000',  // For local development
];

// Get origin and validate
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $ALLOWED_ORIGINS)) {
    header("Access-Control-Allow-Origin: $origin");
} else {
    header('Access-Control-Allow-Origin: https://signal.daedalusapps.com');
}

header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Get JSON payload
$input = file_get_contents('php://input');
$data = json_decode($input, true);

if (!$data || !isset($data['payload']) || !isset($data['signature'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid request: missing payload or signature']);
    exit;
}

$payload = $data['payload'];
$signature = $data['signature'];
$payload_json_from_python = $data['payload_json'] ?? null;  // Exact JSON string from Python

// Get SECRET_KEY from environment
$secret = getenv('SECRET_KEY');
if (!$secret) {
    http_response_code(500);
    echo json_encode(['error' => 'Server configuration error: SECRET_KEY not set']);
    exit;
}

// Verify timestamp (10 minute window)
$timestamp = $payload['timestamp'] ?? 0;
if (abs(time() - $timestamp) > 600) {
    http_response_code(403);
    echo json_encode(['error' => 'Expired payload']);
    exit;
}

// Verify signature
// The signature is HMAC-SHA256 of "timestamp:payload_json" using SECRET_KEY
// Use the exact JSON string from Python if provided, otherwise fall back to PHP encoding

function sort_array_keys_recursive(&$array) {
    if (!is_array($array)) return;
    ksort($array);
    foreach ($array as &$value) {
        if (is_array($value)) {
            sort_array_keys_recursive($value);
        }
    }
}

// Prefer exact JSON string from Python to avoid encoding differences
if ($payload_json_from_python) {
    $payload_json = $payload_json_from_python;
} else {
    // Fallback: re-encode with sorted keys (may not match Python exactly)
    $sorted_payload = $payload;
    sort_array_keys_recursive($sorted_payload);
    $payload_json = json_encode($sorted_payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
}

$message = $timestamp . ':' . $payload_json;
$expected_signature = hash_hmac('sha256', $message, $secret);

if (!hash_equals($expected_signature, $signature)) {
    http_response_code(403);
    echo json_encode(['error' => 'Invalid signature']);
    exit;
}

// Extract email details
$to = $payload['email'] ?? '';
$is_test = $payload['is_test'] ?? false;
$digest_html = $payload['digest_html'] ?? '';

if (!$to || !filter_var($to, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid email address']);
    exit;
}

if (!$digest_html) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing digest content']);
    exit;
}

// Build email
$subject = $is_test ? 'Test Email - DaedalusSignal Digest' : 'DaedalusSignal Daily Digest';

// Get from address from environment or use default
$smtp_from = getenv('SMTP_FROM') ?: 'noreply@signal.daedalusapps.com';

$headers = [
    'MIME-Version: 1.0',
    'Content-type: text/html; charset=utf-8',
    "From: DaedalusSignal <$smtp_from>",
    "Reply-To: $smtp_from",
    'X-Mailer: DaedalusSignal-Worker'
];

// Send email using PHP mail()
$success = mail($to, $subject, $digest_html, implode("\r\n", $headers));

if ($success) {
    echo json_encode([
        'message' => "Email sent successfully to $to",
        'email' => $to,
        'is_test' => $is_test
    ]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to send email. Check server mail configuration.']);
}
