"""
Email template rendering utilities.

Provides functions to load and render HTML email templates with variable substitution.
"""

import os
from pathlib import Path
from typing import Dict
from datetime import datetime

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def render_template(template_name: str, context: Dict[str, str]) -> str:
    """
    Render an HTML email template with context variables.
    
    Args:
        template_name: Name of the template file (e.g., "email_verification.html")
        context: Dictionary of variables to substitute in template
        
    Returns:
        Rendered HTML string
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    template_path = TEMPLATE_DIR / template_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"Email template not found: {template_path}")
    
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Simple variable substitution (Jinja2-style syntax)
    rendered = template_content
    for key, value in context.items():
        placeholder = f"{{{{ {key} }}}}"
        rendered = rendered.replace(placeholder, str(value))
    
    return rendered


def get_verification_email_html(
    app_name: str,
    username: str,
    verification_url: str,
    expiry_hours: int
) -> str:
    """
    Get rendered HTML for verification email.
    
    Args:
        app_name: Application name
        username: User's username
        verification_url: Full verification URL
        expiry_hours: Hours until token expires
        
    Returns:
        Rendered HTML string
    """
    context = {
        "app_name": app_name,
        "username": username,
        "verification_url": verification_url,
        "expiry_hours": expiry_hours,
        "current_year": datetime.now().year,
    }
    
    return render_template("email_verification.html", context)


def get_verification_email_text(
    app_name: str,
    username: str,
    verification_url: str,
    expiry_hours: int
) -> str:
    """
    Get plain text version of verification email.
    
    Args:
        app_name: Application name
        username: User's username
        verification_url: Full verification URL
        expiry_hours: Hours until token expires
        
    Returns:
        Plain text email content
    """
    return f"""
Welcome to {app_name}!

Hi {username},

Thank you for registering! Please verify your email address to activate your account.

Verification link:
{verification_url}

This link will expire in {expiry_hours} hour(s).

If you didn't create an account, you can safely ignore this email.

---
{app_name}
© {datetime.now().year}
    """.strip()
