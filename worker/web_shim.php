<?php
/**
 * DreamHost PHP Shim for browser-triggered test emails
 * Receives signed payload from frontend, sends email via SMTP
 *
 * Deployment:
 * 1. Upload this file to your DreamHost web directory
 * 2. Set environment variables in .htaccess (SECRET_KEY, SMTP_*)
 * 3. Configure allowed origins below
 */

// Configuration
$default_origins = 'https://signal.daedalusapps.com,http://localhost:3000';
$env = getenv('CORS_ALLOWED_ORIGINS');
$origins_list = $env === false ? $default_origins : $env;
$ALLOWED_ORIGINS = array_filter(array_map('trim', explode(',', $origins_list)));

// Get origin and validate
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origin, $ALLOWED_ORIGINS)) {
    header("Access-Control-Allow-Origin: $origin");
} elseif (!empty($ALLOWED_ORIGINS)) {
    header('Access-Control-Allow-Origin: ' . reset($ALLOWED_ORIGINS));
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

function sort_array_keys_recursive(&$array)
{
    if (!is_array($array))
        return;
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

// Check for action type and route accordingly
$action = $payload['action'] ?? 'send_email';

// =========================================
// ACTION: Test Email (simple test with hardcoded content)
// =========================================
if ($action === 'test_email') {
    $admin_email = $payload['email'] ?? '';

    if (!$admin_email || !filter_var($admin_email, FILTER_VALIDATE_EMAIL)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid email address']);
        exit;
    }

    // Simple test email HTML
    $test_html = '
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #8b5cf6;">DaedalusSignal Test Email</h1>
        <p>This is a test email from DaedalusSignal.</p>
        <p>If you received this, the email system is working correctly!</p>
        <p style="color: #666; font-size: 12px;">Sent at: ' . date('Y-m-d H:i:s T') . '</p>
    </body>
    </html>';

    // Get SMTP settings from environment
    $smtp_host = getenv('SMTP_HOST') ?: 'mail.signal.daedalusapps.com';
    $smtp_port = getenv('SMTP_PORT') ?: 587;
    $smtp_user = getenv('SMTP_USER') ?: '';
    $smtp_pass = getenv('SMTP_PASSWORD') ?: '';
    $smtp_from = getenv('SMTP_FROM') ?: 'noreply@signal.daedalusapps.com';

    if ($smtp_user && $smtp_pass) {
        $result = send_smtp_email($admin_email, 'Test Email - DaedalusSignal', $test_html, $smtp_from, $smtp_host, $smtp_port, $smtp_user, $smtp_pass);
        if ($result['success']) {
            echo json_encode(['message' => "Test email sent to $admin_email"]);
        } else {
            http_response_code(500);
            echo json_encode(['error' => 'SMTP error: ' . $result['error']]);
        }
    } else {
        // Fallback to mail()
        $headers = "MIME-Version: 1.0\r\nContent-type: text/html; charset=utf-8\r\nFrom: DaedalusSignal <$smtp_from>";
        if (mail($admin_email, 'Test Email - DaedalusSignal', $test_html, $headers)) {
            echo json_encode(['message' => "Test email sent to $admin_email"]);
        } else {
            http_response_code(500);
            echo json_encode(['error' => 'Failed to send test email']);
        }
    }
    exit;
}

// =========================================
// ACTION: Get Logs
// =========================================
if ($action === 'get_logs') {
    $script_dir = dirname(__FILE__);
    $log_type = $payload['log_type'] ?? 'scraper';

    // Validate log type to prevent path traversal
    $allowed_logs = ['scraper', 'mailer'];
    if (!in_array($log_type, $allowed_logs)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid log type']);
        exit;
    }

    $log_file = $script_dir . '/' . $log_type . '.log';

    if (!file_exists($log_file)) {
        echo json_encode([
            'log_type' => $log_type,
            'content' => '(No log file yet - run the ' . $log_type . ' first)',
            'lines' => 0
        ]);
        exit;
    }

    // Read last 100 lines of the log file
    $lines = file($log_file, FILE_IGNORE_NEW_LINES);
    $total_lines = count($lines);
    $last_lines = array_slice($lines, -100);
    $content = implode("\n", $last_lines);

    echo json_encode([
        'log_type' => $log_type,
        'content' => $content,
        'lines' => count($last_lines),
        'total_lines' => $total_lines
    ]);
    exit;
}

// =========================================
// ACTION: Run Scrapers
// =========================================
if ($action === 'run_scrapers') {
    // Get the directory where this script lives
    $script_dir = dirname(__FILE__);
    $python_script = $script_dir . '/run_scrapers.py';

    if (!file_exists($python_script)) {
        http_response_code(500);
        echo json_encode(['error' => 'Scraper script not found']);
        exit;
    }

    // Run the scraper in background (& at end) so we return immediately
    $log_file = $script_dir . '/scraper.log';
    $command = "cd " . escapeshellarg($script_dir) . " && python3 run_scrapers.py >> " . escapeshellarg($log_file) . " 2>&1 &";
    exec($command, $output, $return_code);

    echo json_encode([
        'message' => 'Scraper started in background',
        'status' => 'running'
    ]);
    exit;
}

// =========================================
// ACTION: Run Mailer
// =========================================
if ($action === 'run_mailer') {
    // Get the directory where this script lives
    $script_dir = dirname(__FILE__);
    $python_script = $script_dir . '/run_mailer.py';

    if (!file_exists($python_script)) {
        http_response_code(500);
        echo json_encode(['error' => 'Mailer script not found']);
        exit;
    }

    // Run the mailer in background (& at end) so we return immediately
    $log_file = $script_dir . '/mailer.log';
    $command = "cd " . escapeshellarg($script_dir) . " && python3 run_mailer.py >> " . escapeshellarg($log_file) . " 2>&1 &";
    exec($command, $output, $return_code);

    echo json_encode([
        'message' => 'Mailer started in background',
        'status' => 'running'
    ]);
    exit;
}

// =========================================
// ACTION: Send Email (default)
// =========================================

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

// Get SMTP settings from environment
$smtp_host = getenv('SMTP_HOST') ?: 'mail.signal.daedalusapps.com';
$smtp_port = getenv('SMTP_PORT') ?: 587;
$smtp_user = getenv('SMTP_USER') ?: '';
$smtp_pass = getenv('SMTP_PASSWORD') ?: '';
$smtp_from = getenv('SMTP_FROM') ?: 'noreply@signal.daedalusapps.com';

/**
 * Send email via SMTP with authentication
 */
function send_smtp_email($to, $subject, $html_body, $from, $host, $port, $user, $pass)
{
    $errors = [];

    // Connect to SMTP server
    $socket = @fsockopen($host, $port, $errno, $errstr, 30);
    if (!$socket) {
        return ['success' => false, 'error' => "Connection failed: $errstr ($errno)"];
    }

    // Helper to send command and get response
    $send_cmd = function ($cmd = null) use ($socket, &$errors) {
        if ($cmd !== null) {
            fwrite($socket, $cmd . "\r\n");
        }
        $response = '';
        while ($line = fgets($socket, 515)) {
            $response .= $line;
            if (substr($line, 3, 1) == ' ')
                break;
        }
        return $response;
    };

    // SMTP conversation
    $send_cmd();  // Read greeting
    $send_cmd("EHLO " . gethostname());

    // Start TLS
    $send_cmd("STARTTLS");
    stream_socket_enable_crypto($socket, true, STREAM_CRYPTO_METHOD_TLS_CLIENT);
    $send_cmd("EHLO " . gethostname());

    // Authenticate
    if ($user && $pass) {
        $send_cmd("AUTH LOGIN");
        $send_cmd(base64_encode($user));
        $response = $send_cmd(base64_encode($pass));
        if (strpos($response, '235') === false) {
            fclose($socket);
            return ['success' => false, 'error' => 'SMTP authentication failed'];
        }
    }

    // Send email
    $send_cmd("MAIL FROM:<$from>");
    $send_cmd("RCPT TO:<$to>");
    $send_cmd("DATA");

    // Email headers and body
    $headers = "From: DaedalusSignal <$from>\r\n";
    $headers .= "To: $to\r\n";
    $headers .= "Subject: $subject\r\n";
    $headers .= "MIME-Version: 1.0\r\n";
    $headers .= "Content-Type: text/html; charset=utf-8\r\n";
    $headers .= "\r\n";

    fwrite($socket, $headers . $html_body . "\r\n.\r\n");
    $response = $send_cmd();

    $send_cmd("QUIT");
    fclose($socket);

    if (strpos($response, '250') !== false) {
        return ['success' => true];
    } else {
        return ['success' => false, 'error' => "Send failed: $response"];
    }
}

// Try SMTP first if credentials are set, fall back to mail()
if ($smtp_user && $smtp_pass) {
    $result = send_smtp_email($to, $subject, $digest_html, $smtp_from, $smtp_host, $smtp_port, $smtp_user, $smtp_pass);
    if ($result['success']) {
        echo json_encode([
            'message' => "Email sent successfully to $to",
            'email' => $to,
            'is_test' => $is_test,
            'method' => 'smtp'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'SMTP error: ' . $result['error']]);
    }
} else {
    // Fallback to PHP mail()
    $headers = [
        'MIME-Version: 1.0',
        'Content-type: text/html; charset=utf-8',
        "From: DaedalusSignal <$smtp_from>",
        "Reply-To: $smtp_from",
        'X-Mailer: DaedalusSignal-Worker'
    ];

    $success = mail($to, $subject, $digest_html, implode("\r\n", $headers));

    if ($success) {
        echo json_encode([
            'message' => "Email sent successfully to $to",
            'email' => $to,
            'is_test' => $is_test,
            'method' => 'mail'
        ]);
    } else {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to send email. Check server mail configuration.']);
    }
}
