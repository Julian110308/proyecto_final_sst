# Plan de Trabajo - Proyecto SST SENA
*Actualizado: Marzo 2026*

---

## Historial Completado (Fases 1–6 — Febrero 2026)

El sistema funcional fue completado en su totalidad. A continuación el resumen:

| Módulo | Estado |
|--------|--------|
| Autenticación y roles (7 roles) | ✅ Completo |
| Control de acceso + geovallas | ✅ Completo |
| Sistema de emergencias + botón pánico | ✅ Completo |
| Mapas, edificios, equipamiento | ✅ Completo |
| Notificaciones in-app + Web Push | ✅ Completo |
| Reportes PDF / Excel / CSV + Celery | ✅ Completo |
| Dashboards por rol con tiempo real (AJAX) | ✅ Completo |
| PWA (Service Worker + manifest) | ✅ Completo |

---

## Nueva Hoja de Ruta: Madurez y Robustez del Sistema

El objetivo de esta etapa es llevar el proyecto de "funcionando en desarrollo" a "confiable en producción".
Las fases están ordenadas por impacto y riesgo real.

---

## FASE 1: Seguridad Inmediata
**Prioridad: CRÍTICA | Riesgo activo hoy**

### 1.1 Mover claves VAPID al entorno ✅ COMPLETADO
- [x] Mover `vapid_private.pem` y `vapid_public.pem` fuera del código fuente
- [x] Agregar claves como variables de entorno en `.env`
- [x] Actualizar `settings.py` para leerlas con `python-decouple`
- [x] Agregar `*.pem` al `.gitignore`
- [x] Documentar variables VAPID en `.env.example`

**Archivos afectados:**
- `sst_proyecto/settings.py`
- `.env` / `.env.example`
- `.gitignore`

### 1.2 Rate Limiting en endpoints críticos ✅ COMPLETADO
- [x] Instalar `django-ratelimit` y `django-axes` (agregados a requirements.txt)
- [x] Aplicar límite en `POST /api/auth/login/` → máx. 10 intentos/minuto por IP
- [x] Aplicar límite en login HTML → máx. 10 intentos/minuto por IP
- [x] Aplicar límite en `POST /api/emergencias/boton_panico/` → máx. 3/hora por usuario
- [x] Configurar bloqueo de IP tras 5 intentos fallidos (django-axes)
- [x] Cooldown de 15 minutos tras bloqueo

**Archivos afectados:**
- `usuarios/views.py`
- `emergencias/views.py`
- `sst_proyecto/settings.py`

### 1.3 Permisos a nivel de objeto ✅ COMPLETADO
- [x] Verificar que un usuario solo pueda ver/editar sus propios registros de acceso
- [x] Verificar que un aprendiz no pueda leer notificaciones de otro usuario
- [x] Agregar `get_queryset()` filtrado por `request.user` donde falte

**Archivos afectados:**
- `control_acceso/views.py`
- `usuarios/views.py`
- `reportes/views.py`

---

## FASE 2: Suite de Tests ✅ COMPLETADO (135/135 tests — 75% cobertura)
**Prioridad: ALTA | Riesgo: cualquier cambio puede romper producción sin saberlo**

### 2.1 Configurar entorno de testing ✅ COMPLETADO
- [x] Instalar `pytest-django`, `factory_boy`, `coverage`, `faker`
- [x] Crear `pytest.ini`
- [x] Crear `conftest.py` con fixtures base (usuarios por rol, tokens, clientes sesión y API)
- [x] Crear factories para los modelos principales

**Archivos creados:**
- `pytest.ini`
- `conftest.py`
- `.coveragerc`
- `usuarios/tests/factories.py`
- `emergencias/tests/factories.py`

### 2.2 Tests críticos — Permisos por rol ✅ COMPLETADO
- [x] Test: APRENDIZ no puede crear emergencia
- [x] Test: VISITANTE no puede acceder a dashboards internos
- [x] Test: Solo BRIGADA/ADMIN puede resolver emergencia
- [x] Test: COORDINADOR_SST puede ver todos los reportes
- [x] Test: Token inválido devuelve 401
- [x] Test: IDOR — APRENDIZ no puede ver perfil ajeno

**Archivos creados:**
- `usuarios/tests/test_permissions.py`

