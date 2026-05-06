# core_multitienda/context_processors.py
from django.conf import settings

def google_analytics(request):
    return {
        "GOOGLE_ANALYTICS_ID": getattr(settings, "GOOGLE_ANALYTICS_ID", None)
    }
