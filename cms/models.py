from django.db import models
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Page


class HomePage(Page):
    hero_title = models.CharField("Заголовок первого экрана", max_length=255)
    hero_text = models.TextField("Текст первого экрана")
    hero_tags = models.CharField("Строка тегов", max_length=255, blank=True)
    hero_image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Обложка showreel",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    hero_video_url = models.URLField("Ссылка на основной showreel", blank=True)
    nav_about_label = models.CharField("Меню: о нас", max_length=64, default="О НАС")
    nav_services_label = models.CharField("Меню: услуги", max_length=64, default="УСЛУГИ")
    nav_projects_label = models.CharField("Меню: проекты", max_length=64, default="ПРОЕКТЫ")
    nav_rental_label = models.CharField("Меню: аренда", max_length=64, default="АРЕНДА")
    nav_contacts_label = models.CharField("Меню: контакты", max_length=64, default="КОНТАКТЫ")

    content_panels = Page.content_panels + [
        HelpPanel(
            content=(
                "<p>Здесь редактируется только первый экран главной страницы из Figma: "
                "название продакшена, описание и основной showreel. Услуги, портфолио, "
                "аренда и контакты находятся рядом в отдельных пунктах меню.</p>"
            )
        ),
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_text"),
                FieldPanel("hero_tags"),
                FieldPanel("hero_image"),
                FieldPanel("hero_video_url"),
            ],
            heading="Первый экран и showreel",
        ),
        MultiFieldPanel(
            [
                FieldPanel("nav_about_label"),
                FieldPanel("nav_services_label"),
                FieldPanel("nav_projects_label"),
                FieldPanel("nav_rental_label"),
                FieldPanel("nav_contacts_label"),
            ],
            heading="Меню сайта",
        ),
    ]


@register_setting
class MainPageSectionSettings(BaseSiteSetting):
    services_title = models.CharField("Заголовок блока услуг", max_length=120, default="УСЛУГИ")
    services_intro = models.TextField("Вводный текст услуг", blank=True)
    projects_title = models.CharField("Заголовок портфолио", max_length=120, default="НАШИ ПРОЕКТЫ")
    rental_title = models.CharField("Заголовок аренды", max_length=120, default="АРЕНДА")
    rental_search_label = models.CharField("Подпись поиска аренды", max_length=64, default="ПОИСК")

    panels = [
        HelpPanel(
            content=(
                "<p>Эти тексты относятся к секциям главной страницы ниже первого экрана. "
                "Карточки услуг, проекты и позиции аренды редактируются в соседних разделах админки.</p>"
            )
        ),
        MultiFieldPanel(
            [FieldPanel("services_title"), FieldPanel("services_intro")],
            heading="Услуги",
        ),
        MultiFieldPanel([FieldPanel("projects_title")], heading="Портфолио"),
        MultiFieldPanel(
            [FieldPanel("rental_title"), FieldPanel("rental_search_label")],
            heading="Аренда",
        ),
    ]

    class Meta:
        verbose_name = "тексты секций главной"
        verbose_name_plural = "тексты секций главной"


@register_setting
class ContactSettings(BaseSiteSetting):
    section_title = models.CharField("Заголовок контактов", max_length=120, default="КОНТАКТЫ")
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Телефон", max_length=64, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    telegram = models.CharField("Telegram", max_length=128, blank=True)
    instagram = models.CharField("Instagram", max_length=128, blank=True)
    youtube = models.CharField("Youtube", max_length=128, blank=True)
    form_title = models.CharField("Заголовок формы связи", max_length=120, default="СВЯЗАТЬСЯ С НАМИ")
    form_name_label = models.CharField("Подпись имени", max_length=64, default="Имя")
    form_name_placeholder = models.CharField("Подсказка имени", max_length=120, default="Как к вам обращаться?")
    form_phone_label = models.CharField("Подпись телефона", max_length=64, default="Телефон")
    form_phone_placeholder = models.CharField("Подсказка телефона", max_length=120, default="+375-XX-XXXXXX")
    form_email_label = models.CharField("Подпись email", max_length=64, default="Email")
    form_email_placeholder = models.CharField("Подсказка email", max_length=120, default="email@mail.com")
    form_message_label = models.CharField("Подпись сообщения", max_length=64, default="Сообщение")
    form_message_placeholder = models.CharField("Подсказка сообщения", max_length=120, default="Ваш текст")

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("section_title"),
                FieldPanel("email"),
                FieldPanel("phone"),
                FieldPanel("address"),
                FieldPanel("telegram"),
                FieldPanel("instagram"),
                FieldPanel("youtube"),
            ],
            heading="Контакты на сайте",
        ),
        MultiFieldPanel(
            [
                FieldPanel("form_title"),
                FieldPanel("form_name_label"),
                FieldPanel("form_name_placeholder"),
                FieldPanel("form_phone_label"),
                FieldPanel("form_phone_placeholder"),
                FieldPanel("form_email_label"),
                FieldPanel("form_email_placeholder"),
                FieldPanel("form_message_label"),
                FieldPanel("form_message_placeholder"),
            ],
            heading="Форма связи",
        ),
    ]


@register_setting
class FooterSettings(BaseSiteSetting):
    details_text = RichTextField("Реквизиты", blank=True)
    contacts_text = RichTextField("Контакты в футере", blank=True)

    panels = [
        MultiFieldPanel(
            [FieldPanel("details_text"), FieldPanel("contacts_text")],
            heading="Текст внизу сайта",
        ),
    ]
