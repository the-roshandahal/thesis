from django.shortcuts import render, get_object_or_404
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .models import *

def project_supervisor(request):
    projects = Project.objects.all()
    context = {
        'projects':projects
    }
    return render(request, 'projects/project_supervisor.html',context)

@require_http_methods(["GET", "POST"])
def add_project(request):
    if request.method == 'POST':
        title = request.POST.get('project_title')
        project_type = request.POST.get('project_type')
        prerequisites = request.POST.get('prerequisites')
        description = request.POST.get('description')

        # Create the main project
        project = Project.objects.create(
            title=title,
            project_type=project_type,
            prerequisites=prerequisites,
            description=description,
            supervisor=request.user,
            availability='available'
        )

        areas = request.POST.getlist('project_areas[]')
        print("Areas received:", areas)


        for f in request.FILES.getlist('uploaded_files[]'):
            ProjectFile.objects.create(project=project, file=f)


        for url in request.POST.getlist('project_links[]'):
            if url.strip():
                ProjectLink.objects.create(project=project, url=url)

        areas = set()
        for area in request.POST.getlist('project_areas[]'):
            clean_area = area.strip()
            if clean_area and clean_area.lower() not in areas:
                ProjectArea.objects.create(project=project, name=clean_area)
                areas.add(clean_area.lower())


        return redirect('project_supervisor')  # Update as needed

    return render(request, 'projects/add_project.html')


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, 'projects/project_details.html', {'project': project})