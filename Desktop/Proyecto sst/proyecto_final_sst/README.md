# 🏗️ Sistema SST - Centro Minero SENA

Sistema integral de Seguridad y Salud en el Trabajo para el Centro Minero SENA Sogamoso, desarrollado con Django y Django REST Framework.

## 📋 Características Principales

- **Control de Acceso:** Registro automático de ingresos y egresos con geocercas
- **Gestión de Emergencias:** Sistema de alertas y botón de pánico con geolocalización
- **Mapas Interactivos:** Puntos de encuentro, equipamiento de seguridad y edificios
- **Reportes y Estadísticas:** Dashboards con métricas de aforo, emergencias y asistencia
- **API REST:** Endpoints completos para integración con aplicaciones móviles
- **Autenticación por Token:** Sistema seguro de autenticación y autorización

## 🛠️ Tecnologías Utilizadas

- **Backend:** Django 4.2.7, Django REST Framework
- **Base de Datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend:** Bootstrap 5, JavaScript ES6+
- **Seguridad:** Token Authentication, CORS configurado, validadores de datos

## 📦 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Git (opcional)

## 🚀 Instalación

### 1. Clonar el repositorio (o descargar el ZIP)

```bash
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
```

### 4. Configurar variables de entorno

Copiar el archivo `.env.example` a `.env`:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Editar el archivo `.env` y configurar las variables necesarias (especialmente `SECRET_KEY`).

**Generar SECRET_KEY segura:**
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Aplicar migraciones

```bash
cd sst_proyecto
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Recolectar archivos estáticos (producción)

```bash
python manage.py collectstatic
```

### 8. Ejecutar el servidor

```bash
python manage.py runserver
```

El sistema estará disponible en: `http://localhost:8000`

## 📱 Estructura del Proyecto

```
sst_proyecto/
├── sst_proyecto/          # Configuración principal
│   ├── settings.py        # Configuración de Django
│   ├── urls.py           # URLs principales
│   └── wsgi.py           # WSGI para producción
├── usuarios/             # Gestión de usuarios y visitantes
├── control_acceso/       # Registro de ingresos/egresos
├── emergencias/          # Sistema de emergencias
├── mapas/               # Mapas y ubicaciones
├── reportes/            # Generación de reportes
├── templates/           # Templates HTML
├── static/              # Archivos estáticos (CSS, JS)
├── media/              # Archivos subidos por usuarios
├── requirements.txt    # Dependencias Python
├── .env               # Variables de entorno
└── README.md          # Este archivo
```

## 🔐 Seguridad

### Configuración Crítica

⚠️ **IMPORTANTE:** Antes de desplegar a producción:

1. **Cambiar SECRET_KEY:** Generar una nueva clave secreta
2. **DEBUG = False:** Desactivar modo debug
3. **ALLOWED_HOSTS:** Configurar dominios permitidos
4. **CORS:** Limitar orígenes permitidos
5. **Base de Datos:** Migrar a PostgreSQL
6. **HTTPS:** Configurar certificados SSL/TLS

### Variables de Entorno Requeridas

```env
SECRET_KEY=<tu-clave-secreta-aqui>
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
CORS_ALLOWED_ORIGINS=https://tudominio.com
```

## 📡 API REST

La documentación completa de la API está disponible en:

- **Archivo:** `API_DOCUMENTATION.md`
- **URL Base:** `http://localhost:8000/api/`
- **Autenticación:** Token-based

### Endpoints Principales

- `/api/auth/usuarios/login/` - Login y obtención de token
- `/api/acceso/registros/` - Registros de acceso
- `/api/emergencias/emergencias/` - Gestión de emergencias
- `/api/mapas/puntos-encuentro/` - Puntos de encuentro
- `/api/reportes/dashboard/` - Dashboard principal

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
python manage.py test

# Ejecutar pruebas de una app específica
python manage.py test usuarios
```

## 📊 Modelos de Datos

### Principales Entidades

- **Usuario:** Sistema de usuarios con roles (ADMIN, INSTRUCTOR, APRENDIZ, etc.)
- **RegistroAcceso:** Control de ingresos y egresos con geolocalización
- **Emergencia:** Gestión de emergencias y alertas
- **PuntoEncuentro:** Puntos de evacuación en caso de emergencia
- **EquipamientoSeguridad:** Equipamiento de seguridad (extintores, botiquines, etc.)

## 🌍 Configuración de Geocercas

El sistema utiliza geocercas circulares para delimitar el área del Centro Minero:

- **Centro:** Latitud 5.5339, Longitud -73.3674
- **Radio:** Configurable en el modelo `Geocerca`
- **Algoritmo:** Fórmula de Haversine para cálculo de distancias

## 🤝 Contribución

Este proyecto fue desarrollado para el Centro Minero SENA Sogamoso.

## 📝 Changelog

### Versión 1.0.0 (2025)

- ✅ Sistema de autenticación y autorización
- ✅ Control de acceso con geocercas
- ✅ Gestión de emergencias con botón de pánico
- ✅ Mapas interactivos
- ✅ Sistema de reportes
- ✅ API REST completa
- ✅ Validadores de datos mejorados
- ✅ Índices de base de datos optimizados
- ✅ Seguridad reforzada

## 🐛 Solución de Problemas

### Error: "SECRET_KEY required"

Asegúrate de tener el archivo `.env` configurado con la variable `SECRET_KEY`.

### Error: "No module named 'decouple'"

Instala las dependencias: `pip install -r requirements.txt`

### Error de migraciones

```bash
python manage.py migrate --run-syncdb
```

### Puerto 8000 en uso

```bash
# Cambiar puerto
python manage.py runserver 8001
```

## 📧 Contacto y Soporte

- **Centro:** Centro Minero SENA Sogamoso
- **Ubicación:** Sogamoso, Boyacá, Colombia

## 📜 Licencia

Este proyecto es de uso interno del SENA Centro Minero.

---

**Desarrollado con ❤️ para el Centro Minero SENA**
