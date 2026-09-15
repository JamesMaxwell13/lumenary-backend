from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images import get_image_model_string
from wagtail.models import Orderable


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Черновик"
    PUBLISHED = "published", "Опубликовано"


class RentalStatus(models.TextChoices):
    AVAILABLE = "available", "Доступно"
    UNAVAILABLE = "unavailable", "Недоступно"


class AttributeType(models.TextChoices):
    TEXT = "text", "Текст"
    NUMBER = "number", "Число"
    BOOLEAN = "boolean", "Да/нет"
    CHOICE = "choice", "Вариант"


class RentalCategory(MP_Node):
    title = models.CharField("Название", max_length=160)
    slug = models.SlugField("Slug", unique=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показывать на сайте", default=True)

    node_order_by = ["sort_order", "title"]

    panels = [
        FieldPanel("title"),
        MultiFieldPanel(
            [FieldPanel("slug"), FieldPanel("sort_order"), FieldPanel("is_active")],
            heading="Технические настройки",
            classname="collapsed",
        ),
    ]

    class Meta:
        verbose_name = "раздел аренды"
        verbose_name_plural = "разделы аренды"

    def __str__(self) -> str:
        return self.title


class PublishedRentalItemQuerySet(models.QuerySet):
    def published(self):
        return self.filter(publication_status=PublishStatus.PUBLISHED, published_at__lte=timezone.now())


class RentalItem(ClusterableModel, models.Model):
    category = models.ForeignKey(
        RentalCategory,
        verbose_name="Раздел",
        on_delete=models.PROTECT,
        related_name="items",
    )
    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("Slug", unique=True)
    short_description = models.CharField("Короткое описание", max_length=255, blank=True)
    search_aliases = models.TextField("Поисковые варианты", blank=True)
    description = models.TextField("Описание", blank=True)
    detail_description = models.TextField("Подробное описание", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, null=True, blank=True)
    price_on_request = models.BooleanField("Цена по запросу", default=False)
    price_unit = models.CharField("Единица цены", max_length=64, blank=True)
    main_image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Главное изображение",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)
    status = models.CharField(
        "Наличие",
        max_length=24,
        choices=RentalStatus.choices,
        default=RentalStatus.AVAILABLE,
    )
    publication_status = models.CharField(
        "Публикация",
        max_length=16,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Показывать на сайте", default=True)
    published_at = models.DateTimeField("Дата публикации", default=timezone.now)
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    objects = PublishedRentalItemQuerySet.as_manager()

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("category"),
                FieldPanel("title"),
                FieldPanel("short_description"),
                FieldPanel("search_aliases"),
                FieldPanel("description"),
                FieldPanel("detail_description"),
                FieldPanel("main_image"),
            ],
            heading="Позиция аренды",
        ),
        MultiFieldPanel(
            [FieldPanel("price"), FieldPanel("price_on_request"), FieldPanel("price_unit")],
            heading="Цена",
        ),
        InlinePanel("gallery", label="Галерея"),
        InlinePanel("attribute_values", label="Характеристики"),
        MultiFieldPanel(
            [FieldPanel("seo_title"), FieldPanel("seo_description")],
            heading="Для Google и превью ссылок",
            classname="collapsed",
        ),
        MultiFieldPanel(
            [FieldPanel("slug"), FieldPanel("status"), FieldPanel("publication_status"), FieldPanel("sort_order"), FieldPanel("is_active"), FieldPanel("published_at")],
            heading="Технические настройки",
            classname="collapsed",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "позиция аренды"
        verbose_name_plural = "позиции аренды"

    def __str__(self) -> str:
        return self.title

class RentalItemImage(Orderable):
    item = ParentalKey(RentalItem, on_delete=models.CASCADE, related_name="gallery")
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
        verbose_name = "изображение аренды"
        verbose_name_plural = "галерея аренды"


class RentalAttribute(models.Model):
    name = models.CharField("Название", max_length=160)
    slug = models.SlugField("Slug", unique=True)
    type = models.CharField("Тип", max_length=16, choices=AttributeType.choices)
    unit = models.CharField("Единица измерения", max_length=32, blank=True)
    filterable = models.BooleanField("Показывать в фильтрах", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    panels = [
        FieldPanel("name"),
        FieldPanel("type"),
        FieldPanel("unit"),
        MultiFieldPanel(
            [FieldPanel("slug"), FieldPanel("filterable"), FieldPanel("sort_order")],
            heading="Технические настройки",
            classname="collapsed",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "характеристика аренды"
        verbose_name_plural = "характеристики аренды"

    def __str__(self) -> str:
        return self.name


class RentalAttributeValue(Orderable):
    item = ParentalKey(RentalItem, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(RentalAttribute, on_delete=models.CASCADE, related_name="values")
    value_text = models.CharField("Текст", max_length=255, blank=True)
    value_number = models.DecimalField("Число", max_digits=12, decimal_places=3, null=True, blank=True)
    value_boolean = models.BooleanField("Да/нет", null=True, blank=True)
    value_choice = models.CharField("Вариант", max_length=255, blank=True)

    class Meta:
        unique_together = ("item", "attribute")
        verbose_name = "значение характеристики"
        verbose_name_plural = "значения характеристик"

    panels = [
        FieldPanel("attribute"),
        FieldPanel("value_text"),
        FieldPanel("value_number"),
        FieldPanel("value_boolean"),
        FieldPanel("value_choice"),
    ]

    def __str__(self) -> str:
        return f"{self.item}: {self.attribute}"
