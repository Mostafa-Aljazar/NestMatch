from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_app', '0005_lifestyleprofile_alcohol_ok_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='roommate_gender_pref',
            field=models.CharField(choices=[('males_only', 'Males only'), ('females_only', 'Females only'), ('any', 'No preference')], max_length=15),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='budget_min',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='budget_max',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='dietary',
            field=models.CharField(choices=[('none', 'No restrictions'), ('vegetarian', 'Vegetarian'), ('halal', 'Halal only'), ('no_seafood', 'No seafood')], max_length=15),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='guest_tolerance',
            field=models.CharField(choices=[('strict', 'Prefers few/no guests'), ('moderate', 'Occasional guests OK'), ('relaxed', 'Frequent guests OK')], max_length=10),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='tenant_type',
            field=models.CharField(choices=[('students', 'Student'), ('professionals', 'Working professional'), ('families', 'Family'), ('anyone', 'Other')], max_length=15),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='household_lang_pref',
            field=models.CharField(choices=[('english', 'English-speaking household'), ('arabic', 'Arabic-only household'), ('local', 'Locals preferred'), ('mixed', 'Mixed nationalities'), ('no_preference', 'No preference')], max_length=15),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='alcohol_ok',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='min_stay_pref',
            field=models.PositiveSmallIntegerField(choices=[(1, '1 Month'), (2, '2 Months'), (3, '3 Months'), (6, '6 Months'), (12, '1 Year'), (0, 'Flexible')]),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='listing_type_pref',
            field=models.CharField(choices=[('private_room', 'Private Room'), ('full_apartment', 'Full Apartment'), ('shared_bed', 'Shared Bed'), ('roommate_wanted', 'Roommate Wanted')], max_length=20),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='works_from_home',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='wants_furnished',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='lifestyleprofile',
            name='wants_building_amenities',
            field=models.BooleanField(),
        ),
    ]
