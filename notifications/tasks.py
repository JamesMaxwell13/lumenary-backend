import json
import urllib.parse
import urllib.request

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from leads.models import Lead, LeadType
from notifications.models import NotificationEvent, NotificationStatus


def build_lead_admin_url(lead: Lead) -> str:
    return f"{settings.ADMIN_BASE_URL.rstrip('/')}/admin/snippets/leads/lead/edit/{lead.id}/"


def build_telegram_message(lead: Lead) -> str:
    lines = [
        "Новая заявка lumEnary",
        f"Тип: {lead.get_type_display()}",
        f"Имя: {lead.name}",
        f"Телефон: {lead.phone}",
    ]
    if lead.email:
        lines.append(f"Email: {lead.email}")
    if lead.type == LeadType.RENTAL:
        period = "не указан"
        if lead.rental_start_date or lead.rental_end_date:
            period = f"{lead.rental_start_date or '...'} - {lead.rental_end_date or '...'}"
        lines.append(f"Период аренды: {period}")
        lines.append("Позиции:")
        for item in lead.rental_items.select_related("rental_item").all():
            comment = f" ({item.comment})" if item.comment else ""
            lines.append(f"- {item.rental_item.title} x {item.quantity}{comment}")
    if lead.message:
        lines.append(f"Сообщение: {lead.message}")
    lines.append(f"Админка: {build_lead_admin_url(lead)}")
    return "\n".join(lines)


def skip_lead_telegram_notification(lead_id: int):
    lead = Lead.objects.prefetch_related("rental_items__rental_item").get(id=lead_id)
    message = build_telegram_message(lead)
    event = NotificationEvent.objects.create(
        type="telegram.lead_created",
        lead=lead,
        status=NotificationStatus.SKIPPED,
        payload={"text": message},
        error_message="TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured.",
    )
    return event.id


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_lead_to_telegram(self, lead_id: int):
    lead = Lead.objects.prefetch_related("rental_items__rental_item").get(id=lead_id)
    message = build_telegram_message(lead)
    event = NotificationEvent.objects.create(
        type="telegram.lead_created",
        lead=lead,
        payload={"text": message},
    )

    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        event.status = NotificationStatus.SKIPPED
        event.error_message = "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured."
        event.save(update_fields=["status", "error_message"])
        return event.id

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": settings.TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": "true",
        }
    ).encode()

    try:
        request = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
        if not body.get("ok"):
            raise RuntimeError(body)
    except Exception as exc:
        event.status = NotificationStatus.FAILED
        event.error_message = str(exc)
        event.save(update_fields=["status", "error_message"])
        raise self.retry(exc=exc)

    event.status = NotificationStatus.SENT
    event.sent_at = timezone.now()
    event.save(update_fields=["status", "sent_at"])
    return event.id
