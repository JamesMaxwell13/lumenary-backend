from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images import get_image_model_string
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    PUBLISHED = "published", "Опубликовано"


@register_snippet
class ProjectCategory(models.Model):
    title = models.CharField("Название", max_length=120)
    slug = models.SlugField("Slug", unique=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активно", default=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("slug"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
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


@register_snippet
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
        verbose_name="Обложка",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    video_file = models.FileField("Видео-файл", upload_to="project-videos/", blank=True)
    external_video_url = models.URLField("Внешняя видео-ссылка", blank=True)
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
        FieldPanel("category"),
        FieldPanel("title"),
        FieldPanel("slug"),
        FieldPanel("cover_image"),
        FieldPanel("video_file"),
        FieldPanel("external_video_url"),
        FieldPanel("short_caption"),
        FieldPanel("description"),
        MultiFieldPanel(
            [
                FieldPanel("client"),
                FieldPanel("production_year"),
                FieldPanel("role"),
                FieldPanel("detail_title"),
                FieldPanel("detail_text"),
            ],
            heading="Страница проекта",
        ),
        MultiFieldPanel(
            [FieldPanel("seo_title"), FieldPanel("seo_description")],
            heading="SEO",
        ),
        InlinePanel("gallery", label="Галерея"),
        FieldPanel("sort_order"),
        FieldPanel("is_featured"),
        FieldPanel("status"),
        FieldPanel("published_at"),
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
                {"external_video_url": "Use either a video file or an external video URL, not both."}
            )


class ProjectGalleryImage(Orderable):
    project = ParentalKey(Project, on_delete=models.CASCADE, related_name="gallery")
    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Изображение",
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
        verbose_name = "изображение проекта"
        verbose_name_plural = "галерея проекта"
