from django.db import models
from wagtail.snippets.models import register_snippet


class NotificationStatus(models.TextChoices):
    PENDING = "pending", "Ожидает"
    SENT = "sent", "Отправлено"
    FAILED = "failed", "Ошибка"
    SKIPPED = "skipped", "Пропущено"


@register_snippet
class NotificationEvent(models.Model):
    type = models.CharField("Тип", max_length=64)
    lead = models.ForeignKey(
        "leads.Lead",
        verbose_name="Заявка",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notification_events",
    )
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
    )
    payload = models.JSONField("Payload", default=dict, blank=True)
    error_message = models.TextField("Ошибка", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    sent_at = models.DateTimeField("Отправлено", null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "событие уведомления"
        verbose_name_plural = "события уведомлений"

    def __str__(self) -> str:
        return f"{self.type}: {self.status}"
