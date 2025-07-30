from django.shortcuts import render
from assessment.models import *
from application.models import *

# Create your views here.
def grading(request):
    user=request.user
    print(user)
    applicationsss = Application.objects.all()
    for appl in applicationsss:

        print(appl.project)
    return render (request, 'grading/grading.html' )