### 2.3 Tests críticos — Flujos de negocio ✅ COMPLETADO
- [x] Test: Flujo completo botón pánico → notificación a brigada
- [x] Test: Registro de acceso fuera de geovalla → rechazado
- [x] Test: Cálculo Haversine con coordenadas conocidas
- [x] Test: Aforo al umbral ADVERTENCIA → notificación automática
- [x] Test: Generación de reporte PDF sin error (smoke test)
- [x] Test: Marcar notificación como leída
- [x] Test: Crear/listar incidentes con permisos y filtros
- [x] Test: Login HTML (cuenta pendiente, bloqueada, inactiva)
- [x] Test: Dashboards HTML por rol
- [x] Test: Acciones Coordinador SST (aprobar/rechazar cuentas, brigada)
- [x] Test: NotificacionService (emergencia atendida/resuelta, incidente crítico, aforo crítico)

**Archivos creados:**
- `emergencias/tests/test_panico.py`
- `emergencias/tests/test_emergencias.py`
- `control_acceso/tests/test_geovalla.py`
- `control_acceso/tests/test_registros.py`
- `reportes/tests/test_generacion.py`
- `reportes/tests/test_incidentes.py`
- `usuarios/tests/test_notificaciones.py`
- `usuarios/tests/test_auth.py`
- `usuarios/tests/test_login_view.py`
- `usuarios/tests/test_dashboard_views.py`

### 2.4 Meta de cobertura ✅ COMPLETADO
- [x] Alcanzar 70% de cobertura en `usuarios/`, `emergencias/`, `control_acceso/`
  - `control_acceso`: 75% ✅
  - `emergencias`: 80% ✅
  - `usuarios`: 70%+ ✅
  - **Total: 75%**
- [x] Reporte de cobertura con `coverage html` → generado en `htmlcov/`

---

## FASE 3: CI/CD con GitHub Actions ✅ COMPLETADO
**Prioridad: ALTA | Impacto: calidad continua automática**

### 3.1 Lint y formateo ✅ COMPLETADO
- [x] Instalar `ruff` (reemplaza flake8 + isort, mucho más rápido)
- [x] Crear `sst_proyecto/ruff.toml` con configuración adaptada al proyecto
- [x] Corregir 88 errores de lint existentes (F401, F841, F541, F821)
- [x] 0 errores tras corrección (`ruff check .` → All checks passed)

**Archivos creados/modificados:**
- `sst_proyecto/ruff.toml`
- `requirements-dev.txt` (dependencias solo de desarrollo/testing)

### 3.2 Pipeline de CI ✅ COMPLETADO
- [x] Crear `.github/workflows/ci.yml`
- [x] Job 1 — Lint: ruff check sobre todo el proyecto
- [x] Job 2 — Tests: pytest + cobertura mínima 70% + reporte XML
- [x] Job 3 — Auditoría: pip-audit sobre requirements.txt
- [x] Verificación de migraciones pendientes antes de tests
- [x] Ejecutar en push a main/develop y en Pull Requests a main

**Archivos creados:**
- `.github/workflows/ci.yml`

### 3.3 Pre-commit hooks ✅ COMPLETADO
- [x] Instalar `pre-commit` + `detect-secrets`
- [x] Configurar hooks: ruff (lint + format), trailing whitespace, end-of-file, merge conflicts, archivos grandes, secretos
- [x] Crear `.pre-commit-config.yaml`
- [x] Generar `.secrets.baseline` con estado inicial del proyecto
- [x] Ejecutar en todos los archivos → 0 errores

---

## FASE 4: Containerización con Docker
**Prioridad: ALTA | Impacto: deploy reproducible y sin errores de entorno**

### 4.1 Dockerizar la aplicación ✅ COMPLETADO
- [x] Crear `Dockerfile` para el servicio web (Python 3.12 slim + Gunicorn)
- [x] Crear `docker-compose.yml` con servicios:
  - `web` → Django + Gunicorn
  - `db` → PostgreSQL 15
  - `redis` → para Celery + Channels
  - `celery` → worker de tareas
  - `nginx` → proxy reverso (producción)
- [x] Crear `docker-compose.dev.yml` simplificado (solo db + redis para desarrollo local)
- [x] Agregar `.dockerignore`
- [x] Crear `nginx/nginx.conf` con proxy reverso y caché de estáticos

**Archivos creados:**
- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `.dockerignore`
- `entrypoint.sh`
- `nginx/nginx.conf`

