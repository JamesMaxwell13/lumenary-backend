from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0004_alter_project_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[("draft", "Черновик"), ("published", "Опубликовано")],
                default="draft",
                max_length=16,
                verbose_name="Статус",
            ),
        ),
    ]
