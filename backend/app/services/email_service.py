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

    def notify_adamjee_policy_issued(
        self,
        customer_email: str,
        customer_name: str,
        policy_number: str,
        plan_name: str,
        effective_date: str,
        expiry_date: str,
        annual_premium_aed: str,
        monthly_premium_aed: str,
        member_count: int,
        payment_reference: str,
        application_number: str,
    ) -> bool:
        subject = f"Your Adamjee Insurance Policy {policy_number} is Now Active 🎉"
        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
  body{{margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}}
  .wrapper{{max-width:600px;margin:32px auto;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.08);}}
  .header{{background:linear-gradient(135deg,#0055A5,#1565C0);padding:40px 32px;text-align:center;}}
  .header h1{{color:#fff;margin:0 0 4px;font-size:24px;}}
  .header p{{color:rgba(255,255,255,.8);margin:0;font-size:14px;}}
  .badge{{display:inline-block;background:#F59E0B;color:#1e3a5f;padding:4px 14px;border-radius:999px;font-size:12px;font-weight:700;margin-top:12px;}}
  .body{{padding:32px;}}
  .greeting{{font-size:16px;color:#374151;margin-bottom:24px;}}
  .policy-card{{background:#EFF6FF;border:2px solid #BFDBFE;border-radius:12px;padding:24px;margin-bottom:24px;text-align:center;}}
  .policy-card .label{{font-size:11px;color:#6B7280;text-transform:uppercase;letter-spacing:.08em;margin-bottom:4px;}}
  .policy-card .pnum{{font-size:28px;font-weight:800;color:#0055A5;font-family:monospace;letter-spacing:.05em;}}
  .detail-table{{width:100%;border-collapse:collapse;margin-bottom:24px;}}
  .detail-table tr{{border-bottom:1px solid #F3F4F6;}}
  .detail-table td{{padding:10px 4px;font-size:14px;}}
  .detail-table td:first-child{{color:#6B7280;width:50%;}}
  .detail-table td:last-child{{color:#111827;font-weight:600;text-align:right;}}
  .steps{{background:#F9FAFB;border-radius:12px;padding:20px;margin-bottom:24px;}}
  .steps h3{{margin:0 0 12px;font-size:14px;color:#374151;}}
  .step{{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px;font-size:13px;color:#4B5563;}}
  .step-icon{{width:20px;height:20px;border-radius:50%;background:#0055A5;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;margin-top:1px;}}
  .cta{{text-align:center;margin:24px 0;}}
  .cta a{{background:#0055A5;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-weight:700;font-size:15px;display:inline-block;}}
  .footer{{background:#F9FAFB;padding:20px 32px;text-align:center;border-top:1px solid #E5E7EB;}}
  .footer p{{color:#9CA3AF;font-size:12px;margin:4px 0;}}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Adamjee Insurance</h1>
    <p>Dubai Health Authority Compliant · TPA: MEDNET</p>
    <span class="badge">✓ POLICY ACTIVE</span>
  </div>

  <div class="body">
    <p class="greeting">Dear <strong>{customer_name}</strong>,</p>
    <p style="color:#4B5563;font-size:14px;margin-bottom:24px;">
      Congratulations! Your health insurance policy has been issued and is effective immediately.
      Your coverage is active and you are protected under the Adamjee DHA Family Care plan.
    </p>

    <div class="policy-card">
      <div class="label">Your Policy Number</div>
      <div class="pnum">{policy_number}</div>
      <div style="margin-top:8px;font-size:12px;color:#6B7280;">Keep this number for all claims and queries</div>
    </div>

    <table class="detail-table">
      <tr><td>Plan</td><td>{plan_name}</td></tr>
      <tr><td>Coverage From</td><td>{effective_date}</td></tr>
      <tr><td>Coverage Until</td><td>{expiry_date}</td></tr>
      <tr><td>Members Covered</td><td>{member_count} person(s)</td></tr>
      <tr><td>Annual Premium</td><td>AED {annual_premium_aed}</td></tr>
      <tr><td>Monthly Equivalent</td><td>AED {monthly_premium_aed}</td></tr>
      <tr><td>Payment Reference</td><td style="font-family:monospace;">{payment_reference}</td></tr>
      <tr><td>Application Number</td><td style="font-family:monospace;">{application_number}</td></tr>
    </table>

    <div class="steps">
      <h3>What happens next?</h3>
      <div class="step"><div class="step-icon">1</div>Your MEDNET TPA insurance card will be dispatched within 3 business days.</div>
      <div class="step"><div class="step-icon">2</div>Your full policy schedule document will be uploaded to the member portal.</div>
      <div class="step"><div class="step-icon">3</div>You can file claims online via the member portal or at any MEDNET network hospital.</div>
      <div class="step"><div class="step-icon">4</div>For emergencies, show this policy number at any MEDNET network facility — no card needed.</div>
    </div>

    <div class="cta">
      <a href="http://localhost:5173/portal/login">Access Member Portal</a>
    </div>

    <p style="font-size:13px;color:#6B7280;text-align:center;">
      For support: <a href="mailto:customercare@adamjeeinsurance.ae" style="color:#0055A5;">customercare@adamjeeinsurance.ae</a><br>
      Call: +971-4-XXX-XXXX (Sat–Thu, 8am–8pm GST)
    </p>
  </div>

  <div class="footer">
    <p>© 2026 Adamjee Insurance · Licensed by the Insurance Authority of UAE</p>
    <p>This is an automated message. Please do not reply directly to this email.</p>
  </div>
</div>
</body>
</html>"""
        text = (
            f"Dear {customer_name},\n\n"
            f"Your Adamjee Insurance policy {policy_number} is now active.\n\n"
            f"Plan: {plan_name}\n"
            f"Effective: {effective_date}\n"
            f"Expires: {expiry_date}\n"
            f"Members: {member_count}\n"
            f"Annual Premium: AED {annual_premium_aed}\n"
            f"Payment Ref: {payment_reference}\n\n"
            f"For support: customercare@adamjeeinsurance.ae\n"
        )
        return self.send(customer_email, subject, html, text)

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

    def notify_password_reset(self, to_email: str, name: str, token: str) -> bool:
        subject = "Reset your password"
        frontend_url = getattr(self.settings, "frontend_url", "http://localhost:5173")
        reset_url = f"{frontend_url}/reset-password?token={token}"
        html = f"""
        <h2>Dear {name},</h2>
        <p>We received a request to reset your password. Click the button below to choose a new one.</p>
        <p style="margin:24px 0;">
          <a href="{reset_url}"
             style="background:#4F46E5;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:600;">
            Reset Password
          </a>
        </p>
        <p style="color:#6B7280;font-size:13px;">
          This link expires in 1 hour. If you did not request a password reset, you can safely ignore this email.
        </p>
        <p style="color:#6B7280;font-size:12px;">
          Or copy this link: {reset_url}
        </p>
        """
        return self.send(to_email, subject, html)
