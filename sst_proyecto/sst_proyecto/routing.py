"""
URL patterns para conexiones WebSocket del proyecto SST.
Incluido desde asgi.py dentro de AuthMiddlewareStack.
"""

from django.urls import re_path

from usuarios import consumers

websocket_urlpatterns = [
    re_path(r"^ws/notificaciones/$", consumers.NotificacionConsumer.as_asgi()),
]
