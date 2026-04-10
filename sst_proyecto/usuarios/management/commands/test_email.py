"""
Comando de diagnóstico para probar el envío de emails.
Uso: python manage.py test_email <correo_destino>
"""

import smtplib
import socket
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings


class Command(BaseCommand):
    help = "Prueba el envío de email y muestra errores detallados"

    def add_arguments(self, parser):
        parser.add_argument("destino", type=str, help="Correo de destino (ej: tu@outlook.com)")

    def handle(self, *args, **options):
        destino = options["destino"]

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write("DIAGNÓSTICO DE EMAIL")
        self.stdout.write(f"{'=' * 60}\n")

        # Mostrar configuración actual
        self.stdout.write(self.style.HTTP_INFO("Configuración actual:"))
        self.stdout.write(f"  EMAIL_BACKEND  : {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  EMAIL_HOST     : {getattr(settings, 'EMAIL_HOST', 'N/A')}")
        self.stdout.write(f"  EMAIL_PORT     : {getattr(settings, 'EMAIL_PORT', 'N/A')}")
        self.stdout.write(f"  EMAIL_USE_TLS  : {getattr(settings, 'EMAIL_USE_TLS', 'N/A')}")
        self.stdout.write(f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'N/A')}")
        self.stdout.write(f"  DEFAULT_FROM   : {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"  EMAIL_TIMEOUT  : {getattr(settings, 'EMAIL_TIMEOUT', 'N/A')}s")
        self.stdout.write(f"  Destino        : {destino}\n")

        # Verificar si hay credenciales
        host_user = getattr(settings, "EMAIL_HOST_USER", "")
        host_pass = getattr(settings, "EMAIL_HOST_PASSWORD", "")

        if not host_user or not host_pass:
            self.stdout.write(
                self.style.ERROR(
                    "ERROR: EMAIL_HOST_USER o EMAIL_HOST_PASSWORD están vacíos en .env\n"
                    "El sistema usa el backend de CONSOLA — los emails solo aparecen en terminal."
                )
            )
            return

        # Probar conectividad SMTP
        host = getattr(settings, "EMAIL_HOST", "smtp.gmail.com")
        port = getattr(settings, "EMAIL_PORT", 587)
        self.stdout.write(self.style.HTTP_INFO(f"Probando conectividad con {host}:{port}..."))
        try:
            sock = socket.create_connection((host, port), timeout=10)
            sock.close()
            self.stdout.write(self.style.SUCCESS(f"  Conexion TCP a {host}:{port} - OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  No se puede conectar a {host}:{port}: {e}"))
            return

        # Probar autenticación SMTP
        self.stdout.write(self.style.HTTP_INFO("Probando autenticacion SMTP..."))
        try:
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(host_user, host_pass)
            server.quit()
            self.stdout.write(self.style.SUCCESS(f"  Autenticacion como {host_user} - OK"))
        except smtplib.SMTPAuthenticationError as e:
            self.stdout.write(
                self.style.ERROR(
                    f"  Error de autenticacion: {e}\n"
                    "  Verifica que EMAIL_HOST_PASSWORD sea una 'Contrasena de aplicacion' de Google,\n"
                    "  no tu contrasena normal de Gmail."
                )
            )
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error SMTP: {e}"))
            return

        # Enviar email de prueba
        self.stdout.write(self.style.HTTP_INFO(f"\nEnviando email de prueba a {destino}..."))
        try:
            msg = EmailMessage(
                subject="[SST] Prueba de notificacion de emergencia",
                body=(
                    "<html><body style='font-family:Arial,sans-serif; padding:20px;'>"
                    "<h2 style='color:#DC2626;'>Email de prueba recibido correctamente</h2>"
                    "<p>Este correo confirma que el sistema de notificaciones de emergencias "
                    "del Centro Minero SENA esta configurado correctamente.</p>"
                    "<p>Si ves este mensaje, las alertas de emergencia llegaran a tu correo.</p>"
                    "<hr><small style='color:#666;'>Sistema SST - Centro Minero SENA</small>"
                    "</body></html>"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[destino],
            )
            msg.content_subtype = "html"
            msg.send(fail_silently=False)
            self.stdout.write(
                self.style.SUCCESS(f"\nOK - Email enviado a {destino}\n   Revisa inbox Y carpeta de spam/no deseado.")
            )
        except smtplib.SMTPRecipientsRefused as e:
            self.stdout.write(
                self.style.ERROR(
                    f"\nERROR - El servidor rechazo el destinatario {destino}: {e}\n"
                    "   Gmail puede bloquear envios a ciertos dominios desde cuentas gratuitas."
                )
            )
        except smtplib.SMTPDataError as e:
            self.stdout.write(self.style.ERROR(f"\nERROR al enviar datos: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nERROR inesperado: {type(e).__name__}: {e}"))

        self.stdout.write(f"\n{'=' * 60}\n")
