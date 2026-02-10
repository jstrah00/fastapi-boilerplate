"""
Email service for sending templated emails via SMTP.

Uses Jinja2 templates from templates/email/ and sends via SSL SMTP (port 465).
Sending is done in a background thread to avoid blocking the event loop.
"""
import smtplib
import ssl
from datetime import datetime, UTC
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from jinja2 import Environment, FileSystemLoader

from app.config import settings
from app.common.logging import get_logger

logger = get_logger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "email"
_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
_executor = ThreadPoolExecutor(max_workers=2)


def _send_smtp(to_email: str, subject: str, html_body: str) -> None:
    """Send an email via SMTP SSL (runs in thread pool)."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to_email, msg.as_string())


def _render_template(template_name: str, **kwargs: object) -> str:
    """Render a Jinja2 email template."""
    template = _jinja_env.get_template(template_name)
    return template.render(year=datetime.now(UTC).year, **kwargs)


async def send_email(to_email: str, subject: str, template_name: str, **kwargs: object) -> None:
    """
    Send a templated email. Non-blocking (runs SMTP in thread pool).

    Silently logs errors without raising — email failures should not break flows.
    """
    if not settings.SMTP_ENABLED:
        logger.debug("email_skipped", to=to_email, template=template_name, reason="SMTP disabled")
        return

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("email_skipped", to=to_email, reason="SMTP credentials not configured")
        return

    try:
        html_body = _render_template(template_name, subject=subject, **kwargs)

        import asyncio
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(_executor, _send_smtp, to_email, subject, html_body)

        logger.info("email_sent", to=to_email, subject=subject, template=template_name)
    except Exception:
        logger.exception("email_send_failed", to=to_email, template=template_name)


# ---- Convenience functions for each email type ----

async def send_welcome_aretan(to_email: str, first_name: str) -> None:
    """Send welcome email to a newly registered aretan."""
    await send_email(
        to_email,
        "Bienvenido/a a Athlete2Work",
        "welcome_aretan.html",
        first_name=first_name,
    )


async def send_welcome_contractor(to_email: str, first_name: str) -> None:
    """Send welcome email to a newly registered contractor."""
    await send_email(
        to_email,
        "Bienvenido/a a Athlete2Work",
        "welcome_contractor.html",
        first_name=first_name,
        platform_url=settings.FRONTEND_URL,
    )


async def send_approval_approved(to_email: str, first_name: str) -> None:
    """Send approval notification to an aretan."""
    await send_email(
        to_email,
        "Tu perfil ha sido aprobado - Athlete2Work",
        "approval_approved.html",
        first_name=first_name,
        platform_url=settings.FRONTEND_URL,
    )


async def send_approval_rejected(to_email: str, first_name: str) -> None:
    """Send rejection notification to an aretan."""
    await send_email(
        to_email,
        "Actualización sobre tu perfil - Athlete2Work",
        "approval_rejected.html",
        first_name=first_name,
    )


async def send_password_reset(to_email: str, first_name: str, reset_url: str) -> None:
    """Send password reset email."""
    await send_email(
        to_email,
        "Restablecer contraseña - Athlete2Work",
        "password_reset.html",
        first_name=first_name,
        reset_url=reset_url,
    )


async def send_contact_request(to_email: str, first_name: str, requester_name: str, message: str | None = None) -> None:
    """Send email to aretan when they receive a contact request."""
    await send_email(
        to_email,
        "Nueva solicitud de contacto - Athlete2Work",
        "contact_request.html",
        first_name=first_name,
        requester_name=requester_name,
        message=message,
        platform_url=f"{settings.FRONTEND_URL}/contact-requests",
    )


async def send_contact_accepted(to_email: str, first_name: str, aretan_name: str, contact_email: str | None = None, phone: str | None = None) -> None:
    """Send email to contractor when their contact request is accepted."""
    await send_email(
        to_email,
        "Solicitud de contacto aceptada - Athlete2Work",
        "contact_accepted.html",
        first_name=first_name,
        aretan_name=aretan_name,
        contact_email=contact_email,
        phone=phone,
        platform_url=f"{settings.FRONTEND_URL}/contact-requests",
    )
