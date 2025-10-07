from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.contrib.gis.geoip2 import GeoIP2
from django.core.cache import cache
from ip_tracking.models import RequestLog, BlockedIP

class IPTrackingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)

        # Block if IP is blacklisted
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Access denied: Your IP has been blocked.")

        # Get cached geolocation
        geo_data = cache.get(ip)
        if not geo_data:
            try:
                geo = GeoIP2()
                location = geo.city(ip)
                geo_data = {
                    'country': location.get('country_name', 'Unknown'),
                    'city': location.get('city', 'Unknown'),
                }
                cache.set(ip, geo_data, 60 * 60 * 24)  # cache for 24h
            except Exception:
                geo_data = {'country': 'Unknown', 'city': 'Unknown'}

        # Log request
        RequestLog.objects.create(
            ip_address=ip,
            path=request.path,
            timestamp=timezone.now(),
            country=geo_data['country'],
            city=geo_data['city']
        )

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
