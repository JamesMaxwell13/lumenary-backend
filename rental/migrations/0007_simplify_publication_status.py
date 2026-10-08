from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rental", "0006_alter_rentalitem_publication_status"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="rentalitem",
            name="is_active",
        ),
        migrations.AlterField(
            model_name="rentalitem",
            name="publication_status",
            field=models.CharField(
                choices=[("draft", "Черновик"), ("published", "Опубликовано")],
                default="draft",
                max_length=16,
                verbose_name="Публикация",
            ),
        ),
    ]
