# Generated by Django 5.0.2 on 2025-07-23 02:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0003_assessment_submission_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='submission_type',
            field=models.CharField(max_length=50),
        ),
    ]
