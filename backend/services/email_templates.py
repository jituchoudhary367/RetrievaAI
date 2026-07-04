"""
services/email_templates.py

Renders email templates for verification and password reset.
"""

def render_verification_email(link: str) -> tuple[str, str]:
    subject = "Verify your email address for RAG System"
    html_body = f"""
    <html>
      <body>
        <h2>Welcome to RAG System!</h2>
        <p>Please click the link below to verify your email address and activate your account:</p>
        <p><a href="{link}" style="display:inline-block;padding:10px 20px;background-color:#10b981;color:white;text-decoration:none;border-radius:5px;">Verify Email</a></p>
        <p>Or paste this link into your browser: <br>{link}</p>
        <p>If you did not request this, you can safely ignore this email.</p>
      </body>
    </html>
    """
    return subject, html_body

def render_password_reset_email(link: str) -> tuple[str, str]:
    subject = "Reset your RAG System password"
    html_body = f"""
    <html>
      <body>
        <h2>Password Reset Request</h2>
        <p>We received a request to reset your password. Click the link below to set a new one:</p>
        <p><a href="{link}" style="display:inline-block;padding:10px 20px;background-color:#3b82f6;color:white;text-decoration:none;border-radius:5px;">Reset Password</a></p>
        <p>Or paste this link into your browser: <br>{link}</p>
        <p>If you did not request a password reset, please ignore this email.</p>
      </body>
    </html>
    """
    return subject, html_body
