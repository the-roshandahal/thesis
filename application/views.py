from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Application, ApplicationMember
from projects.models import Project
from django.contrib.auth import get_user_model
from defaults.models import Notification

User = get_user_model()

@login_required
def apply_to_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    applicant = request.user
    
    print(f"DEBUG: apply_to_project called for project '{project.title}' by user '{applicant.email}'")
    print(f"DEBUG: Request method: {request.method}")

    def has_accepted_application(user):
        # Only prevent applications if user has an ACCEPTED application
        # Users can still apply to multiple projects while waiting for decisions
        accepted_apps = ApplicationMember.objects.filter(
            user=user,
            application__status='accepted'  # Only check for accepted applications
        )
        print(f"DEBUG: User {user.email} has {accepted_apps.count()} accepted applications")
        return accepted_apps.exists()

    if request.method == "POST":
        print(f"DEBUG: Processing POST request")
        print(f"DEBUG: POST data: {request.POST}")
        
        application_type = request.POST.get('application_type')
        message = request.POST.get('message', '').strip()
        
        print(f"DEBUG: Application type: {application_type}")
        print(f"DEBUG: Message: {message}")

        if application_type not in ['individual', 'group']:
            print(f"DEBUG: Invalid application type: {application_type}")
            messages.error(request, "Please select a valid application type.")
            return render(request, "application/apply_to_project.html", {
                'project': project,
                'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                'user_is_admin': request.user.is_superuser,
            })

        # Check if applicant already has accepted application
        if has_accepted_application(applicant):
            print(f"DEBUG: User {applicant.email} already has accepted application")
            messages.error(request, "You already have an accepted application to another project.")
            return render(request, "application/apply_to_project.html", {
                'project': project,
                'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                'user_is_admin': request.user.is_superuser,
            })

        try:
            if application_type == 'individual':
                print(f"DEBUG: Creating individual application")
                # Create application
                application = Application.objects.create(
                    project=project,
                    application_type='individual',
                    status='applied',
                    message=message,
                )
                print(f"DEBUG: Application created with ID: {application.id}")
                
                # Add applicant as leader and member
                ApplicationMember.objects.create(application=application, user=applicant, is_leader=True)
                print(f"DEBUG: ApplicationMember created for user {applicant.email}")
                
                messages.success(request, "Your individual application has been submitted.")

                # Notify supervisor
                Notification.objects.create(
                    user=project.supervisor,
                    message=f"{applicant.get_full_name()} applied to your project '{project.title}'.",
                    url=reverse('project_detail', args=[project.id])
                )
                print(f"DEBUG: Notification created for supervisor {project.supervisor.email}")

            else:  # group application
                print(f"DEBUG: Processing group application")
                group_emails_raw = request.POST.get('group_emails', '')
                if not group_emails_raw.strip():
                    print(f"DEBUG: No group emails provided")
                    messages.error(request, "Please enter emails of group members for group application.")
                    return render(request, "application/apply_to_project.html", {
                        'project': project,
                        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                        'user_is_admin': request.user.is_superuser,
                    })

                group_emails = [email.strip().lower() for email in group_emails_raw.split(',') if email.strip()]
                if applicant.email.lower() not in group_emails:
                    group_emails.append(applicant.email.lower())
                
                print(f"DEBUG: Group emails: {group_emails}")

                users = list(User.objects.filter(email__in=group_emails))
                found_emails = {user.email.lower() for user in users}
                missing_emails = [email for email in group_emails if email not in found_emails]

                if missing_emails:
                    print(f"DEBUG: Missing emails: {missing_emails}")
                    messages.error(request,
                        "These emails are not registered students: " + ", ".join(missing_emails) +
                        ". Please fix and apply again."
                    )
                    return render(request, "application/apply_to_project.html", {
                        'project': project,
                        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                        'user_is_admin': request.user.is_superuser,
                    })

                # Check if any user has accepted application
                for user in users:
                    if has_accepted_application(user):
                        print(f"DEBUG: User {user.email} already has accepted application")
                        messages.error(request, f"Student {user.email} already has an accepted application to another project.")
                        return render(request, "application/apply_to_project.html", {
                            'project': project,
                            'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                            'user_is_admin': request.user.is_superuser,
                        })

                print(f"DEBUG: Creating group application")
                application = Application.objects.create(
                    project=project,
                    application_type='group',
                    status='applied',
                    message=message,
                )
                print(f"DEBUG: Group application created with ID: {application.id}")
                
                # Add members to ApplicationMember with leader flag for applicant
                for user in users:
                    ApplicationMember.objects.create(
                        application=application,
                        user=user,
                        is_leader=(user == applicant)
                    )
                    print(f"DEBUG: ApplicationMember created for user {user.email}, is_leader: {user == applicant}")

                messages.success(request, "Group application submitted successfully.")

                # Notify supervisor
                Notification.objects.create(
                    user=project.supervisor,
                    message=f"{applicant.get_full_name()} applied to your project '{project.title}' as a group.",
                    url=reverse('project_detail', args=[project.id])
                )
                print(f"DEBUG: Notification created for supervisor {project.supervisor.email}")

                # Notify group members except leader
                for user in users:
                    if user != applicant:
                        Notification.objects.create(
                            user=user,
                            message=f"You were added by {applicant.get_full_name()} to apply for the project '{project.title}'.",
                            url=reverse('project_detail', args=[project.id])
                        )
                        print(f"DEBUG: Notification created for group member {user.email}")

            print(f"DEBUG: Application submitted successfully, redirecting to project detail")
            return redirect('project_detail', project_id=project.id)
            
        except Exception as e:
            print(f"DEBUG: Error creating application: {str(e)}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            messages.error(request, f"An error occurred while submitting your application: {str(e)}")
            return render(request, "application/apply_to_project.html", {
                'project': project,
                'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
                'user_is_admin': request.user.is_superuser,
            })

    # GET request
    print(f"DEBUG: Rendering application form")
    return render(request, "application/apply_to_project.html", {
        'project': project,
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    })


def supervisor_application(request):
    user = request.user
    print(f"DEBUG: supervisor_application called for user: {user.email}")
    print(f"DEBUG: User is_staff: {user.is_staff}, is_superuser: {user.is_superuser}")
    
    # Get all projects for this supervisor
    supervisor_projects = Project.objects.filter(supervisor=user)
    print(f"DEBUG: Supervisor has {supervisor_projects.count()} projects")
    
    # Get applications for supervisor's projects
    applications = Application.objects.filter(project__supervisor=user).select_related('project').prefetch_related('members__user')
    print(f"DEBUG: Found {applications.count()} applications for supervisor's projects")
    
    for app in applications:
        print(f"DEBUG: Application {app.id}: Project '{app.project.title}', Status: {app.status}, Members: {app.members.count()}")
    
    return render(request, 'application/supervisor_application.html', {
        'applications': applications,
        'user_is_supervisor': request.user.is_staff and not request.user.is_superuser,
        'user_is_admin': request.user.is_superuser,
    })


@login_required
@require_http_methods(["POST"])
def accept_application(request, application_id):
    print(f"DEBUG: accept_application called for application_id: {application_id}")
    print(f"DEBUG: Current user: {request.user.email}, is_staff: {request.user.is_staff}, is_superuser: {request.user.is_superuser}")
    
    application = get_object_or_404(Application, id=application_id, project__supervisor=request.user)
    print(f"DEBUG: Found application: {application.id}, status: {application.status}, project: {application.project.title}")
    
    if application.status != 'accepted':
        print(f"DEBUG: Updating application status from '{application.status}' to 'accepted'")
        application.status = 'accepted'
        application.save()
        
        # Update project availability status
        project = application.project
        print(f"DEBUG: Updating project availability for: {project.title}")
        print(f"DEBUG: Project availability before: {project.availability}")
        project.update_availability_status()
        print(f"DEBUG: Project availability after: {project.availability}")
        
        messages.success(request, "Application accepted.")

        for member in application.members.all():
            Notification.objects.create(
                user=member.user,  # Send notification to each member of the application
                message=f"Your application to the project '{application.project.title}' has been accepted.",
                url=reverse('project_detail', args=[application.project.id])  # Redirect to project detail page
            )
            print(f"DEBUG: Created notification for user: {member.user.email}")
    else:
        print(f"DEBUG: Application {application_id} is already accepted, no changes made")
    
    return redirect('supervisor_application')


@login_required
@require_http_methods(["POST"])
def decline_application(request, application_id):
    print(f"DEBUG: decline_application called for application_id: {application_id}")
    print(f"DEBUG: Current user: {request.user.email}, is_staff: {request.user.is_staff}, is_superuser: {request.user.is_superuser}")
    
    application = get_object_or_404(Application, id=application_id, project__supervisor=request.user)
    print(f"DEBUG: Found application: {application.id}, status: {application.status}, project: {application.project.title}")
    
    if application.status != 'declined':
        print(f"DEBUG: Updating application status from '{application.status}' to 'declined'")
        application.status = 'declined'
        application.save()
        
        # Update project availability status (might become available again if no other accepted applications)
        project = application.project
        print(f"DEBUG: Updating project availability for: {project.title}")
        print(f"DEBUG: Project availability before: {project.availability}")
        project.update_availability_status()
        print(f"DEBUG: Project availability after: {project.availability}")
        
        messages.success(request, "Application declined.")
    else:
        print(f"DEBUG: Application {application_id} is already declined, no changes made")
    
    return redirect('supervisor_application')
