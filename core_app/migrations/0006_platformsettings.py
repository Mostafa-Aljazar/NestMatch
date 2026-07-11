from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core_app', '0005_remove_testimonial_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform_name', models.CharField(default='NestMatch', max_length=80)),
                ('support_email', models.EmailField(default='hello@nestmatch.io', max_length=254)),
                ('max_listing_photos', models.PositiveSmallIntegerField(default=10)),
                ('auto_approve_listings', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Platform Settings',
                'verbose_name_plural': 'Platform Settings',
            },
        ),
    ]
