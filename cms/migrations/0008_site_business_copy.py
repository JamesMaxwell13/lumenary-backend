from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0007_homepage_hero_video_file_remove_preview"),
    ]

    operations = [
        migrations.AddField(
            model_name="mainpagesectionsettings",
            name="projects_page_intro",
            field=models.TextField(
                blank=True,
                default="Выберите категорию и откройте страницу проекта с видео, кадрами и описанием.",
                verbose_name="Описание страницы проектов",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="mainpagesectionsettings",
            name="projects_cta_title",
            field=models.CharField(blank=True, default="У вас есть своя идея?", max_length=160, verbose_name="Заголовок призыва в проектах"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="mainpagesectionsettings",
            name="projects_cta_text",
            field=models.TextField(blank=True, default="Проконсультируем и поможем воплотить вашу идею с гарантированным результатом.", verbose_name="Текст призыва в проектах"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="mainpagesectionsettings",
            name="rental_page_intro",
            field=models.TextField(blank=True, default="Выберите раздел, подраздел или найдите позицию по названию.", verbose_name="Описание страницы аренды"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="mainpagesectionsettings",
            name="rental_cta_title",
            field=models.CharField(blank=True, default="Нужна консультация?", max_length=160, verbose_name="Заголовок призыва в аренде"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="mainpagesectionsettings",
            name="rental_cta_text",
            field=models.TextField(blank=True, default="Напишите нам и мы поможем подобрать реквизит или костюмы для вашей задумки", verbose_name="Текст призыва в аренде"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="contactsettings",
            name="section_intro",
            field=models.TextField(blank=True, default="Напишите продакшену напрямую. Быстрее всего связаться в Telegram или по телефону, а детали съемки, аренды и постпродакшна согласуем в личном разговоре.", verbose_name="Описание блока контактов"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="contactsettings",
            name="footer_legal_text",
            field=models.TextField(blank=True, default='© 2026 Lumenary\nООО "РэдКвин" УНП 193775701\nЮр. адрес: 220040 г.Минск 3-й переулок Можайского д.11, пом. 109', verbose_name="Юридический текст в футере"),
            preserve_default=False,
        ),
    ]
