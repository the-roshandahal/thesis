from .models import Notification

def notifications(request):
    if request.user.is_authenticated:
        # Fetch unread notifications
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        unread_notifications = notifications.filter(is_read=False)
        return {
            'unread_notifications': unread_notifications,
        }
    return {}
