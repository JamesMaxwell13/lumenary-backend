from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0005_homepage_hero_title_mobile_alter_homepage_hero_title"),
    ]

    operations = [
        migrations.RemoveField(model_name="contactsettings", name="form_email_label"),
        migrations.RemoveField(model_name="contactsettings", name="form_email_placeholder"),
        migrations.RemoveField(model_name="contactsettings", name="form_message_label"),
        migrations.RemoveField(model_name="contactsettings", name="form_message_placeholder"),
        migrations.RemoveField(model_name="contactsettings", name="form_name_label"),
        migrations.RemoveField(model_name="contactsettings", name="form_name_placeholder"),
        migrations.RemoveField(model_name="contactsettings", name="form_phone_label"),
        migrations.RemoveField(model_name="contactsettings", name="form_phone_placeholder"),
        migrations.RemoveField(model_name="contactsettings", name="form_title"),
        migrations.DeleteModel(name="FooterSettings"),
    ]
