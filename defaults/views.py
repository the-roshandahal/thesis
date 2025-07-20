from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import *
from django.contrib.auth.models import User
from projects.models import *


from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def home(request):

    if request.user.is_superuser:
        return render(request, 'admin_dashboard.html')

    elif request.user.is_staff:
        return render(request, 'supervisor_dashboard.html')

    else:
        projects = Project.objects.all()
        context = {
            'projects' : projects,
        }
        return render(request, 'student_dashboard.html', context)

def homepage(request):
    query = request.GET.get('q')
    topic_type = request.GET.get('topic_type')

    projects = Project.objects.all()

    if query:
        projects = projects.filter(title__icontains=query)  # or any field you want to search in

    if topic_type:
        projects = projects.filter(project_type__iexact=topic_type)

    context = {
        'projects': projects,
        'query': query,
        'selected_topic_type': topic_type,
    }
    return render(request, 'index.html', context)
