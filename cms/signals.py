from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from cms.cache import clear_public_api_cache
from cms.models import ContactSettings, FooterSettings
from projects.models import Project, ProjectCategory
from rental.models import RentalAttribute, RentalAttributeValue, RentalCategory, RentalItem
from services.models import ServiceBlock


CONTENT_MODELS = (
    ContactSettings,
    FooterSettings,
    Project,
    ProjectCategory,
    RentalAttribute,
    RentalAttributeValue,
    RentalCategory,
    RentalItem,
    ServiceBlock,
)


@receiver(post_save)
@receiver(post_delete)
def clear_public_cache_on_content_change(sender, **kwargs):
    if sender in CONTENT_MODELS:
        clear_public_api_cache()
