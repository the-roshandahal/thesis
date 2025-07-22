from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import Application, ApplicationMember
from projects.models import Project
from django.contrib.auth import get_user_model
from defaults.models import Notification



from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

User = get_user_model()

@login_required
def apply_to_project(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    applicant = request.user

    def has_active_application(user):
        return ApplicationMember.objects.filter(
            user=user,
            application__status__in=['applied', 'accepted']
        ).exists()

    if request.method == "POST":
        application_type = request.POST.get('application_type')
        message = request.POST.get('message', '').strip()

        if application_type not in ['individual', 'group']:
            messages.error(request, "Please select a valid application type.")
            return render(request, "application/apply_to_project.html", {'project': project})

        # Check if applicant already has active application
        if has_active_application(applicant):
            messages.error(request, "You already have an active or accepted application.")
            return render(request, "application/apply_to_project.html", {'project': project})

        if application_type == 'individual':
            # Create application
            application = Application.objects.create(
                project=project,
                application_type='individual',
                status='applied',
                message=message,
            )
            # Add applicant as leader and member
            ApplicationMember.objects.create(application=application, user=applicant, is_leader=True)
            messages.success(request, "Your individual application has been submitted.")

            # Notify supervisor
            Notification.objects.create(
                user=project.supervisor,
                message=f"{applicant.get_full_name()} applied to your project '{project.title}'.",
                url=reverse('project_detail', args=[project.id])
            )

        else:  # group application
            group_emails_raw = request.POST.get('group_emails', '')
            if not group_emails_raw.strip():
                messages.error(request, "Please enter emails of group members for group application.")
                return render(request, "application/apply_to_project.html", {'project': project})

            group_emails = [email.strip().lower() for email in group_emails_raw.split(',') if email.strip()]
            if applicant.email.lower() not in group_emails:
                group_emails.append(applicant.email.lower())

            users = list(User.objects.filter(email__in=group_emails))
            found_emails = {user.email.lower() for user in users}
            missing_emails = [email for email in group_emails if email not in found_emails]

            if missing_emails:
                messages.error(request,
                    "These emails are not registered students: " + ", ".join(missing_emails) +
                    ". Please fix and apply again."
                )
                return render(request, "application/apply_to_project.html", {'project': project})

            # Check if any user has active application
            for user in users:
                if has_active_application(user):
                    messages.error(request, f"Student {user.email} already has an active or accepted application.")
                    return render(request, "application/apply_to_project.html", {'project': project})

            application = Application.objects.create(
                project=project,
                application_type='group',
                status='applied',
                message=message,
            )
            # Add members to ApplicationMember with leader flag for applicant
            for user in users:
                ApplicationMember.objects.create(
                    application=application,
                    user=user,
                    is_leader=(user == applicant)
                )

            messages.success(request, "Group application submitted successfully.")

            # Notify supervisor
            Notification.objects.create(
                user=project.supervisor,
                message=f"{applicant.get_full_name()} applied to your project '{project.title}' as a group.",
                url=reverse('project_detail', args=[project.id])
            )

            # Notify group members except leader
            for user in users:
                if user != applicant:
                    Notification.objects.create(
                        user=user,
                        message=f"You were added by {applicant.get_full_name()} to apply for the project '{project.title}'.",
                        url=reverse('project_detail', args=[project.id])
                    )

        return redirect('project_detail', project_id=project.id)

    # GET request
    return render(request, "application/apply_to_project.html", {'project': project})


def supervisor_application(request):
    user = request.user
    applications = Application.objects.filter(project__supervisor=user).select_related('project').prefetch_related('members__user')
    return render (request,'application/supervisor_application.html',{'applications': applications})


@login_required
def accept_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, project__supervisor=request.user)
    if application.status != 'accepted':
        application.status = 'accepted'
        application.save()
        messages.success(request, "Application accepted.")
    return redirect('supervisor_application')


@login_required
def decline_application(request, application_id):
    application = get_object_or_404(Application, id=application_id, project__supervisor=request.user)
    if application.status != 'declined':
        application.status = 'declined'
        application.save()
        messages.success(request, "Application declined.")
    return redirect('supervisor_application')
