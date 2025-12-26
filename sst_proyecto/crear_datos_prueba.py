"""
Script para crear datos de prueba en la base de datos
Ejecutar: python crear_datos_prueba.py
"""
import os
import django
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from usuarios.models import Usuario, Visitante
from control_acceso.models import RegistroAcceso, ConfiguracionAforo

def crear_datos_prueba():
    """Crea datos de prueba para el dashboard"""

    print("=" * 70)
    print("CREANDO DATOS DE PRUEBA PARA EL DASHBOARD")
    print("=" * 70)
    print()

    # 1. Configurar aforo
    print("1. Configurando aforo...")
    ConfiguracionAforo.objects.all().delete()
    aforo = ConfiguracionAforo.objects.create(
        aforo_maximo=2000,
        aforo_minimo=1800,
        mensaje_alerta='Se esta alcanzando el aforo maximo del centro',
        activo=True
    )
    print(f"   Aforo maximo configurado: {aforo.aforo_maximo} personas")
    print()

    # 2. Crear algunos registros de acceso para HOY
    print("2. Creando registros de acceso para HOY...")
    RegistroAcceso.objects.all().delete()

    usuarios = Usuario.objects.filter(activo=True)[:4]
    hoy = timezone.now()

    registros_creados = 0

    # Crear algunos ingresos
    for i, usuario in enumerate(usuarios):
        # Ingreso de esta mañana (aún en el centro)
        RegistroAcceso.objects.create(
            usuario=usuario,
            tipo='INGRESO',
            fecha_hora_ingreso=hoy - timedelta(hours=3+i),
            latitud_ingreso=5.5339,
            longitud_ingreso=-73.3674,
            metodo_ingreso='QR'
        )
        registros_creados += 1

    # Crear algunos ingresos y egresos completos
    for i, usuario in enumerate(usuarios[:2]):
        registro = RegistroAcceso.objects.create(
            usuario=usuario,
            tipo='INGRESO',
            fecha_hora_ingreso=hoy - timedelta(hours=8),
            latitud_ingreso=5.5339,
            longitud_ingreso=-73.3674,
            metodo_ingreso='AUTOMATICO'
        )
        # Agregar egreso
        registro.fecha_hora_egreso = hoy - timedelta(hours=2)
        registro.latitud_egreso = 5.5339
        registro.longitud_egreso = -73.3674
        registro.metodo_egreso = 'AUTOMATICO'
        registro.save()
        registros_creados += 1

    print(f"   Registros de acceso creados: {registros_creados}")
    print()

    # 3. Crear registros de días anteriores (para gráfica)
    print("3. Creando registros de días anteriores (para gráfica)...")

    for dias_atras in range(1, 8):
        fecha = hoy - timedelta(days=dias_atras)
        cantidad = 2 + dias_atras  # Aumenta gradualmente

        for usuario in usuarios[:cantidad]:
            RegistroAcceso.objects.create(
                usuario=usuario,
                tipo='INGRESO',
                fecha_hora_ingreso=fecha,
                latitud_ingreso=5.5339,
                longitud_ingreso=-73.3674,
                metodo_ingreso='QR'
            )

    print(f"   Registros históricos creados para los últimos 7 días")
    print()

    # 4. Crear algunos visitantes para HOY
    print("4. Creando visitantes para HOY...")
    Visitante.objects.all().delete()

    visitantes_data = [
        {
            'nombre_completo': 'Carlos Ramirez',
            'tipo_documento': 'CC',
            'numero_documento': '1234567890',
            'telefono': '3101234567',
            'entidad': 'Empresa ABC',
            'motivo_visita': 'Reunion con instructor'
        },
        {
            'nombre_completo': 'Maria Lopez',
            'tipo_documento': 'CC',
            'numero_documento': '9876543210',
            'telefono': '3109876543',
            'entidad': 'Universidad XYZ',
            'motivo_visita': 'Entrevista de trabajo'
        },
        {
            'nombre_completo': 'Juan Perez',
            'tipo_documento': 'CE',
            'numero_documento': '5555555555',
            'telefono': '3155555555',
            'entidad': 'Proveedora LTDA',
            'motivo_visita': 'Entrega de equipos'
        }
    ]

    admin_user = Usuario.objects.filter(rol='ADMINISTRATIVO').first()
    instructor = Usuario.objects.filter(rol='INSTRUCTOR').first() or admin_user

    for data in visitantes_data:
        Visitante.objects.create(
            **data,
            persona_a_visitar=instructor,
            registrado_por=admin_user
        )

    print(f"   Visitantes creados: {len(visitantes_data)}")
    print()

    # 5. Mostrar resumen
    print("=" * 70)
    print("RESUMEN DE DATOS CREADOS")
    print("=" * 70)
    print()

    total_usuarios = Usuario.objects.filter(activo=True).count()
    ingresos_hoy = RegistroAcceso.objects.filter(
        tipo='INGRESO',
        fecha_hora_ingreso__date=hoy.date()
    ).count()
    personas_en_centro = RegistroAcceso.objects.filter(
        tipo='INGRESO',
        fecha_hora_egreso__isnull=True,
        fecha_hora_ingreso__date=hoy.date()
    ).count()
    visitantes_hoy = Visitante.objects.filter(fecha_visita=hoy.date()).count()

    print(f"Total de usuarios registrados: {total_usuarios}")
    print(f"Ingresos hoy: {ingresos_hoy}")
    print(f"Personas en centro ahora: {personas_en_centro}")
    print(f"Visitantes hoy: {visitantes_hoy}")
    print(f"Aforo maximo: {aforo.aforo_maximo}")
    print(f"% Ocupacion: {round((personas_en_centro/aforo.aforo_maximo)*100, 1)}%")
    print()

    print("=" * 70)
    print("DATOS DE PRUEBA CREADOS EXITOSAMENTE")
    print("=" * 70)
    print()
    print("Ahora puedes:")
    print("1. Refrescar el dashboard en el navegador (F5)")
    print("2. Ver los datos reales en las tarjetas")
    print("3. Probar con diferentes roles de usuario")
    print()

if __name__ == '__main__':
    crear_datos_prueba()
