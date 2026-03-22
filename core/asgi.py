# core/asgi.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')  # ✅ MUST be before everything

import django
django.setup()  # ✅ ADD THIS

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import social.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            social.routing.websocket_urlpatterns
        )
    ),
})