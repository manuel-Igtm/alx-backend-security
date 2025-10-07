from django.http import HttpResponseForbidden
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from .models import RequestLog, BlockedIP

class IPTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)

        # Block if IP is blacklisted
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Access denied: Your IP has been blocked.")

        # Otherwise, log the request
        RequestLog.objects.create(
            ip_address=ip,
            path=request.path,
            timestamp=timezone.now()
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
