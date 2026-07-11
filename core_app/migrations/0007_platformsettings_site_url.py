from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_app', '0006_platformsettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='platformsettings',
            name='site_url',
            field=models.CharField(default='nestmatch.io', max_length=200),
        ),
    ]
