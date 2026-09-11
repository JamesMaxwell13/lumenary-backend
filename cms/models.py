from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Page


class HomePage(Page):
    hero_title = models.CharField("Заголовок hero", max_length=255)
    hero_text = models.TextField("Текст hero")
    hero_tags = models.CharField("Строка тегов", max_length=255, blank=True)
    hero_image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Hero изображение",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    hero_video_url = models.URLField("Hero video URL", blank=True)
    services_intro = models.TextField("Вводный текст услуг", blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_text"),
                FieldPanel("hero_tags"),
                FieldPanel("hero_image"),
                FieldPanel("hero_video_url"),
            ],
            heading="Hero",
        ),
        FieldPanel("services_intro"),
    ]


@register_setting
class ContactSettings(BaseSiteSetting):
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Телефон", max_length=64, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    telegram = models.CharField("Telegram", max_length=128, blank=True)
    instagram = models.CharField("Instagram", max_length=128, blank=True)
    youtube = models.CharField("Youtube", max_length=128, blank=True)

    panels = [
        FieldPanel("email"),
        FieldPanel("phone"),
        FieldPanel("address"),
        FieldPanel("telegram"),
        FieldPanel("instagram"),
        FieldPanel("youtube"),
    ]


@register_setting
class FooterSettings(BaseSiteSetting):
    details_text = RichTextField("Реквизиты", blank=True)
    contacts_text = RichTextField("Контакты в футере", blank=True)

    panels = [
        FieldPanel("details_text"),
        FieldPanel("contacts_text"),
    ]