### 4.2 Configuración de producción ✅ COMPLETADO
- [x] Actualizar `.env.example` con todas las variables del proyecto (DB, email, VAPID, Redis, Sentry)
- [x] Separación base/dev/production omitida — settings.py ya usa decouple con if not DEBUG, suficiente por ahora

---

## FASE 5: Monitoreo y Auditoría
**Prioridad: MEDIA | Impacto: visibilidad de errores y trazabilidad legal**

### 5.1 Monitoreo de errores con Sentry ✅ COMPLETADO
- [x] Instalar `sentry-sdk`
- [x] Configurar en `settings.py` con DSN desde variable de entorno (solo activa si SENTRY_DSN está en .env)
- [x] Ambiente automático: development/production según DEBUG
- [x] No envía datos sensibles (send_default_pii=False)

**Pendiente del usuario:** crear cuenta en sentry.io y pegar el DSN en `.env`

### 5.2 Auditoría de cambios en modelos críticos ✅ COMPLETADO
- [x] Instalar `django-auditlog`
- [x] Registrar modelos: `Emergencia`, `BrigadaEmergencia`, `RegistroAcceso`, `ConfiguracionAforo`, `Geocerca`, `Usuario`, `Incidente`
- [x] Usuario excluye `last_login` y `password` (no aportan trazabilidad)
- [x] Panel de auditoría en Django Admin (solo lectura, solo superuser puede borrar)
- [x] 135/135 tests pasando tras los cambios

### 5.3 Logging de seguridad mejorado ✅ YA IMPLEMENTADO (Fase 1)
- Intentos de login fallidos → `logs/seguridad.log`
- Login exitoso → `logs/auditoria.log`
- Cuentas bloqueadas por axes → log de seguridad

---

## FASE 6: Caché y Rendimiento
**Prioridad: MEDIA | Impacto: velocidad en hora pico**

### 6.1 Activar caché con Redis ✅ COMPLETADO
- [x] Configurar `django.core.cache` con backend Redis en `settings.py`
- [x] Cachear `aforo_actual` con TTL de 30 segundos
- [x] Cachear estadísticas de dashboard con TTL de 5 minutos
- [x] Cachear `TipoEmergencia` (catálogo estático) con TTL de 1 hora
- [x] Invalidar caché via señal `post_save` en `RegistroAcceso`
- [x] Tests usan `LocMemCache` automáticamente (sin Redis real)

### 6.2 Optimización de queries N+1 ✅ COMPLETADO
- [x] `EmergenciaViewSet` → `select_related("tipo", "reportada_por", "edificio")` + `prefetch_related("atendida_por")`
- [x] `RegistroAccesoViewSet` → `select_related("usuario")`

### 6.3 Índices de base de datos ✅ COMPLETADO
- [x] Índice compuesto `RegistroAcceso(usuario, fecha_hora_ingreso)` — ya tenía índices individuales
- [x] Índice compuesto `Emergencia(estado, fecha_hora_reporte)` — nuevo
- [x] `Notificacion(destinatario, leida)` y `(destinatario, fecha_creacion)` — ya existían

---

## FASE 7: Notificaciones en Tiempo Real (WebSocket) ✅ COMPLETADO
**Prioridad: MEDIA | Impacto: UX en emergencias — de 30s de delay a instantáneo**

### 7.1 Implementar WebSocket consumer ✅ COMPLETADO
- [x] Crear `usuarios/consumers.py` — `NotificacionConsumer`
- [x] Grupos por usuario: `notif_user_{id}` y por rol: `notif_rol_{ROL}`
- [x] Autenticación via sesión (cierra con 4001 si no autenticado)
- [x] Actualizar `asgi.py` con ProtocolTypeRouter HTTP + WebSocket
- [x] `AllowedHostsOriginValidator` + `AuthMiddlewareStack` para seguridad WS

**Archivos creados/modificados:**
- `usuarios/consumers.py`
- `sst_proyecto/asgi.py`
- `sst_proyecto/routing.py`
- `sst_proyecto/settings.py` → `channels` en INSTALLED_APPS + `CHANNEL_LAYERS`

