# 📁 Estructura de Templates - Sistema SST

> Documentación de la organización de plantillas del proyecto

## 📊 Resumen
- **Total de archivos:** 36 templates HTML
- **Total de carpetas:** 9 directorios
- **Última actualización:** Febrero 2026

---

## 🗂️ Estructura de Carpetas

```
templates/
├── 📄 Archivos Raíz (7 archivos)
├── 📁 dashboard/ (6 roles + subcarpetas)
├── 📁 registration/ (6 archivos de autenticación)
└── 📁 reportes/ (5 archivos de incidentes)
```

---

## 📄 ARCHIVOS RAÍZ

### Templates Base
| Archivo | Descripción | Hereda de |
|---------|-------------|-----------|
| `base.html` | Template base principal del sistema | - |
| `dashboard.html` | Base para todos los dashboards | `base.html` |

### Template de Autenticación
| Archivo | Descripción | Usado en |
|---------|-------------|----------|
| `login.html` | Página de inicio de sesión | `usuarios/login_view.py` |

### Templates de Módulos Principales
| Archivo | Descripción | URL |
|---------|-------------|-----|
| `control_acceso.html` | Control de ingresos/egresos | `/acceso/` |
| `emergencias.html` | Sistema de emergencias | `/emergencias/` |
| `mapas.html` | Mapas interactivos del centro | `/mapas/` |
| `reportes.html` | Índice general de reportes | `/reportes/general/` |

---

## 📁 DASHBOARD/ - Dashboards por Rol

### Estructura de Dashboards
Cada rol tiene:
1. **Archivo principal:** `dashboard/{rol}.html` - Dashboard principal del rol
2. **Subcarpeta:** `dashboard/{rol}/` - Vistas específicas del rol

### 👨‍🎓 APRENDIZ
```
dashboard/
├── aprendiz.html                    # Dashboard principal
└── aprendiz/
    ├── mi_horario.html              # Horario de clases
    ├── mi_asistencia.html           # Registro de asistencia
    ├── informacion_sst.html         # Información SST
    └── mis_alertas.html             # Alertas y notificaciones
```

**URLs relacionadas:**
- `/` - Dashboard principal (si rol = APRENDIZ)
- `/aprendiz/horario/`
- `/aprendiz/asistencia/`
- `/aprendiz/informacion-sst/`
- `/aprendiz/alertas/`

---

### 👨‍🏫 INSTRUCTOR
```
dashboard/
├── instructor.html                  # Dashboard principal
└── instructor/
    ├── mis_aprendices.html          # Listado de aprendices
    └── registrar_asistencia.html    # Registro de asistencia
```

**URLs relacionadas:**
- `/` - Dashboard principal (si rol = INSTRUCTOR)
- `/instructor/mis-aprendices/`
- `/instructor/asistencia/`

---

### 👔 ADMINISTRATIVO
```
dashboard/
├── administrativo.html              # Dashboard principal
└── administrativo/
    ├── gestion_usuarios.html        # CRUD de usuarios
    └── configuracion.html           # Configuración del sistema
```

**URLs relacionadas:**
- `/` - Dashboard principal (si rol = ADMINISTRATIVO)
- `/administrativo/usuarios/`
- `/administrativo/configuracion/`

---

### 👮 VIGILANCIA
```
dashboard/
├── vigilancia.html                  # Dashboard principal
└── vigilancia/
    └── gestion_visitantes.html      # Gestión de visitantes
```

**URLs relacionadas:**
- `/` - Dashboard principal (si rol = VIGILANCIA)
- `/vigilancia/visitantes/`

---

### 🚒 BRIGADA
```
dashboard/
├── brigada.html                     # Dashboard principal
└── brigada/
    ├── equipos.html                 # Equipamiento de seguridad
    ├── mi_brigada.html              # Miembros de la brigada
    └── capacitaciones.html          # Capacitaciones y cursos
```

**URLs relacionadas:**
- `/` - Dashboard principal (si rol = BRIGADA)
- `/brigada/equipos/`
- `/brigada/mi-brigada/`
- `/brigada/capacitaciones/`

---

### 👤 VISITANTE
```
dashboard/
├── visitante.html                   # Dashboard principal
└── visitante/                       # (Subcarpeta preparada para futuras vistas)
```

**URLs relacionadas:**
- `/` - Dashboard principal (si rol = VISITANTE)

---

## 📁 REGISTRATION/ - Autenticación

Sistema completo de recuperación de contraseña y autenticación.

