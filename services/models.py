from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class ServiceBlock(models.Model):
    title = models.CharField("Заголовок", max_length=120)
    text = models.TextField("Текст")
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активно", default=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("text"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "блок услуги"
        verbose_name_plural = "блоки услуг"

    def __str__(self) -> str:
        return self.title
