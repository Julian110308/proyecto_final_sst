"""
Script para configurar inicialmente el módulo de control de acceso
Ejecutar con: python manage.py shell < configurar_control_acceso.py
"""

from control_acceso.models import ConfiguracionAforo, Geocerca

# Crear configuración de aforo si no existe
if not ConfiguracionAforo.objects.exists():
    ConfiguracionAforo.objects.create(
        aforo_maximo=2000,
        aforo_minimo=1800,
        mensaje_alerta='Se está alcanzando el aforo máximo del centro',
        activo=True
    )
    print("✅ Configuración de aforo creada: Máximo 2000 personas")
else:
    print("✅ Configuración de aforo ya existe")

# Crear geocerca del centro minero si no existe
if not Geocerca.objects.exists():
    Geocerca.objects.create(
        nombre='Centro Minero SENA',
        descripcion='Perímetro virtual del Centro Minero SENA',
        centro_latitud=5.5339,
        centro_longitud=-73.3674,
        radio_metros=200,
        activo=True
    )
    print("✅ Geocerca creada: Centro Minero SENA (radio 200m)")
else:
    print("✅ Geocerca ya existe")

print("\n🎉 Configuración completada. El módulo de control de acceso está listo para usar.")