| Archivo | Descripción | URL |
|---------|-------------|-----|
| `base_auth.html` | Base para templates de autenticación | - |
| `recuperar_clave.html` | Formulario de recuperación | `/accounts/password-reset/` |
| `correo_enviado.html` | Confirmación de envío | `/accounts/password-reset/done/` |
| `nueva_clave.html` | Formulario de nueva clave | `/accounts/reset/<uidb64>/<token>/` |
| `clave_cambiada.html` | Confirmación de cambio | `/accounts/reset/done/` |
| `email_recuperacion.html` | Template del email | (Email template) |

**Flujo completo:**
1. Usuario olvida contraseña → `recuperar_clave.html`
2. Email enviado → `correo_enviado.html`
3. Click en link del email → `nueva_clave.html`
4. Contraseña cambiada → `clave_cambiada.html`

---

## 📁 REPORTES/ - Sistema de Incidentes

Gestión completa de incidentes y reportes de seguridad.

| Archivo | Descripción | URL |
|---------|-------------|-----|
| `index.html` | Índice principal de reportes | `/reportes/` |
| `incidentes_lista.html` | Lista de todos los incidentes | `/reportes/incidentes/` |
| `incidente_form.html` | Formulario de nuevo incidente | `/reportes/incidente/crear/` |
| `incidente_detalle.html` | Detalles de un incidente | `/reportes/incidente/<id>/` |
| `incidente_actualizar.html` | Actualizar estado/info | `/reportes/incidente/<id>/actualizar/` |

**Flujo típico:**
1. Ver lista → `incidentes_lista.html`
2. Crear nuevo → `incidente_form.html`
3. Ver detalles → `incidente_detalle.html`
4. Actualizar → `incidente_actualizar.html`

---

## 🎨 Jerarquía de Herencia

```
base.html (Template raíz)
    │
    ├── dashboard.html (Base de dashboards)
    │       │
    │       ├── dashboard/aprendiz.html
    │       ├── dashboard/instructor.html
    │       ├── dashboard/administrativo.html
    │       ├── dashboard/brigada.html
    │       ├── dashboard/vigilancia.html
    │       └── dashboard/visitante.html
    │
    ├── control_acceso.html
    ├── emergencias.html
    ├── mapas.html
    └── reportes.html

registration/base_auth.html (Base de autenticación)
    │
    ├── recuperar_clave.html
    ├── correo_enviado.html
    ├── nueva_clave.html
    └── clave_cambiada.html
```

---

## 🔧 Convenciones de Nombres

### Archivos Principales de Dashboard
- **Patrón:** `dashboard/{rol}.html`
- **Ejemplo:** `dashboard/aprendiz.html`

### Vistas Específicas de Rol
- **Patrón:** `dashboard/{rol}/{funcionalidad}.html`
- **Ejemplo:** `dashboard/aprendiz/mi_horario.html`

### Módulos del Sistema
- **Patrón:** `{modulo}.html` en raíz
- **Ejemplo:** `mapas.html`, `emergencias.html`

---

## ✅ Archivos Eliminados (Limpieza)

Durante la reorganización se eliminaron:
- ❌ `login_simple.html` - Duplicado sin uso (se usa `login.html`)

---

## 📝 Notas para Desarrolladores

### Al Crear Nuevos Templates:

1. **Dashboard de nuevo rol:**
   - Crear `dashboard/{rol}.html`
   - Crear carpeta `dashboard/{rol}/`
   - Actualizar `usuarios/models.py` método `get_dashboard_template()`
   - Actualizar `sst_proyecto/urls.py` en `dashboard_templates`

2. **Vista específica de rol:**
   - Crear en `dashboard/{rol}/{vista}.html`
   - Crear URL en `sst_proyecto/urls.py`
   - Crear view en `sst_proyecto/urls.py` o app correspondiente

3. **Nuevo módulo principal:**
   - Crear en raíz `templates/{modulo}.html`
   - Extender de `base.html`
   - Crear URL y view correspondientes

### Evitar:
- ❌ No crear archivos duplicados (como `login_simple.html`)
- ❌ No crear templates en ubicaciones inconsistentes
- ❌ No olvidar actualizar esta documentación

---

## 🔗 Referencias Útiles

- **Configuración de templates:** `sst_proyecto/settings.py` (línea 77-91)
- **URLs principales:** `sst_proyecto/urls.py`
- **Login view:** `usuarios/login_view.py`
- **Dashboard view:** `sst_proyecto/urls.py` (línea 16-120)

---

## 📊 Estadísticas

- **Total archivos HTML:** 36
- **Dashboards por rol:** 6
- **Módulos principales:** 4
- **Sistema de autenticación:** 6 templates
- **Sistema de reportes:** 5 templates

---

**Última actualización:** Febrero 2026
**Mantenedor:** Equipo de Desarrollo SST Centro Minero SENA
