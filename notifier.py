"""
notifier.py
Handles "sending" notifications. In the web app, real email is optional
(configured via Streamlit secrets / .env). If not configured, actions
are simulated and shown in the UI as an activity log instead of crashing.
"""

import smtplib
from email.mime.text import MIMEText


def send_email(sender_email, sender_password, to_email, subject, message):
    """
    Attempts to send an email via Gmail SMTP.
    Returns a tuple: (success: bool, info: str)
    """
    if not sender_email or not sender_password or not to_email:
        return False, "Email not sent — credentials not configured (simulated)."

    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True, f"Email sent to {to_email}"
    except Exception as e:
        return False, f"Email failed ({e}) — simulated instead."


def build_family_alert(user_name, message):
    """
    Builds the subject and body for a family notification email.
    """
    subject = f"Medication check-in needed for {user_name}"
    body = (
        f"This is an automated alert from the Medication Reminder app.\n\n"
        f"{message}\n\n"
        f"Please check in with {user_name} when you can."
    )
    return subject, body
