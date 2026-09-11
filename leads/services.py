from django.db import transaction
from django.conf import settings

from leads.models import Lead, LeadType, RentalLeadItem
from notifications.tasks import send_lead_to_telegram, skip_lead_telegram_notification


def create_contact_lead(**validated_data):
    with transaction.atomic():
        lead = Lead.objects.create(type=LeadType.CONTACT, source="contact_form", **validated_data)
        enqueue_lead_notification(lead)
    return lead


def create_rental_lead(*, items, **validated_data):
    with transaction.atomic():
        lead = Lead.objects.create(type=LeadType.RENTAL, source="rental_selection", **validated_data)
        RentalLeadItem.objects.bulk_create(
            [
                RentalLeadItem(
                    lead=lead,
                    rental_item=item["rental_item"],
                    quantity=item.get("quantity", 1),
                    comment=item.get("comment", ""),
                )
                for item in items
            ]
        )
        enqueue_lead_notification(lead)
    return lead


def enqueue_lead_notification(lead):
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        transaction.on_commit(lambda: send_lead_to_telegram.delay(lead.id))
    else:
        transaction.on_commit(lambda: skip_lead_telegram_notification(lead.id))
