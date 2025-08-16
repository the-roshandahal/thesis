from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from .models import *
import os
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from application.models import ApplicationMember
from accounts.decorators import supervisor_required


def project_supervisor(request):
    projects = Project.objects.filter(supervisor=request.user)
    context = {
        'projects': projects,
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    return render(request, 'projects/project_supervisor.html', context)


def validate_pdf(file):
    """Validate that the uploaded file is a PDF and within size limits."""
    ext = os.path.splitext(file.name)[1].lower()
    if ext != '.pdf':
        raise ValidationError('Only PDF files are allowed.')
    
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        raise ValidationError(f'File size exceeds {max_size//(1024*1024)}MB limit')

@login_required
@require_http_methods(["GET", "POST"])
@supervisor_required
def add_project(request):
    print(f"DEBUG: add_project called by user: {request.user.email}")
    print(f"DEBUG: Request method: {request.method}")
    
    if request.method == 'POST':
        print(f"DEBUG: POST data received: {request.POST}")
        print(f"DEBUG: Files received: {request.FILES}")
        
        try:
            required_fields = {
                'project_title': 'Title is required',
                'project_type': 'Project type is required',
                'prerequisites': 'Prerequisites are required',
                'description': 'Description is required'
            }
            
            for field, error_msg in required_fields.items():
                field_value = request.POST.get(field)
                print(f"DEBUG: Field '{field}': '{field_value}'")
                if not field_value:
                    print(f"DEBUG: Missing required field: {field}")
                    raise ValidationError(error_msg)

            project = Project.objects.create(
                title=request.POST['project_title'],
                project_type=request.POST['project_type'],
                prerequisites=request.POST['prerequisites'],
                description=request.POST['description'],
                supervisor=request.user,
                availability='available'
            )
            print(f"DEBUG: Project created successfully with ID: {project.id}")
            print(f"DEBUG: Project title: {project.title}")
            print(f"DEBUG: Project supervisor: {project.supervisor.email}")
            print(f"DEBUG: Project availability field: {project.availability}")
            print(f"DEBUG: Project is_available property: {project.is_available_for_application}")
            
            # Force update availability status to ensure it's correct
            project.update_availability_status()
            print(f"DEBUG: After update_availability_status - availability: {project.availability}")
            print(f"DEBUG: After update_availability_status - is_available: {project.is_available_for_application}")
            
            # Double-check and force availability if needed
            if project.availability != 'available':
                print(f"DEBUG: Forcing availability to 'available' for new project")
                project.availability = 'available'
                project.save()
                print(f"DEBUG: Final availability after force: {project.availability}")
                print(f"DEBUG: Final is_available after force: {project.is_available_for_application}")

            areas = set()
            for area in request.POST.getlist('project_areas[]'):
                if area and area not in areas:
                    ProjectArea.objects.create(project=project, name=area)
                    areas.add(area)

            # Handle sample file
            sample_file = request.FILES.get('sample_file')
            if sample_file:
                try:
                    validate_pdf(sample_file)
                    ProjectFile.objects.create(
                        project=project,
                        file=sample_file,
                        display_name="Sample File"
                    )
                    print(f"DEBUG: Sample file created: {sample_file.name}")
                except ValidationError as e:
                    print(f"DEBUG: Sample file validation failed: {str(e)}")

            # Handle assessment file
            assessment_file = request.FILES.get('assessment_file')
            if assessment_file:
                try:
                    validate_pdf(assessment_file)
                    ProjectFile.objects.create(
                        project=project,
                        file=assessment_file,
                        display_name="Assessment Details"
                    )
                    print(f"DEBUG: Assessment file created: {assessment_file.name}")
                except ValidationError as e:
                    print(f"DEBUG: Assessment file validation failed: {str(e)}")

            # Handle links
            links = set()
            for url in request.POST.getlist('project_links[]'):
                clean_url = url.strip().lower()
                if clean_url and clean_url not in links:
                    ProjectLink.objects.create(project=project, url=clean_url)
                    links.add(clean_url)

            return redirect('project_supervisor')

        except ValidationError as e:
            return render(request, 'projects/add_project.html', {
                'error': str(e),
                'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                'user_is_admin': request.user.is_superuser,
            })
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return render(request, 'projects/add_project.html', {
                'error': 'An unexpected error occurred. Please try again.',
                'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                'user_is_admin': request.user.is_superuser,
            })

    return render(request, 'projects/add_project.html', {
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    })



@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Get detailed application information for the current user FOR THIS SPECIFIC PROJECT
    user_application = None
    has_applied = False
    application_status = None
    
    # Check if user has ANY active application to ANY project
    has_active_application_anywhere = False
    
    if not request.user.is_superuser and not request.user.is_staff:
        # Only check for students
        user_application = ApplicationMember.objects.filter(
            user=request.user,
            application__project=project,  # Check for THIS specific project
            application__status__in=["applied", "accepted"]
        ).select_related('application').first()
        
        if user_application:
            has_applied = True
            application_status = user_application.application.status
        
        # Check if user has ANY ACCEPTED application to ANY project
        has_accepted_application_anywhere = False
        
        if not request.user.is_superuser and not request.user.is_staff:
            # Only check for students
            user_application = ApplicationMember.objects.filter(
                user=request.user,
                application__project=project,  # Check for THIS specific project
                application__status__in=["applied", "accepted"]
            ).select_related('application').first()
            
            if user_application:
                has_applied = True
                application_status = user_application.application.status
            
            # Check if user has ANY ACCEPTED application to ANY project
            # Users can still apply to multiple projects while waiting for decisions
            has_accepted_application_anywhere = ApplicationMember.objects.filter(
                user=request.user,
                application__status='accepted'  # Only check for accepted applications
            ).exists()
            
            print(f"DEBUG: User {request.user.email} - has_accepted_application_anywhere: {has_accepted_application_anywhere}")

    # Check if project is available for new applications
    is_available = project.is_available_for_application

    # Choose template based on user type
    if request.user.is_superuser or request.user.is_staff:
        template_name = "projects/project_details.html"
    else:
        template_name = "projects/student_project_detail.html"

    return render(request, template_name, {
        "project": project,
        "has_applied": has_applied,
        "user_application": user_application,
        "application_status": application_status,
        "is_available": is_available,
        "has_accepted_application_anywhere": has_accepted_application_anywhere,
        "user_is_supervisor": request.user.is_staff and not request.user.is_superuser,
        "user_is_admin": request.user.is_superuser,
    })


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check if the current user is the supervisor of this project
    if project.supervisor != request.user:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('project_supervisor')
    
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

            # Update project fields
            project.title = request.POST['project_title']
            project.project_type = request.POST['project_type']
            project.prerequisites = request.POST['prerequisites']
            project.description = request.POST['description']
            project.save()

            # Update project areas
            # First, remove existing areas
            project.areas.all().delete()
            
            # Add new areas
            areas = set()
            for area in request.POST.getlist('project_areas[]'):
                if area and area not in areas:
                    ProjectArea.objects.create(project=project, name=area)
                    areas.add(area)

            # Handle file uploads
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

            # Update project links
            # First, remove existing links
            project.links.all().delete()
            
            # Add new links
            links = set()
            for url in request.POST.getlist('project_links[]'):
                clean_url = url.strip().lower()
                if clean_url and clean_url not in links:
                    ProjectLink.objects.create(project=project, url=clean_url)
                    links.add(clean_url)

            messages.success(request, 'Project updated successfully!')
            return redirect('project_supervisor')

        except ValidationError as e:
            return render(request, 'projects/edit_project.html', {
                'project': project,
                'error': str(e),
                'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                'user_is_admin': request.user.is_superuser,
            })
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return render(request, 'projects/edit_project.html', {
                'project': project,
                'error': 'An unexpected error occurred. Please try again.',
                'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                'user_is_admin': request.user.is_superuser,
            })

    return render(request, 'projects/edit_project.html', {
        'project': project,
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    })


@login_required
def delete_file(request, file_id):
    """Delete a project file"""
    file = get_object_or_404(ProjectFile, id=file_id)
    
    # Check if the current user is the supervisor of this project
    if file.project.supervisor != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        file.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def student_projects(request):
    # Get search and filter parameters
    query = request.GET.get('q')
    topic_type = request.GET.get('topic_type')
    availability_filter = request.GET.get('availability', 'all')
    
    print(f"DEBUG: student_projects - Query: {query}, Topic Type: {topic_type}, Availability: {availability_filter}")
    
    # Get all projects initially
    projects = Project.objects.all()
    print(f"DEBUG: Total projects found: {projects.count()}")
    
    # Check if current user has any accepted application to any project
    has_accepted_application_anywhere = False
    if not request.user.is_superuser and not request.user.is_staff:
        # Only prevent applications if user has an ACCEPTED application
        # Users can still apply to multiple projects while waiting for decisions
        has_accepted_application_anywhere = ApplicationMember.objects.filter(
            user=request.user,
            application__status='accepted'  # Only check for accepted applications
        ).exists()
        print(f"DEBUG: student_projects - User {request.user.email} has accepted application anywhere: {has_accepted_application_anywhere}")
    
    # Apply availability filter if specified
    if availability_filter == 'available':
        # Show only projects that are available for new applications
        projects = [p for p in projects if p.is_available_for_application]
        print(f"DEBUG: After 'available' filter: {len(projects)} projects")
    elif availability_filter == 'taken':
        # Show only projects that have accepted applications (are taken)
        projects = [p for p in projects if not p.is_available_for_application]
        print(f"DEBUG: After 'taken' filter: {len(projects)} projects")
    # If 'all' or no filter, show all projects
    
    # Apply search filter if specified
    if query:
        query_lower = query.lower()
        projects = [p for p in projects if 
                   query_lower in p.title.lower() or 
                   query_lower in p.description.lower()]
        print(f"DEBUG: After search filter: {len(projects)} projects")
    
    # Apply topic type filter if specified
    if topic_type:
        projects = [p for p in projects if p.project_type.lower() == topic_type.lower()]
        print(f"DEBUG: After topic type filter: {len(projects)} projects")
    
    # Add availability information to each project
    for project in projects:
        project.is_available = project.is_available_for_application
        print(f"DEBUG: student_projects - Project '{project.title}' - is_available: {project.is_available}")
    
    # Calculate counts for filter summary
    total_projects = len(projects)
    available_count = len([p for p in projects if p.is_available])
    taken_count = len([p for p in projects if not p.is_available])
    
    context = {
        'projects': projects,
        'query': query,
        'selected_topic_type': topic_type,
        'selected_availability': availability_filter,
        'total_projects': total_projects,
        'available_count': available_count,
        'taken_count': taken_count,
        'has_accepted_application_anywhere': has_accepted_application_anywhere,
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    }
    
    print(f"DEBUG: Final context - Total: {total_projects}, Available: {available_count}, Taken: {taken_count}")
    
    return render(request, 'projects/student_projects.html', context)