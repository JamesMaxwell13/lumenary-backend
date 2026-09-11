from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from treebeard.mp_tree import MP_Node
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images import get_image_model_string
from wagtail.models import Orderable


class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"


class RentalStatus(models.TextChoices):
    AVAILABLE = "available", "Available"
    UNAVAILABLE = "unavailable", "Unavailable"


class AttributeType(models.TextChoices):
    TEXT = "text", "Text"
    NUMBER = "number", "Number"
    BOOLEAN = "boolean", "Boolean"
    CHOICE = "choice", "Choice"


class RentalCategory(MP_Node):
    title = models.CharField("Title", max_length=160)
    slug = models.SlugField("Slug", unique=True)
    sort_order = models.PositiveIntegerField("Sort order", default=0)
    is_active = models.BooleanField("Active", default=True)

    node_order_by = ["sort_order", "title"]

    panels = [
        FieldPanel("title"),
        FieldPanel("slug"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]

    class Meta:
        verbose_name = "rental category"
        verbose_name_plural = "rental categories"

    def __str__(self) -> str:
        return self.title


class PublishedRentalItemQuerySet(models.QuerySet):
    def published(self):
        return self.filter(publication_status=PublishStatus.PUBLISHED, published_at__lte=timezone.now())


class RentalItem(ClusterableModel, models.Model):
    category = models.ForeignKey(
        RentalCategory,
        verbose_name="Category",
        on_delete=models.PROTECT,
        related_name="items",
    )
    title = models.CharField("Title", max_length=255)
    slug = models.SlugField("Slug", unique=True)
    short_description = models.CharField("Short description", max_length=255, blank=True)
    description = models.TextField("Description", blank=True)
    detail_description = models.TextField("Detail description", blank=True)
    price = models.DecimalField("Price", max_digits=10, decimal_places=2, null=True, blank=True)
    price_on_request = models.BooleanField("Price on request", default=False)
    price_unit = models.CharField("Price unit", max_length=64, blank=True)
    main_image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Main image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    video_file = models.FileField("Video file", upload_to="rental-videos/", blank=True)
    external_video_url = models.URLField("External video URL", blank=True)
    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)
    status = models.CharField(
        "Availability",
        max_length=24,
        choices=RentalStatus.choices,
        default=RentalStatus.AVAILABLE,
    )
    publication_status = models.CharField(
        "Publication status",
        max_length=16,
        choices=PublishStatus.choices,
        default=PublishStatus.DRAFT,
    )
    sort_order = models.PositiveIntegerField("Sort order", default=0)
    is_active = models.BooleanField("Active", default=True)
    published_at = models.DateTimeField("Published at", default=timezone.now)
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    objects = PublishedRentalItemQuerySet.as_manager()

    panels = [
        FieldPanel("category"),
        FieldPanel("title"),
        FieldPanel("slug"),
        FieldPanel("short_description"),
        FieldPanel("description"),
        FieldPanel("detail_description"),
        MultiFieldPanel(
            [FieldPanel("price"), FieldPanel("price_on_request"), FieldPanel("price_unit")],
            heading="Price",
        ),
        FieldPanel("main_image"),
        FieldPanel("video_file"),
        FieldPanel("external_video_url"),
        MultiFieldPanel(
            [FieldPanel("seo_title"), FieldPanel("seo_description")],
            heading="SEO",
        ),
        InlinePanel("gallery", label="Gallery"),
        InlinePanel("attribute_values", label="Attributes"),
        FieldPanel("status"),
        FieldPanel("publication_status"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
        FieldPanel("published_at"),
    ]

    class Meta:
        ordering = ["sort_order", "title"]
        verbose_name = "rental item"
        verbose_name_plural = "rental items"

    def __str__(self) -> str:
        return self.title

    def clean(self):
        super().clean()
        if self.video_file and self.external_video_url:
            raise ValidationError(
                {"external_video_url": "Use either a video file or an external video URL, not both."}
            )


class RentalItemImage(Orderable):
    item = ParentalKey(RentalItem, on_delete=models.CASCADE, related_name="gallery")
    image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="Image",
        on_delete=models.CASCADE,
        related_name="+",
    )
    caption = models.CharField("Caption", max_length=255, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "rental image"
        verbose_name_plural = "rental gallery"


class RentalAttribute(models.Model):
    name = models.CharField("Name", max_length=160)
    slug = models.SlugField("Slug", unique=True)
    type = models.CharField("Type", max_length=16, choices=AttributeType.choices)
    unit = models.CharField("Unit", max_length=32, blank=True)
    filterable = models.BooleanField("Use in filters", default=True)
    sort_order = models.PositiveIntegerField("Sort order", default=0)

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("type"),
        FieldPanel("unit"),
        FieldPanel("filterable"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "rental attribute"
        verbose_name_plural = "rental attributes"

    def __str__(self) -> str:
        return self.name


class RentalAttributeValue(Orderable):
    item = ParentalKey(RentalItem, on_delete=models.CASCADE, related_name="attribute_values")
    attribute = models.ForeignKey(RentalAttribute, on_delete=models.CASCADE, related_name="values")
    value_text = models.CharField("Text", max_length=255, blank=True)
    value_number = models.DecimalField("Number", max_digits=12, decimal_places=3, null=True, blank=True)
    value_boolean = models.BooleanField("Boolean", null=True, blank=True)
    value_choice = models.CharField("Choice", max_length=255, blank=True)

    class Meta:
        unique_together = ("item", "attribute")
        verbose_name = "rental attribute value"
        verbose_name_plural = "rental attribute values"

    panels = [
        FieldPanel("attribute"),
        FieldPanel("value_text"),
        FieldPanel("value_number"),
        FieldPanel("value_boolean"),
        FieldPanel("value_choice"),
    ]

    def __str__(self) -> str:
        return f"{self.item}: {self.attribute}"
