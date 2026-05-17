"""
Email notification service.

In production set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, EMAIL_FROM
in the environment. In dev/test mode (SMTP_HOST unset) emails are logged instead
of sent so no mail server is required.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.settings = get_settings()
        self.smtp_host: str = getattr(self.settings, "smtp_host", "")
        self.smtp_port: int = int(getattr(self.settings, "smtp_port", 587))
        self.smtp_user: str = getattr(self.settings, "smtp_user", "")
        self.smtp_password: str = getattr(self.settings, "smtp_password", "")
        self.from_address: str = getattr(self.settings, "email_from", "noreply@healthinsurance.local")

    @property
    def _configured(self) -> bool:
        return bool(self.smtp_host)

    def send(self, to: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
        if not self._configured:
            logger.info("Email (dev mode — no SMTP configured): to=%s subject=%s", to, subject)
            return True

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_address
        msg["To"] = to
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                if self.smtp_user:
                    smtp.login(self.smtp_user, self.smtp_password)
                smtp.sendmail(self.from_address, [to], msg.as_string())
            logger.info("Email sent: to=%s subject=%s", to, subject)
            return True
        except Exception as exc:
            logger.error("Email failed: to=%s subject=%s error=%s", to, subject, exc)
            return False

    # ------------------------------------------------------------------ #
    # Notification helpers                                                 #
    # ------------------------------------------------------------------ #

    def notify_policy_issued(self, customer_email: str, customer_name: str, policy_number: str,
                              effective_date: str, expiry_date: str, premium: str) -> bool:
        subject = f"Your Insurance Policy {policy_number} Is Active"
        html = f"""
        <h2>Dear {customer_name},</h2>
        <p>Your health insurance policy has been issued successfully.</p>
        <table cellpadding="8" style="border-collapse:collapse;">
          <tr><td><strong>Policy Number</strong></td><td>{policy_number}</td></tr>
          <tr><td><strong>Effective Date</strong></td><td>{effective_date}</td></tr>
          <tr><td><strong>Expiry Date</strong></td><td>{expiry_date}</td></tr>
          <tr><td><strong>Monthly Premium</strong></td><td>${premium}</td></tr>
        </table>
        <p>Please keep this policy number for your records.</p>
        """
        return self.send(customer_email, subject, html)

    def notify_claim_submitted(self, customer_email: str, customer_name: str,
                                claim_number: str, claimed_amount: str) -> bool:
        subject = f"Claim {claim_number} Received"
        html = f"""
        <h2>Dear {customer_name},</h2>
        <p>We have received your claim <strong>{claim_number}</strong>
           for <strong>${claimed_amount}</strong>.</p>
        <p>Our team will review it and update you within 3–5 business days.</p>
        """
        return self.send(customer_email, subject, html)

    def notify_claim_approved(self, customer_email: str, customer_name: str,
                               claim_number: str, approved_amount: str) -> bool:
        subject = f"Claim {claim_number} Approved"
        html = f"""
        <h2>Dear {customer_name},</h2>
        <p>Your claim <strong>{claim_number}</strong> has been <strong>approved</strong>
           for <strong>${approved_amount}</strong>.</p>
        <p>Payment will be processed within 5–7 business days.</p>
        """
        return self.send(customer_email, subject, html)

    def notify_claim_rejected(self, customer_email: str, customer_name: str,
                               claim_number: str, reason: str) -> bool:
        subject = f"Claim {claim_number} Not Approved"
        html = f"""
        <h2>Dear {customer_name},</h2>
        <p>Unfortunately your claim <strong>{claim_number}</strong> could not be approved.</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p>If you believe this decision is incorrect, please contact our support team.</p>
        """
        return self.send(customer_email, subject, html)

    def notify_policy_renewal(self, customer_email: str, customer_name: str,
                               old_number: str, new_number: str, expiry_date: str) -> bool:
        subject = f"Policy Renewed — New Policy {new_number}"
        html = f"""
        <h2>Dear {customer_name},</h2>
        <p>Your policy <strong>{old_number}</strong> has been renewed.</p>
        <p>Your new policy number is <strong>{new_number}</strong>,
           valid until <strong>{expiry_date}</strong>.</p>
        """
        return self.send(customer_email, subject, html)

    def notify_application_approved(self, customer_email: str, customer_name: str,
                                     application_number: str) -> bool:
        subject = f"Application {application_number} Approved"
        html = f"""
        <h2>Dear {customer_name},</h2>
        <p>Your application <strong>{application_number}</strong> has been approved.</p>
        <p>Your policy will be issued shortly.</p>
        """
        return self.send(customer_email, subject, html)
