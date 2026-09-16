from django.db import models
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.images import get_image_model_string
from wagtail.models import Page


class HomePage(Page):
    hero_title = models.TextField("Заголовок первого экрана")
    hero_title_mobile = models.TextField("Заголовок первого экрана на мобильных", blank=True)
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
    hero_video_preview = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Превью основного showreel",
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
                "<p><strong>Главная страница.</strong> Здесь редактируется первый экран сайта: "
                "крупный заголовок, текст под ним, строка тегов, обложка и ссылка на showreel. "
                "Если нужен перенос строки в заголовке или тегах, поставьте перенос прямо в поле.</p>"
                "<p>Блоки услуг, проекты, аренда, контакты и футер редактируются в соседних "
                "разделах админки. После изменений нажмите <strong>Опубликовать</strong>, иначе "
                "посетители сайта не увидят обновление.</p>"
            )
        ),
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_title_mobile"),
                FieldPanel("hero_text"),
                FieldPanel("hero_tags"),
                FieldPanel("hero_image"),
                FieldPanel("hero_video_preview"),
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
                "<p><strong>Тексты секций главной.</strong> Здесь задаются названия и короткие подписи "
                "для блоков ниже первого экрана. Не добавляйте сюда сами карточки: услуги, проекты "
                "и позиции аренды управляются в своих разделах.</p>"
                "<p>Используйте короткие понятные формулировки: заголовок должен помещаться в меню "
                "и на мобильном экране, а вводный текст лучше держать в пределах одного-двух предложений.</p>"
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
    ]
