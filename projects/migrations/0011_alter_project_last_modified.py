# Generated by Django 5.0.2 on 2025-07-21 07:52

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0010_alter_project_last_modified_projectapplication'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2025, 7, 21, 7, 52, 18, 219068, tzinfo=datetime.timezone.utc)),
        ),
    ]
