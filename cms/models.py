from django.core.exceptions import ValidationError
from django.db import models
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.images import get_image_model_string
from wagtail.models import Page

from cms.videos import validate_external_video_url


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
    hero_video_file = models.FileField("Видео-файл showreel", upload_to="showreel-videos/", blank=True)
    hero_video_url = models.URLField(
        "Ссылка на основной showreel",
        blank=True,
        help_text="YouTube, Vimeo или прямая ссылка на MP4-файл.",
    )
    nav_about_label = models.CharField("Меню: о нас", max_length=64, blank=True)
    nav_services_label = models.CharField("Меню: услуги", max_length=64, blank=True)
    nav_projects_label = models.CharField("Меню: проекты", max_length=64, blank=True)
    nav_rental_label = models.CharField("Меню: аренда", max_length=64, blank=True)
    nav_contacts_label = models.CharField("Меню: контакты", max_length=64, blank=True)

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
                FieldPanel("hero_video_file"),
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

    def clean(self):
        super().clean()
        if self.hero_video_file and self.hero_video_url:
            raise ValidationError(
                {"hero_video_url": "Укажите видео-файл или внешнюю ссылку, но не оба варианта одновременно."}
            )
        try:
            validate_external_video_url(self.hero_video_url)
        except ValidationError as error:
            raise ValidationError({"hero_video_url": error.messages}) from error


@register_setting
class MainPageSectionSettings(BaseSiteSetting):
    services_title = models.CharField("Заголовок блока услуг", max_length=120, blank=True)
    services_intro = models.TextField("Вводный текст услуг", blank=True)
    projects_title = models.CharField("Заголовок портфолио", max_length=120, blank=True)
    projects_page_intro = models.TextField("Описание страницы проектов", blank=True)
    projects_cta_title = models.CharField("Заголовок призыва в проектах", max_length=160, blank=True)
    projects_cta_text = models.TextField("Текст призыва в проектах", blank=True)
    rental_title = models.CharField("Заголовок аренды", max_length=120, blank=True)
    rental_search_label = models.CharField("Подпись поиска аренды", max_length=64, blank=True)
    rental_page_intro = models.TextField("Описание страницы аренды", blank=True)
    rental_cta_title = models.CharField("Заголовок призыва в аренде", max_length=160, blank=True)
    rental_cta_text = models.TextField("Текст призыва в аренде", blank=True)

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
        MultiFieldPanel(
            [
                FieldPanel("projects_title"),
                FieldPanel("projects_page_intro"),
                FieldPanel("projects_cta_title"),
                FieldPanel("projects_cta_text"),
            ],
            heading="Проекты",
        ),
        MultiFieldPanel(
            [
                FieldPanel("rental_title"),
                FieldPanel("rental_search_label"),
                FieldPanel("rental_page_intro"),
                FieldPanel("rental_cta_title"),
                FieldPanel("rental_cta_text"),
            ],
            heading="Аренда",
        ),
    ]

    class Meta:
        verbose_name = "тексты секций главной"
        verbose_name_plural = "тексты секций главной"


@register_setting
class ContactSettings(BaseSiteSetting):
    section_title = models.CharField("Заголовок контактов", max_length=120, blank=True)
    section_intro = models.TextField("Описание блока контактов", blank=True)
    email = models.EmailField("Email", blank=True)
    phone = models.CharField("Телефон", max_length=64, blank=True)
    address = models.CharField("Адрес", max_length=255, blank=True)
    telegram = models.CharField("Telegram", max_length=128, blank=True)
    instagram = models.CharField("Instagram", max_length=128, blank=True)
    youtube = models.CharField("Youtube", max_length=128, blank=True)
    footer_legal_text = models.TextField("Юридический текст в футере", blank=True)

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("section_title"),
                FieldPanel("section_intro"),
                FieldPanel("email"),
                FieldPanel("phone"),
                FieldPanel("address"),
                FieldPanel("telegram"),
                FieldPanel("instagram"),
                FieldPanel("youtube"),
                FieldPanel("footer_legal_text"),
            ],
            heading="Контакты на сайте",
        ),
    ]
