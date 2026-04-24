# Sistema SST — Centro Minero SENA

Sistema integral de Seguridad y Salud en el Trabajo para el Centro Minero SENA Sogamoso, desarrollado con Django, Django REST Framework y Django Channels.

## Características principales

- **Control de acceso:** Registro de ingresos y egresos con geocercas (algoritmo Haversine)
- **Gestión de emergencias:** Alertas masivas, botón de pánico, emergencias naturales autorizadas
- **Brigada de emergencia:** Panel de disponibilidad en tiempo real, gestión de miembros
- **Notificaciones en tiempo real:** WebSockets vía Django Channels + Redis
- **Mapas interactivos:** Edificios, puntos de encuentro y equipamiento de seguridad (Leaflet.js)
- **Dashboards por rol:** Vistas específicas para 7 roles del sistema
- **Reportes:** Exportación en PDF (ReportLab) y Excel (openpyxl)
- **API REST completa:** Documentada con Swagger / ReDoc (drf-spectacular)
- **Auditoría y seguridad:** django-auditlog, django-axes, Sentry SDK, rate limiting

## Roles del sistema

| Rol | Descripción |
|-----|-------------|
| `ADMIN` | Administrador del sistema |
| `COORDINADOR_SST` | Coordinador de Seguridad y Salud en el Trabajo |
| `BRIGADA` | Miembro de la brigada de emergencia |
| `INSTRUCTOR` | Instructor SENA |
| `APRENDIZ` | Aprendiz SENA |
| `VIGILANCIA` | Personal de vigilancia |
| `VISITANTE` | Visitante externo |

## Tecnologías

| Capa | Tecnología |
|------|------------|
| Backend | Django 4.2.7, Django REST Framework 3.14 |
| Tiempo real | Django Channels 4, Daphne (ASGI), Redis |
| Frontend | Bootstrap 5, JavaScript ES6+, Leaflet.js, Chart.js |
| Base de datos | SQLite (desarrollo) / PostgreSQL (producción) |
| Servidor | Nginx + Daphne vía Docker Compose |
| Seguridad | django-axes, django-ratelimit, Sentry SDK |
| Auditoría | django-auditlog |
| Reportes | ReportLab, openpyxl, pandas |
| API docs | drf-spectacular (Swagger / ReDoc) |
| Scheduler | django-apscheduler |

## Estructura del proyecto

```
proyecto_final_sst/
├── sst_proyecto/              # Código fuente Django
│   ├── sst_proyecto/          # Configuración principal (settings, urls, routing)
│   ├── usuarios/              # Usuarios, roles, notificaciones, push
│   ├── control_acceso/        # Ingresos/egresos, geocercas, señales
│   ├── emergencias/           # Emergencias, brigada, alertas masivas
│   ├── mapas/                 # Edificios, puntos de encuentro, equipamiento
│   ├── reportes/              # Reportes, incidentes SST
│   ├── templates/             # Plantillas HTML por rol/sección
│   ├── static/                # CSS, JS, íconos, vendors (Bootstrap, Leaflet…)
│   ├── manage.py
│   └── db.sqlite3             # Base de datos local (desarrollo)
├── nginx/                     # Configuración Nginx
├── Dockerfile
├── docker-compose.yml         # Producción
├── docker-compose.dev.yml     # Desarrollo con Docker
├── requirements.txt           # Dependencias producción
├── requirements-dev.txt       # Dependencias desarrollo
└── .env                       # Variables de entorno (no versionado)
```

## Requisitos previos

- Python 3.10 o superior
- pip
- Redis (para WebSockets y caché) — o usar Docker Compose
- Git

## Instalación local (sin Docker)

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd proyecto_final_sst
```

### 2. Crear y activar entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
# Para desarrollo (pytest, ruff, etc.)
pip install -r requirements-dev.txt
```

### 4. Configurar variables de entorno

Crear el archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=<clave-secreta-django>
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (opcional, por defecto SQLite)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sst_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Redis (para WebSockets)
REDIS_URL=redis://localhost:6379/0

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=correo@dominio.com
EMAIL_HOST_PASSWORD=contraseña
```

**Generar SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Aplicar migraciones

```bash
cd sst_proyecto
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Iniciar el servidor

```bash
python manage.py runserver
```

El sistema estará disponible en: `http://localhost:8000`

La documentación de la API estará en: `http://localhost:8000/api/schema/swagger-ui/`

---

## Despliegue con Docker

### Desarrollo

```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Producción

```bash
docker-compose up --build -d
```

El stack levanta: **Daphne** (ASGI) + **Nginx** (proxy inverso + archivos estáticos) + **Redis**.

---

## API REST

La documentación interactiva está disponible en:

- **Swagger UI:** `/api/schema/swagger-ui/`
- **ReDoc:** `/api/schema/redoc/`

### Endpoints principales

```
POST   /api/auth/usuarios/login/              Login — obtener token
GET    /api/auth/usuarios/perfil/             Perfil del usuario autenticado

GET    /api/acceso/registros/                 Registros de acceso
POST   /api/acceso/registros/                 Registrar ingreso/egreso

GET    /api/emergencias/emergencias/          Listar emergencias
POST   /api/emergencias/emergencias/          Crear emergencia / activar alerta
GET    /api/emergencias/brigada/              Estado de la brigada
POST   /api/emergencias/brigada/mi-disponibilidad/  Actualizar disponibilidad

GET    /api/mapas/api/edificios/              Edificios del campus
GET    /api/mapas/api/equipamientos/          Equipamiento de seguridad
GET    /api/mapas/api/puntos-encuentro/       Puntos de encuentro

GET    /api/reportes/dashboard/               Métricas del dashboard
```

---

## Seguridad en producción

Antes de desplegar a producción verificar:

1. `SECRET_KEY` — clave única y secreta
2. `DEBUG = False`
3. `ALLOWED_HOSTS` — solo dominios autorizados
4. `CORS_ALLOWED_ORIGINS` — limitar orígenes permitidos
5. Base de datos PostgreSQL configurada
6. HTTPS / SSL activo
7. Redis con autenticación
8. Variables sensibles fuera del repositorio (`.env` en `.gitignore`)

---

## Testing

```bash
cd sst_proyecto

# Ejecutar todas las pruebas con pytest
pytest

# Ejecutar pruebas de Django estándar
python manage.py test
```

---

## Solución de problemas comunes

**`SECRET_KEY required`** — Verifica que el archivo `.env` existe y contiene `SECRET_KEY`.

**`No module named 'decouple'`** — Ejecuta `pip install -r requirements.txt`.

**Error de migraciones** — Ejecuta `python manage.py migrate --run-syncdb`.

**Puerto 8000 en uso** — Cambia el puerto: `python manage.py runserver 8001`.

**WebSockets no funcionan** — Verifica que Redis esté corriendo (`redis-cli ping`).

---

## Contacto

- **Institución:** Centro Minero SENA — Sogamoso, Boyacá, Colombia
- **Proyecto:** Sistema SST — Seguridad y Salud en el Trabajo

---

*Desarrollado para el Centro Minero SENA*
