from django.db import migrations, models
from django.db.models import F


def copy_video_preview_to_cover(apps, schema_editor):
    HomePage = apps.get_model("cms", "HomePage")
    HomePage.objects.filter(hero_image__isnull=True, hero_video_preview__isnull=False).update(
        hero_image_id=F("hero_video_preview_id")
    )


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0006_remove_contact_form_and_footer_settings"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="hero_video_file",
            field=models.FileField(blank=True, upload_to="showreel-videos/", verbose_name="Видео-файл showreel"),
        ),
        migrations.RunPython(copy_video_preview_to_cover, migrations.RunPython.noop),
        migrations.RemoveField(model_name="homepage", name="hero_video_preview"),
    ]
