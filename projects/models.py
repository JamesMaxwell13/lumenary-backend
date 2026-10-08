from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images import get_image_model_string
from wagtail.models import Orderable

from cms.videos import validate_external_video_url


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    PUBLISHED = "published", "Опубликовано"


class ProjectCategory(models.Model):
    title = models.CharField("Название", max_length=120)
    slug = models.SlugField("Slug", unique=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активно", default=True)

    panels = [
        FieldPanel("title"),
        MultiFieldPanel(
            [FieldPanel("slug"), FieldPanel("sort_order"), FieldPanel("is_active")],
            heading="Технические настройки",
            classname="collapsed",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "категория проекта"
        verbose_name_plural = "категории проектов"

    def __str__(self) -> str:
        return self.title


class PublishedProjectQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=PublishStatus.PUBLISHED, published_at__lte=timezone.now())


class Project(ClusterableModel, models.Model):
    category = models.ForeignKey(
        ProjectCategory,
        verbose_name="Категория",
        on_delete=models.PROTECT,
        related_name="projects",
    )
    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug", unique=True)
    cover_image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Обложка / превью видео",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    video_file = models.FileField("Видео-файл", upload_to="project-videos/", blank=True)
    external_video_url = models.URLField(
        "Внешняя видео-ссылка",
        blank=True,
        help_text="YouTube, Vimeo или прямая ссылка на MP4-файл.",
    )
    short_caption = models.CharField("Подпись карточки", max_length=255, blank=True)
    description = models.TextField("Краткое описание", blank=True)
    client = models.CharField("Клиент", max_length=255, blank=True)
    production_year = models.PositiveIntegerField("Год", null=True, blank=True)
    role = models.CharField("Роль/задача", max_length=255, blank=True)
    detail_title = models.CharField("Заголовок detail", max_length=255, blank=True)
    detail_text = models.TextField("Текст кейса", blank=True)
    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_featured = models.BooleanField("Показывать на главной", default=False)
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )
    published_at = models.DateTimeField("Дата публикации", default=timezone.now)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    objects = PublishedProjectQuerySet.as_manager()

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("category"),
                FieldPanel("title"),
                FieldPanel("cover_image"),
                FieldPanel("video_file"),
                FieldPanel("external_video_url"),
                FieldPanel("short_caption"),
                FieldPanel("description"),
            ],
            heading="Карточка проекта",
        ),
        MultiFieldPanel(
            [
                FieldPanel("status"),
                FieldPanel("published_at"),
                FieldPanel("is_featured"),
            ],
            heading="Публикация",
        ),
        MultiFieldPanel(
            [
                FieldPanel("client"),
                FieldPanel("production_year"),
                FieldPanel("role"),
                FieldPanel("detail_title", heading="Заголовок страницы проекта"),
                FieldPanel("detail_text", heading="Описание проекта"),
            ],
            heading="Страница проекта",
        ),
        InlinePanel("gallery", label="Скриншоты проекта"),
        MultiFieldPanel(
            [FieldPanel("seo_title"), FieldPanel("seo_description")],
            heading="Для Google и превью ссылок",
            classname="collapsed",
        ),
        MultiFieldPanel(
            [FieldPanel("slug"), FieldPanel("sort_order")],
            heading="Технические настройки",
            classname="collapsed",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "-published_at", "title"]
        verbose_name = "проект"
        verbose_name_plural = "проекты"

    def __str__(self) -> str:
        return self.title

    def clean(self):
        super().clean()
        if self.video_file and self.external_video_url:
            raise ValidationError(
                {"external_video_url": "Укажите видео-файл или внешнюю ссылку, но не оба варианта одновременно."}
            )
        try:
            validate_external_video_url(self.external_video_url)
        except ValidationError as error:
            raise ValidationError({"external_video_url": error.messages}) from error


class ProjectGalleryImage(Orderable):
    project = ParentalKey(Project, on_delete=models.CASCADE, related_name="gallery")
    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Скриншот",
        on_delete=models.CASCADE,
        related_name="+",
    )
    caption = models.CharField("Подпись", max_length=255, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "скриншот проекта"
        verbose_name_plural = "скриншоты проекта"
