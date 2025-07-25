# Generated by Django 5.0.2 on 2025-07-21 06:11

import datetime
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0007_alter_project_last_modified'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projectfile',
            options={'ordering': ['-uploaded_at']},
        ),
        migrations.AddField(
            model_name='projectfile',
            name='display_name',
            field=models.CharField(default='dsads', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projectfile',
            name='uploaded_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='project',
            name='last_modified',
            field=models.DateTimeField(default=datetime.datetime(2025, 7, 21, 6, 10, 48, 268784, tzinfo=datetime.timezone.utc)),
        ),
        migrations.AlterField(
            model_name='projectfile',
            name='file',
            field=models.FileField(upload_to='project_files/%Y/%m/%d/'),
        ),
    ]
