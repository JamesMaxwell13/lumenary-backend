from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class ServiceBlock(models.Model):
    title = models.CharField("Заголовок", max_length=120)
    text = models.TextField("Текст")
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активно", default=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("text"),
        MultiFieldPanel(
            [FieldPanel("sort_order"), FieldPanel("is_active")],
            heading="Технические настройки",
            classname="collapsed",
        ),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "блок услуги"
        verbose_name_plural = "блоки услуг"

    def __str__(self) -> str:
        return self.title
