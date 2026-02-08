import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import get_settings
from app.shared.utils import setup_logger
from app.modules.users.models import User

settings = get_settings()
logger = setup_logger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """
    Send email using SMTP Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (HTML supported)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        logger.error("SMTP credentials not configured")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_EMAIL}>"
        msg["To"] = to
        msg["Subject"] = subject

        html_part = MIMEText(body, "html")
        msg.attach(html_part)

        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {str(e)}")
        return False


def send_verification_email(user: User, token: str, base_url: str = "http://localhost:3000") -> bool:
    """
    Send email verification link to user.
    
    Args:
        user: User object
        token: Verification token
        base_url: Frontend base URL
    
    Returns:
        bool: True if sent successfully
    """
    verification_link = f"{base_url}/verify-email?token={token}"
    
    subject = "Verify Your Email Address"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #4CAF50;">Welcome to {settings.SMTP_FROM_NAME}!</h2>
                <p>Hello <strong>{user.username}</strong>,</p>
                <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_link}" 
                       style="background-color: #4CAF50; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{verification_link}</p>
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    If you didn't create an account, please ignore this email.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(user.email, subject, body)


def send_update_notification(user: User, changes: dict) -> bool:
    """
    Send notification email when user profile is updated.
    
    Args:
        user: User object
        changes: Dictionary of changed fields
    
    Returns:
        bool: True if sent successfully
    """
    changes_list = "<ul>"
    for field, value in changes.items():
        changes_list += f"<li><strong>{field.replace('_', ' ').title()}:</strong> {value}</li>"
    changes_list += "</ul>"
    
    subject = "Your Account Information Has Been Updated"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2196F3;">Account Update Notification</h2>
                <p>Hello <strong>{user.username}</strong>,</p>
                <p>Your account information has been updated by an administrator:</p>
                {changes_list}
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    If you didn't request these changes, please contact support immediately.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(user.email, subject, body)


def send_password_reset_by_admin(user: User, temp_password: str) -> bool:
    """
    Send temporary password email when admin resets user password.
    
    Args:
        user: User object
        temp_password: Temporary password
    
    Returns:
        bool: True if sent successfully
    """
    subject = "Your Password Has Been Reset"
    body = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF9800;">Password Reset Notification</h2>
                <p>Hello <strong>{user.username}</strong>,</p>
                <p>Your password has been reset by an administrator.</p>
                <p>Your temporary password is:</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; 
                            font-family: monospace; font-size: 18px; text-align: center; margin: 20px 0;">
                    <strong>{temp_password}</strong>
                </div>
                <p style="color: #d32f2f;">
                    <strong>Important:</strong> Please change this password immediately after logging in.
                </p>
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    If you didn't request a password reset, please contact support immediately.
                </p>
            </div>
        </body>
    </html>
    """
    
    return send_email(user.email, subject, body)
