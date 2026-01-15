<?php
/**
 * Email sending functions for DaedalusSignal
 */

/**
 * Send an email via SMTP
 *
 * Uses environment variables for configuration:
 *   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
 */
function send_email(string $to, string $subject, string $html_body, string $plain_body = ''): bool
{
    $smtp_host = getenv('SMTP_HOST') ?: 'mail.signal.daedalusapps.com';
    $smtp_port = (int)(getenv('SMTP_PORT') ?: 587);
    $smtp_user = getenv('SMTP_USER') ?: '';
    $smtp_pass = getenv('SMTP_PASSWORD') ?: '';
    $from = getenv('SMTP_FROM') ?: 'noreply@signal.daedalusapps.com';

    // Generate boundary for multipart email
    $boundary = md5(uniqid(time()));

    // Build headers
    $headers = [
        "From: DaedalusSignal <{$from}>",
        "Reply-To: {$from}",
        "MIME-Version: 1.0",
        "Content-Type: multipart/alternative; boundary=\"{$boundary}\"",
        "X-Mailer: DaedalusSignal-PHP"
    ];

    // Build body with plain text fallback
    if (empty($plain_body)) {
        $plain_body = strip_tags($html_body);
    }

    $body = "--{$boundary}\r\n";
    $body .= "Content-Type: text/plain; charset=UTF-8\r\n\r\n";
    $body .= $plain_body . "\r\n\r\n";
    $body .= "--{$boundary}\r\n";
    $body .= "Content-Type: text/html; charset=UTF-8\r\n\r\n";
    $body .= $html_body . "\r\n\r\n";
    $body .= "--{$boundary}--";

    // If no SMTP credentials, use PHP's mail() function
    if (empty($smtp_user) || empty($smtp_pass)) {
        error_log("Email: Using PHP mail() - no SMTP credentials configured");
        return mail($to, $subject, $body, implode("\r\n", $headers));
    }

    // Use SMTP
    try {
        $socket = @fsockopen($smtp_host, $smtp_port, $errno, $errstr, 30);
        if (!$socket) {
            error_log("SMTP connection failed: {$errno} - {$errstr}");
            return false;
        }

        // Read greeting
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '220') {
            error_log("SMTP greeting error: {$response}");
            fclose($socket);
            return false;
        }

        // EHLO
        fputs($socket, "EHLO " . gethostname() . "\r\n");
        $response = '';
        while ($line = fgets($socket, 512)) {
            $response .= $line;
            if (substr($line, 3, 1) === ' ') break;
        }

        // STARTTLS
        fputs($socket, "STARTTLS\r\n");
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '220') {
            error_log("STARTTLS error: {$response}");
            fclose($socket);
            return false;
        }

        // Enable TLS
        if (!stream_socket_enable_crypto($socket, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
            error_log("Failed to enable TLS");
            fclose($socket);
            return false;
        }

        // EHLO again after TLS
        fputs($socket, "EHLO " . gethostname() . "\r\n");
        $response = '';
        while ($line = fgets($socket, 512)) {
            $response .= $line;
            if (substr($line, 3, 1) === ' ') break;
        }

        // AUTH LOGIN
        fputs($socket, "AUTH LOGIN\r\n");
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '334') {
            error_log("AUTH LOGIN error: {$response}");
            fclose($socket);
            return false;
        }

        // Username
        fputs($socket, base64_encode($smtp_user) . "\r\n");
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '334') {
            error_log("SMTP username error: {$response}");
            fclose($socket);
            return false;
        }

        // Password
        fputs($socket, base64_encode($smtp_pass) . "\r\n");
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '235') {
            error_log("SMTP auth error: {$response}");
            fclose($socket);
            return false;
        }

        // MAIL FROM
        fputs($socket, "MAIL FROM:<{$from}>\r\n");
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '250') {
            error_log("MAIL FROM error: {$response}");
            fclose($socket);
            return false;
        }

        // RCPT TO
        fputs($socket, "RCPT TO:<{$to}>\r\n");
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '250') {
            error_log("RCPT TO error: {$response}");
            fclose($socket);
            return false;
        }

        // DATA
        fputs($socket, "DATA\r\n");
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '354') {
            error_log("DATA error: {$response}");
            fclose($socket);
            return false;
        }

        // Send message
        $message = "Subject: {$subject}\r\n";
        $message .= "To: {$to}\r\n";
        $message .= implode("\r\n", $headers) . "\r\n\r\n";
        $message .= $body . "\r\n.\r\n";

        fputs($socket, $message);
        $response = fgets($socket, 512);
        if (substr($response, 0, 3) !== '250') {
            error_log("Message send error: {$response}");
            fclose($socket);
            return false;
        }

        // QUIT
        fputs($socket, "QUIT\r\n");
        fclose($socket);

        error_log("Email sent successfully to: {$to}");
        return true;

    } catch (Exception $e) {
        error_log("SMTP exception: " . $e->getMessage());
        return false;
    }
}

/**
 * Send password reset email with magic link
 */
function send_password_reset_email(string $email, string $name, string $reset_link): bool
{
    $subject = "Reset Your DaedalusSignal Password";

    // Escape name for HTML output
    $name = htmlspecialchars($name, ENT_QUOTES, 'UTF-8');

    $html = <<<HTML
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); padding: 30px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 28px;">DaedalusSignal</h1>
        </div>
        <div style="padding: 40px 30px;">
            <h2 style="color: #1f2937; margin-top: 0;">Hi {$name},</h2>
            <p style="color: #4b5563; line-height: 1.6;">
                We received a request to reset your password. Click the button below to create a new password:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{$reset_link}" style="display: inline-block; background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Reset Password
                </a>
            </div>
            <p style="color: #6b7280; font-size: 14px; line-height: 1.6;">
                This link will expire in <strong>15 minutes</strong> for security reasons.
            </p>
            <p style="color: #6b7280; font-size: 14px; line-height: 1.6;">
                If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
            </p>
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            <p style="color: #9ca3af; font-size: 12px; text-align: center; margin: 0;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{$reset_link}" style="color: #6366f1; word-break: break-all;">{$reset_link}</a>
            </p>
        </div>
    </div>
</body>
</html>
HTML;

    $plain = <<<PLAIN
Hi {$name},

We received a request to reset your DaedalusSignal password.

Click this link to reset your password:
{$reset_link}

This link will expire in 15 minutes.

If you didn't request a password reset, you can safely ignore this email.

- DaedalusSignal Team
PLAIN;

    return send_email($email, $subject, $html, $plain);
}
