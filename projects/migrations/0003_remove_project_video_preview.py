import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F


def copy_video_preview_to_cover(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    Project.objects.filter(cover_image__isnull=True, video_preview__isnull=False).update(
        cover_image_id=F("video_preview_id")
    )


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_alter_projectgalleryimage_options_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_video_preview_to_cover, migrations.RunPython.noop),
        migrations.RemoveField(model_name="project", name="video_preview"),
        migrations.AlterField(
            model_name="project",
            name="cover_image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtailimages.image",
                verbose_name="Обложка / превью видео",
            ),
        ),
    ]
