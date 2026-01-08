#!/usr/bin/env python3
"""
DreamHost Mailer Worker
Fetches digest payloads from PythonAnywhere and sends via local SMTP
"""
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
from api_client import PAClient


def send_email(to_email: str, html_content: str, subject: str = "DaedalusSignal Daily Digest") -> bool:
    """Send an email via local SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        msg.attach(MIMEText(html_content, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        return True
    except Exception as e:
        print(f"    SMTP error for {to_email}: {e}")
        return False


def run_mailer():
    """Main entry point - fetch digests and send emails."""
    print(f"\n[{datetime.now()}] Starting DreamHost mailer worker...")

    client = PAClient()

    try:
        digests = client.get_digests()
        print(f"  Fetched {len(digests)} digest payloads from PythonAnywhere")
    except Exception as e:
        print(f"  ERROR fetching digests: {e}")
        sys.exit(1)

    sent = 0
    failed = 0

    for digest in digests:
        email = digest['email']
        html = digest['digest_html']
        content_ids = digest.get('content_ids', [])

        print(f"  Sending to: {email}")

        if send_email(email, html):
            sent += 1
            try:
                # Notify PA that email was sent
                client.mark_digest_sent(email, content_ids)
            except Exception as e:
                print(f"    Warning: failed to notify PA: {e}")
        else:
            failed += 1

    print(f"[{datetime.now()}] Mailer complete: {sent} sent, {failed} failed\n")


if __name__ == '__main__':
    run_mailer()
