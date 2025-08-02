from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import *
import os
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from application.models import ApplicationMember


def project_supervisor(request):
    projects = Project.objects.filter(supervisor=request.user)
    context = {
        'projects':projects
    }
    return render(request, 'projects/project_supervisor.html',context)


def validate_pdf(file):
    """Validate that the uploaded file is a PDF and within size limits."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError('Only PDF files are allowed.')
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        raise ValidationError(f'File size exceeds {max_size//(1024*1024)}MB limit')

@require_http_methods(["GET", "POST"])
def add_project(request):
    if request.method == 'POST':
        try:
            required_fields = {
                'project_title': 'Title is required',
                'project_type': 'Project type is required',
                'prerequisites': 'Prerequisites are required',
                'description': 'Description is required'
            }
            
            for field, error_msg in required_fields.items():
                if not request.POST.get(field):
                    raise ValidationError(error_msg)

            project = Project.objects.create(
                title=request.POST['project_title'],
                project_type=request.POST['project_type'],
                prerequisites=request.POST['prerequisites'],
                description=request.POST['description'],
                supervisor=request.user,
                availability='available'
            )

            areas = set()
            for area in request.POST.getlist('project_areas[]'):
                if area and area not in areas:
                    ProjectArea.objects.create(project=project, name=area)
                    areas.add(area)

            uploaded_files = request.FILES.getlist('uploaded_files')
            
            custom_names_map = {}
            for i in range(len(uploaded_files)):
                custom_name_key = f'custom_file_name_{i}'
                original_file_name_key = f'original_file_name_{i}'
                
                original_name_from_frontend = request.POST.get(original_file_name_key)
                custom_name = request.POST.get(custom_name_key)
                
                if original_name_from_frontend:
                    custom_names_map[original_name_from_frontend] = custom_name
                else:
                    custom_names_map[uploaded_files[i].name] = custom_name 


            for file in uploaded_files:
                try:
                    validate_pdf(file)
                    
                    custom_display_name = custom_names_map.get(file.name) 
                    
                    if custom_display_name:
                        display_name_to_use = custom_display_name.strip()
                        if not display_name_to_use:
                            display_name_to_use = os.path.splitext(file.name)[0]
                    else:
                        display_name_to_use = os.path.splitext(file.name)[0]

                    display_name_to_use = display_name_to_use[:255]

                    ProjectFile.objects.create(
                        project=project,
                        file=file,
                        display_name=display_name_to_use
                    )
                except ValidationError as e:
                    print(f"Skipped invalid file: {file.name} - {str(e)}")
                    continue

            links = set()
            for url in request.POST.getlist('project_links[]'):
                clean_url = url.strip().lower()
                if clean_url and clean_url not in links:
                    ProjectLink.objects.create(project=project, url=clean_url)
                    links.add(clean_url)

            return redirect('project_supervisor')

        except ValidationError as e:
            return render(request, 'projects/add_project.html', {'error': str(e)})
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return render(request, 'projects/add_project.html', 
                          {'error': 'An unexpected error occurred. Please try again.'})

    return render(request, 'projects/add_project.html')



@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    has_applied = ApplicationMember.objects.filter(
        user=request.user,
        application__status__in=["applied", "accepted"]
    ).exists()

    return render(request, "projects/project_details.html", {
        "project": project,
        "has_applied": has_applied,
    })


def student_projects(request):
    projects = Project.objects.all()
    context = {
        'projects' : projects,
    }
    return render(request,'projects/student_projects.html', context)