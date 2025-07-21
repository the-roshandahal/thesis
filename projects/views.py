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

import os
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .models import Project, ProjectArea, ProjectFile, ProjectLink

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
            # Validate required fields (same as before)
            required_fields = {
                'project_title': 'Title is required',
                'project_type': 'Project type is required',
                'prerequisites': 'Prerequisites are required',
                'description': 'Description is required'
            }
            
            for field, error_msg in required_fields.items():
                if not request.POST.get(field):
                    raise ValidationError(error_msg)

            # Create project (same as before)
            project = Project.objects.create(
                title=request.POST['project_title'],
                project_type=request.POST['project_type'],
                prerequisites=request.POST['prerequisites'],
                description=request.POST['description'],
                supervisor=request.user,
                availability='available'
            )

            # Process topic areas (same as before)
            areas = set()
            for area in request.POST.getlist('project_areas[]'):
                if area and area not in areas:
                    ProjectArea.objects.create(project=project, name=area)
                    areas.add(area)

            # Process files with custom names
            uploaded_files = request.FILES.getlist('uploaded_files')
            
            # Create a dictionary to map original filenames (or indices) to custom names
            custom_names_map = {}
            for i in range(len(uploaded_files)):
                custom_name_key = f'custom_file_name_{i}'
                original_file_name_key = f'original_file_name_{i}'
                
                original_name_from_frontend = request.POST.get(original_file_name_key)
                custom_name = request.POST.get(custom_name_key)
                
                if original_name_from_frontend:
                    # Use the original filename as the key if provided, otherwise the index
                    # This helps in case files get reordered on the frontend
                    custom_names_map[original_name_from_frontend] = custom_name
                # Fallback to index if original_file_name isn't reliable or available
                else:
                    custom_names_map[uploaded_files[i].name] = custom_name # This assumes files maintain order


            for file in uploaded_files:
                try:
                    validate_pdf(file)
                    
                    # Determine the display name
                    # Prioritize the custom name if available, otherwise use original filename without extension
                    custom_display_name = custom_names_map.get(file.name) # Try to get by original file name
                    
                    if custom_display_name:
                        # Ensure the custom name isn't empty or just whitespace
                        display_name_to_use = custom_display_name.strip()
                        if not display_name_to_use: # If custom name is empty after strip, fallback
                            display_name_to_use = os.path.splitext(file.name)[0]
                    else:
                        display_name_to_use = os.path.splitext(file.name)[0]

                    # Truncate to max_length of your CharField
                    display_name_to_use = display_name_to_use[:255]

                    ProjectFile.objects.create(
                        project=project,
                        file=file,
                        display_name=display_name_to_use
                    )
                except ValidationError as e:
                    print(f"Skipped invalid file: {file.name} - {str(e)}")
                    continue

            # Process links (same as before)
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


def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, 'projects/project_details.html', {'project': project})