### 7.2 Integrar con el servicio de notificaciones ✅ COMPLETADO
- [x] Helpers `_ws_dispatch_roles` y `_ws_dispatch_usuario` en `services.py`
- [x] Dispatch en `notificar_emergencia_creada` → BRIGADA, ADMINISTRATIVO, VIGILANCIA
- [x] Dispatch en `notificar_incidente_critico` → ADMINISTRATIVO, INSTRUCTOR
- [x] Dispatch en `notificar_aforo_critico` → VIGILANCIA, ADMINISTRATIVO
- [x] Reemplazar polling 30s por WebSocket en `base.html` con fallback automático
- [x] Toast flotante para notificaciones ALTA/EMERGENCIA recibidas por WS
- [x] Reconexión automática con backoff exponencial (2s → 30s)
- [x] Tests usan `InMemoryChannelLayer` (sin Redis real) — 135/135 pasando

**Archivos afectados:**
- `usuarios/services.py`
- `templates/base.html`
- `conftest.py` → override `CHANNEL_LAYERS` para tests

---

## FASE 8: Madurez de API ✅ COMPLETADO
**Prioridad: BAJA | Impacto: mantenibilidad y escalabilidad futura**

### 8.1 Documentación automática con Swagger ✅ COMPLETADO
- [x] Instalar `drf-spectacular==0.29.0`
- [x] Configurar `SPECTACULAR_SETTINGS` en settings.py (título, descripción, tags, solo staff)
- [x] `DEFAULT_SCHEMA_CLASS` → `drf_spectacular.openapi.AutoSchema`
- [x] `@extend_schema` en: `boton_panico`, `atender`, `resolver` (emergencias); `login`, `logout`, `perfil` (usuarios); `auto_registro`, `aforo_actual` (control_acceso)
- [x] `/api/schema/` (YAML), `/api/schema/swagger/` (Swagger UI), `/api/schema/redoc/` — solo staff

**Archivos modificados:**
- `sst_proyecto/settings.py` → SPECTACULAR_SETTINGS + DEFAULT_SCHEMA_CLASS
- `emergencias/views.py`, `usuarios/views.py`, `control_acceso/views.py` → decoradores

### 8.2 Versionado de API ✅ COMPLETADO
- [x] Rutas `/api/v1/auth/`, `/api/v1/acceso/`, `/api/v1/mapas/`, `/api/v1/emergencias/` (canónicas)
- [x] Rutas `/api/` mantenidas como alias (backwards compatibility — templates sin cambios)

### 8.3 Manejo global de errores ✅ COMPLETADO
- [x] `handler404` y `handler500` en urls.py → `sst_proyecto.error_views`
- [x] JSON para peticiones API, HTML para navegador (detección automática por path/headers)
- [x] Templates `errors/404.html` y `errors/500.html` con diseño SENA
- [x] DRF `sst_exception_handler`: respuestas uniformes `{error, detail, status}` + log de advertencia

**Archivos creados:**
- `sst_proyecto/error_views.py`
- `sst_proyecto/exception_handler.py`
- `templates/errors/404.html`
- `templates/errors/500.html`

---

## Cronograma

| Fase | Descripción | Estado | Prioridad |
|------|-------------|--------|-----------|
| **1** | Seguridad inmediata | ✅ Completado | CRÍTICA |
| **2** | Suite de tests | ✅ Completado (135 tests, 75% cobertura) | ALTA |
| **3** | CI/CD GitHub Actions | ✅ Completado (lint + tests + audit + pre-commit) | ALTA |
| **4** | Docker + deploy | ✅ Completado | ALTA |
| **5** | Sentry + Auditoría | ✅ Completado | MEDIA |
| **6** | Caché + rendimiento | ✅ Completado | MEDIA |
| **7** | WebSocket real | ✅ Completado (WS + toast + fallback polling) | MEDIA |
| **8** | Madurez de API | ✅ Completado (Swagger + v1 + error handlers) | BAJA |

---

## Dependencias a instalar por fase

```bash
# Fase 1
pip install django-ratelimit django-axes

# Fase 2
pip install pytest-django factory_boy coverage faker

# Fase 3
pip install ruff mypy django-stubs pre-commit pip-audit

# Fase 4
# Docker Desktop (no pip)

# Fase 5
pip install sentry-sdk django-auditlog

# Fase 6
# Redis ya instalado. Agregar django-debug-toolbar para auditoría
pip install django-debug-toolbar

# Fase 7
# Django Channels ya instalado

# Fase 8
pip install drf-spectacular
```

---

## Notas de trabajo

- Cada fase puede implementarse independientemente
- Las fases 1–4 son prerequisito para desplegar en producción con confianza
- Los tests (Fase 2) deben escribirse **antes** de tocar código existente en fases posteriores
- Priorizar siempre seguridad > funcionalidad > rendimiento
