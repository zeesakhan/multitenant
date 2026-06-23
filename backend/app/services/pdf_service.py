"""PDF generation service using WeasyPrint + Jinja2.

All templates live in app/templates/documents/.
render_pdf() accepts a template name + context dict and returns PDF bytes.

macOS note: requires DYLD_LIBRARY_PATH=/opt/homebrew/lib at process startup.
"""

import os
import logging
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Optional
from decimal import Decimal

from jinja2 import Environment, FileSystemLoader, select_autoescape

log = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "documents"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)
_jinja_env.globals["now"] = datetime.now


def _preload_macos_libs() -> None:
    """Pre-load gobject/pango via ctypes so WeasyPrint finds them on macOS Apple Silicon."""
    import ctypes, platform
    if platform.system() != "Darwin":
        return
    homebrew = "/opt/homebrew/lib"
    for lib in [
        "libgobject-2.0.0.dylib", "libglib-2.0.0.dylib",
        "libpango-1.0.0.dylib", "libpangoft2-1.0.0.dylib",
        "libharfbuzz.0.dylib", "libfontconfig.1.dylib",
        "libcairo.2.dylib", "libcairo-gobject.2.dylib",
    ]:
        path = f"{homebrew}/{lib}"
        if os.path.exists(path):
            try:
                ctypes.CDLL(path)
            except OSError:
                pass


_preload_macos_libs()


def render_pdf(template_name: str, context: dict) -> bytes:
    """Render a Jinja2 HTML template to PDF bytes via WeasyPrint."""
    context.setdefault("generation_date", date.today().strftime("%d %b %Y"))

    try:
        from weasyprint import HTML, CSS
    except Exception as exc:
        raise RuntimeError(
            "WeasyPrint not available. Run: brew install pango cairo"
        ) from exc

    template = _jinja_env.get_template(template_name)
    html_str = template.render(**context)

    css_str = CSS(string="@page { size: A4; }")
    pdf_bytes = HTML(string=html_str, base_url=str(_TEMPLATES_DIR)).write_pdf(stylesheets=[css_str])
    log.info("PDF generated template=%s size=%d bytes", template_name, len(pdf_bytes))
    return pdf_bytes


def render_html(template_name: str, context: dict) -> str:
    """Render Jinja2 template to HTML string (useful for preview/testing)."""
    context.setdefault("generation_date", date.today().strftime("%d %b %Y"))
    template = _jinja_env.get_template(template_name)
    return template.render(**context)


# ── Context builders ──────────────────────────────────────────────────────────

class PdfContextBuilder:
    """Builds the template context dict for each document type."""

    @staticmethod
    def maf_context(application, members, plan, tenant_config: dict) -> dict:
        return {
            "application": application,
            "members": members,
            "plan": plan,
            "tenant": tenant_config,
            "doc_reference": f"MAF-{application.application_number}",
        }

    @staticmethod
    def kyc_context(application, principal, tenant_config: dict) -> dict:
        return {
            "application": application,
            "principal": principal,
            "tenant": tenant_config,
            "doc_reference": f"KYC-{application.application_number}",
        }

    @staticmethod
    def tob_context(application, plan, coverages, breakdown: Optional[dict], tenant_config: dict) -> dict:
        return {
            "application": application,
            "plan": plan,
            "coverages": coverages,
            "breakdown": breakdown,
            "tenant": tenant_config,
            "doc_reference": f"TOB-{application.application_number}",
        }

    @staticmethod
    def policy_schedule_context(policy, application, members, plan, breakdown: Optional[dict], payment, tenant_config: dict) -> dict:
        return {
            "policy": policy,
            "application": application,
            "members": members,
            "plan": plan,
            "breakdown": breakdown,
            "payment": payment,
            "tenant": tenant_config,
            "doc_reference": f"SCH-{policy.policy_number}",
        }

    @staticmethod
    def credit_note_context(policy, application, plan, breakdown: Optional[dict], seq: int, tenant_config: dict) -> dict:
        return {
            "policy": policy,
            "application": application,
            "plan": plan,
            "breakdown": breakdown,
            "tenant": tenant_config,
            "doc_reference": f"CN-{policy.policy_number}-{seq:04d}",
        }

    @staticmethod
    def tax_invoice_context(policy, application, plan, breakdown: Optional[dict], seq: int, tenant_config: dict) -> dict:
        return {
            "policy": policy,
            "application": application,
            "plan": plan,
            "breakdown": breakdown,
            "tenant": tenant_config,
            "doc_reference": f"INV-{policy.policy_number}-{seq:04d}",
        }

    @staticmethod
    def receipt_context(policy, application, plan, breakdown: Optional[dict], payment, seq: int, tenant_config: dict) -> dict:
        return {
            "policy": policy,
            "application": application,
            "plan": plan,
            "breakdown": breakdown,
            "payment": payment,
            "tenant": tenant_config,
            "doc_reference": f"RV-{policy.policy_number}-{seq:04d}",
        }
