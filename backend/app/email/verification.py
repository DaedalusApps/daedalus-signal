"""
Email verification and password reset utilities
"""
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from app.config import (
    EMAIL_MODE, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM,
    VERIFICATION_CODE_EXPIRY_MINUTES, PA_API_URL
)


def generate_verification_code() -> str:
    """Generate a 6-digit numeric verification code."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))


def get_code_expiry() -> datetime:
    """Get the expiry datetime for a verification code."""
    return datetime.utcnow() + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)


def _generate_verification_html(code: str, code_type: str) -> str:
    """Generate HTML email content for verification codes."""
    if code_type == 'email_verify':
        title = "Verify Your Email"
        message = "Welcome to DaedalusSignal! Please use the code below to verify your email address."
        action = "verify your email"
    else:
        title = "Reset Your Password"
        message = "You requested a password reset for your DaedalusSignal account. Use the code below to reset your password."
        action = "reset your password"

    base_url = PA_API_URL if PA_API_URL else 'https://signal.daedalusapps.com'

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
             max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
    <div style="background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <h1 style="color: #6366f1; margin: 0 0 10px 0;">
            {title}
        </h1>
        <p style="color: #666; margin: 0 0 30px 0;">
            {message}
        </p>

        <div style="background: #f8f9fa; border-radius: 8px; padding: 30px; text-align: center; margin: 20px 0;">
            <p style="color: #666; margin: 0 0 10px 0; font-size: 14px;">
                Your verification code is:
            </p>
            <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #6366f1; font-family: monospace;">
                {code}
            </div>
            <p style="color: #999; margin: 10px 0 0 0; font-size: 12px;">
                This code expires in {VERIFICATION_CODE_EXPIRY_MINUTES} minutes.
            </p>
        </div>

        <p style="color: #666; font-size: 14px;">
            If you didn't request this code to {action}, you can safely ignore this email.
        </p>

        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            <a href="{base_url}" style="color: #6366f1;">DaedalusSignal</a> - Your AI Content Curator
        </p>
    </div>
</body>
</html>
"""
    return html


def send_verification_email(email: str, code: str, code_type: str) -> bool:
    """
    Send a verification code email.

    Args:
        email: Recipient email address
        code: 6-digit verification code
        code_type: 'email_verify' or 'password_reset'

    Returns:
        True if sent successfully, False otherwise
    """
    if code_type == 'email_verify':
        subject = "Verify your email - DaedalusSignal"
    else:
        subject = "Reset your password - DaedalusSignal"

    html_content = _generate_verification_html(code, code_type)

    if EMAIL_MODE == 'console':
        print("\n" + "=" * 60)
        print(f"VERIFICATION EMAIL to {email}")
        print(f"Subject: {subject}")
        print(f"Code: {code}")
        print(f"Type: {code_type}")
        print(f"Expires in: {VERIFICATION_CODE_EXPIRY_MINUTES} minutes")
        print("=" * 60 + "\n")
        return True

    elif EMAIL_MODE == 'smtp':
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SMTP_FROM
            msg['To'] = email

            # Plain text fallback
            plain_text = f"Your DaedalusSignal verification code is: {code}\n\nThis code expires in {VERIFICATION_CODE_EXPIRY_MINUTES} minutes."
            msg.attach(MIMEText(plain_text, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, email, msg.as_string())

            print(f"Verification email sent to {email}")
            return True

        except Exception as e:
            print(f"Failed to send verification email: {e}")
            return False

    return False
