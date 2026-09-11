from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet


class LeadType(models.TextChoices):
    CONTACT = "contact", "Contact"
    RENTAL = "rental", "Rental"


class LeadStatus(models.TextChoices):
    NEW = "new", "New"
    IN_PROGRESS = "in_progress", "In progress"
    DONE = "done", "Done"
    ARCHIVED = "archived", "Archived"


@register_snippet
class Lead(ClusterableModel, models.Model):
    type = models.CharField("Type", max_length=24, choices=LeadType.choices)
    name = models.CharField("Name", max_length=255)
    phone = models.CharField("Phone", max_length=64)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Message", blank=True)
    rental_start_date = models.DateField("Rental start date", null=True, blank=True)
    rental_end_date = models.DateField("Rental end date", null=True, blank=True)
    status = models.CharField(
        "Status",
        max_length=24,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
    )
    source = models.CharField("Source", max_length=64, blank=True)
    created_at = models.DateTimeField("Created at", auto_now_add=True)
    updated_at = models.DateTimeField("Updated at", auto_now=True)

    panels = [
        FieldPanel("type"),
        FieldPanel("name"),
        FieldPanel("phone"),
        FieldPanel("email"),
        FieldPanel("message"),
        MultiFieldPanel(
            [FieldPanel("rental_start_date"), FieldPanel("rental_end_date")],
            heading="Rental dates",
        ),
        InlinePanel("rental_items", label="Rental items"),
        FieldPanel("status"),
        FieldPanel("source"),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "lead"
        verbose_name_plural = "leads"

    def __str__(self) -> str:
        return f"{self.get_type_display()} #{self.pk}: {self.name}"


class RentalLeadItem(Orderable):
    lead = ParentalKey(Lead, on_delete=models.CASCADE, related_name="rental_items")
    rental_item = models.ForeignKey("rental.RentalItem", on_delete=models.PROTECT, related_name="lead_items")
    quantity = models.PositiveIntegerField("Quantity", default=1)
    comment = models.CharField("Comment", max_length=255, blank=True)

    panels = [
        FieldPanel("rental_item"),
        FieldPanel("quantity"),
        FieldPanel("comment"),
    ]

    class Meta:
        verbose_name = "rental lead item"
        verbose_name_plural = "rental lead items"

    def __str__(self) -> str:
        return f"{self.rental_item} x {self.quantity}"
