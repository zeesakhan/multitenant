from app.worker import celery


@celery.task(bind=True, max_retries=3)
def send_email_task(self, to: str, subject: str, body_html: str) -> dict:
    """Async email sending. Falls back to SMTP logging in dev mode."""
    try:
        from app.services.email_service import EmailService
        EmailService().send(to, subject, body_html)
        return {"status": "sent", "to": to}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery.task
def generate_policy_document_task(policy_id: str) -> dict:
    """Background policy document generation."""
    from app.db.database import _get_session_factory
    from app.services.policy_service import PolicyService

    factory = _get_session_factory()
    db = factory()
    try:
        PolicyService(db).generate_document(policy_id)
        db.commit()
    finally:
        db.close()
    return {"status": "done", "policy_id": policy_id}
