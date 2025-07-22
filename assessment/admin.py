from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(AssessmentSchema)
admin.site.register(Assessment)
admin.site.register(AssessmentDetailFile)
admin.site.register(AssessmentSampleFile)