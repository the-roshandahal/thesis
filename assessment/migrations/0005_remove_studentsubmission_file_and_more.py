# Generated by Django 5.0.2 on 2025-07-25 06:44

import assessment.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0004_alter_assessment_submission_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentsubmission',
            name='file',
        ),
        migrations.AddField(
            model_name='studentsubmission',
            name='submitted_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='SubmissionFIle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=assessment.models.student_submission_upload_path)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assessment.studentsubmission')),
            ],
        ),
    ]
