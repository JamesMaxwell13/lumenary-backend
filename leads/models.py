from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable


class LeadType(models.TextChoices):
    CONTACT = "contact", "Общая заявка"
    RENTAL = "rental", "Заявка на аренду"


class LeadStatus(models.TextChoices):
    NEW = "new", "Новая"
    IN_PROGRESS = "in_progress", "В работе"
    DONE = "done", "Закрыта"
    ARCHIVED = "archived", "В архиве"


class Lead(ClusterableModel, models.Model):
    type = models.CharField("Тип заявки", max_length=24, choices=LeadType.choices)
    name = models.CharField("Имя", max_length=255)
    phone = models.CharField("Телефон", max_length=64)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Сообщение", blank=True)
    rental_start_date = models.DateField("Дата начала аренды", null=True, blank=True)
    rental_end_date = models.DateField("Дата окончания аренды", null=True, blank=True)
    status = models.CharField(
        "Статус",
        max_length=24,
        choices=LeadStatus.choices,
        default=LeadStatus.NEW,
    )
    source = models.CharField("Источник", max_length=64, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    panels = [
        FieldPanel("type"),
        FieldPanel("name"),
        FieldPanel("phone"),
        FieldPanel("email"),
        FieldPanel("message"),
        MultiFieldPanel(
            [FieldPanel("rental_start_date"), FieldPanel("rental_end_date")],
            heading="Даты аренды",
        ),
        InlinePanel("rental_items", label="Позиции аренды"),
        FieldPanel("status"),
        FieldPanel("source"),
    ]

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "заявка"
        verbose_name_plural = "заявки"

    def __str__(self) -> str:
        return f"{self.get_type_display()} #{self.pk}: {self.name}"


class RentalLeadItem(Orderable):
    lead = ParentalKey(Lead, on_delete=models.CASCADE, related_name="rental_items")
    rental_item = models.ForeignKey("rental.RentalItem", on_delete=models.PROTECT, related_name="lead_items")
    quantity = models.PositiveIntegerField("Количество", default=1)
    comment = models.CharField("Комментарий", max_length=255, blank=True)

    panels = [
        FieldPanel("rental_item"),
        FieldPanel("quantity"),
        FieldPanel("comment"),
    ]

    class Meta:
        verbose_name = "позиция в заявке"
        verbose_name_plural = "позиции в заявке"

    def __str__(self) -> str:
        return f"{self.rental_item} x {self.quantity}"
