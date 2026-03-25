"""
WebSocket consumer para notificaciones en tiempo real.

Cada usuario autenticado se une a dos grupos:
  - notif_user_{id}  → mensajes personales
  - notif_rol_{rol}  → mensajes a todo un rol (ej. BRIGADA, ADMINISTRATIVO)

El frontend se conecta a /ws/notificaciones/ y recibe eventos JSON
del tipo { tipo, titulo, mensaje, prioridad, url } cuando
NotificacionService crea una notificación.
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class NotificacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_group = f"notif_user_{user.id}"
        self.rol_group = f"notif_rol_{user.rol}"

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.rol_group, self.channel_name)
        await self.accept()

        logger.debug("WS conectado: user=%s grupos=[%s, %s]", user.username, self.user_group, self.rol_group)

    async def disconnect(self, close_code):
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if hasattr(self, "rol_group"):
            await self.channel_layer.group_discard(self.rol_group, self.channel_name)

    # El cliente no envía mensajes; ignoramos cualquier texto recibido.
    async def receive(self, text_data=None, bytes_data=None):
        pass

    # ------------------------------------------------------------------ #
    # Manejadores de eventos enviados desde el channel layer              #
    # ------------------------------------------------------------------ #

    async def notification(self, event):
        """
        Recibe un evento del channel layer (enviado por NotificacionService)
        y lo reenvía al WebSocket del navegador.
        """
        await self.send(text_data=json.dumps(event["data"]))
