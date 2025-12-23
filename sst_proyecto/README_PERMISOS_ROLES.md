# Sistema de Permisos y Roles - SST Centro Minero

## Implementación de Seguridad Basada en Roles

Este documento explica cómo funciona el sistema de control de acceso basado en roles implementado en el proyecto.

---

## 📋 Roles del Sistema

El sistema cuenta con 6 roles diferentes:

1. **ADMINISTRATIVO** - Control total del sistema
2. **INSTRUCTOR** - Gestión de aprendices y acceso limitado
3. **VIGILANCIA** - Control de acceso y seguridad
4. **BRIGADA** - Gestión de emergencias
5. **APRENDIZ** - Acceso limitado a su información
6. **VISITANTE** - Acceso mínimo

---

## 🔒 Restricciones por Módulo

### 1. Control de Acceso (`/acceso/`)

**Pueden Acceder:**
- ✅ ADMINISTRATIVO
- ✅ VIGILANCIA
- ✅ INSTRUCTOR

**Funcionalidades:**
- Registrar ingresos/egresos
- Escanear códigos QR
- Ver estadísticas en tiempo real
- Gestionar aforo

**NO Pueden Acceder:**
- ❌ APRENDIZ
- ❌ BRIGADA
- ❌ VISITANTE

---

### 2. Mapa Interactivo (`/mapas/`)

**Pueden Acceder:**
- ✅ ADMINISTRATIVO
- ✅ INSTRUCTOR
- ✅ VIGILANCIA
- ✅ BRIGADA
- ✅ APRENDIZ

**Funcionalidades:**
- Ver ubicación en tiempo real
- Ver geocerca del centro
- Ver puntos de interés
- Rutas de evacuación (BRIGADA prioritario)

**NO Pueden Acceder:**
- ❌ VISITANTE

---

### 3. Emergencias (`/emergencias/`)

**Pueden Acceder:**
- ✅ ADMINISTRATIVO
- ✅ BRIGADA (prioridad)
- ✅ INSTRUCTOR
- ✅ VIGILANCIA
- ✅ APRENDIZ (solo ver/reportar)

**Funcionalidades:**
- Reportar emergencias
- Ver estado de emergencias
- Coordinar brigada (BRIGADA/ADMINISTRATIVO)

**NO Pueden Acceder:**
- ❌ VISITANTE

---

### 4. Reportes (`/reportes/`)

**Pueden Acceder:**
- ✅ ADMINISTRATIVO (todos los reportes)
- ✅ INSTRUCTOR (reportes de sus aprendices)
- ✅ VIGILANCIA (reportes de acceso)
- ✅ BRIGADA (reportes de emergencias)
- ✅ APRENDIZ (solo sus propios reportes)

**NO Pueden Acceder:**
- ❌ VISITANTE

---

### 5. Gestión de Usuarios

**Pueden Acceder:**
- ✅ ADMINISTRATIVO únicamente

**Funcionalidades:**
- Crear/editar/eliminar usuarios
- Ver lista completa de usuarios
- Gestionar permisos

**NO Pueden Acceder:**
- ❌ Todos los demás roles

---

### 6. Gestión de Visitantes

**Pueden Acceder:**
- ✅ ADMINISTRATIVO
- ✅ VIGILANCIA
- ✅ INSTRUCTOR

**Funcionalidades:**
- Registrar visitantes
- Generar códigos QR para visitantes
- Ver historial de visitas

---

## 🛡️ Implementación Técnica

### 1. Decoradores para Vistas Django (HTML)

#### `@rol_requerido()`
Restringe acceso a roles específicos:

```python
@rol_requerido('ADMINISTRATIVO', 'VIGILANCIA')
def mi_vista(request):
    # Solo ADMINISTRATIVO y VIGILANCIA pueden acceder
    return render(request, 'template.html')
```

#### `@solo_administrativo`
Acceso exclusivo para administrativos:

```python
@solo_administrativo
def vista_admin(request):
    # Solo ADMINISTRATIVO puede acceder
    return render(request, 'admin.html')
```

#### `@excluir_visitantes`
Bloquea acceso a visitantes:

```python
@excluir_visitantes
def vista_interna(request):
    # Todos menos VISITANTE pueden acceder
    return render(request, 'interna.html')
```

---

### 2. Clases de Permisos para REST Framework (API)

#### `EsAdministrativo`
Solo usuarios con rol ADMINISTRATIVO:

```python
class MiViewSet(viewsets.ModelViewSet):
    permission_classes = [EsAdministrativo]
```

#### `EsVigilanciaOAdministrativo`
Para control de acceso:

```python
class RegistroAccesoViewSet(viewsets.ModelViewSet):
    permission_classes = [EsVigilanciaOAdministrativo]
```

#### `EsBrigadaOAdministrativo`
Para gestión de emergencias:

```python
class EmergenciaViewSet(viewsets.ModelViewSet):
    permission_classes = [EsBrigadaOAdministrativo]
```

#### `NoEsVisitante`
Excluye visitantes:

```python
class MapasViewSet(viewsets.ModelViewSet):
    permission_classes = [NoEsVisitante]
```

#### `PuedeGestionarUsuarios`
Solo ADMINISTRATIVO modifica, todos ven su perfil:

```python
class UsuarioViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ['list', 'create', 'update']:
            return [PuedeGestionarUsuarios()]
        return [IsAuthenticated()]
```

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Vista HTML con Restricción de Rol

**Archivo:** `sst_proyecto/urls.py`

```python
@rol_requerido('ADMINISTRATIVO', 'VIGILANCIA', 'INSTRUCTOR')
def control_acceso_view(request):
    """
    Solo ADMINISTRATIVO, VIGILANCIA e INSTRUCTOR pueden ver Control de Acceso
    """
    return render(request, 'control_acceso.html')
```

**Resultado:**
- Si un APRENDIZ intenta acceder a `/acceso/`:
  - Es redirigido al dashboard
  - Ve mensaje: "No tienes permiso para acceder a esta sección"

---

### Ejemplo 2: API con Permisos Dinámicos

**Archivo:** `control_acceso/views.py`

```python
class GeocercaViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        # Modificar geocercas: solo ADMINISTRATIVO
        if self.action in ['create', 'update', 'destroy']:
            return [EsAdministrativo()]
        # Ver geocercas: todos los autenticados
        return [IsAuthenticated()]
```

**Resultado:**
- INSTRUCTOR puede ver geocercas (GET)
- INSTRUCTOR NO puede crear/editar geocercas (POST/PUT)
- ADMINISTRATIVO puede hacer todo

---

### Ejemplo 3: Menú Dinámico en Base.html

**Archivo:** `templates/base.html`

```django
{% if user.rol == 'ADMINISTRATIVO' %}
    <li><a href="/acceso/">Control Acceso</a></li>
    <li><a href="/usuarios/">Gestión Usuarios</a></li>
{% elif user.rol == 'APRENDIZ' %}
    <li><a href="#">Mi Horario</a></li>
    <li><a href="#">Mi Asistencia</a></li>
{% endif %}
```

**Resultado:**
- Cada rol ve solo las opciones que puede usar
- El menú cambia completamente según el rol

---

## ⚠️ Mensajes de Error

### Error 403 (Forbidden)
Si un usuario intenta acceder sin permisos:

```json
{
    "detail": "Solo el personal administrativo puede realizar esta acción."
}
```

### Redirección con Mensaje
En vistas HTML:

```
"No tienes permiso para acceder a esta sección. Se requiere rol: ADMINISTRATIVO, VIGILANCIA"
```

---

## 🧪 Cómo Probar las Restricciones

### Paso 1: Ingresar como APRENDIZ

```bash
Usuario: aprendiz1
Contraseña: aprendiz123
```

**Intenta acceder a:**
- `/acceso/` → ❌ Bloqueado
- `/mapas/` → ✅ Permitido
- `/api/auth/usuarios/` → ❌ Bloqueado

---

### Paso 2: Ingresar como VIGILANCIA

```bash
Usuario: vigilante1
Contraseña: vigilante123
```

**Intenta acceder a:**
- `/acceso/` → ✅ Permitido
- `/api/acceso/registros/` → ✅ Permitido
- `/api/auth/usuarios/` (POST) → ❌ Bloqueado

---

### Paso 3: Ingresar como ADMINISTRATIVO

```bash
Usuario: admin
Contraseña: admin123
```

**Tiene acceso a:**
- ✅ TODO el sistema sin restricciones

---

## 🔐 Seguridad Implementada

### 1. Frontend (Templates)
- Menú dinámico según rol
- Opciones ocultas para roles sin permiso

### 2. Backend (URLs/Views)
- Decoradores validan rol antes de renderizar
- Redirección automática si no tiene permiso

### 3. API (REST Framework)
- Clases de permisos personalizadas
- Validación en cada endpoint
- Respuesta 403 si no tiene permiso

### 4. Base de Datos
- Usuario tiene campo `rol`
- No se puede cambiar rol sin ser ADMINISTRATIVO

---

## 📊 Tabla Resumen de Permisos

| Módulo          | ADMIN | INSTRUCTOR | VIGILANCIA | BRIGADA | APRENDIZ | VISITANTE |
|-----------------|-------|------------|------------|---------|----------|-----------|
| Dashboard       | ✅    | ✅         | ✅         | ✅      | ✅       | ✅        |
| Control Acceso  | ✅    | ✅         | ✅         | ❌      | ❌       | ❌        |
| Mapas           | ✅    | ✅         | ✅         | ✅      | ✅       | ❌        |
| Emergencias     | ✅    | ✅         | ✅         | ✅      | ✅ (ver) | ❌        |
| Reportes        | ✅    | ✅ (propios)| ✅ (acceso)| ✅ (emergencias)| ✅ (propios)| ❌|
| Gestión Usuarios| ✅    | ❌         | ❌         | ❌      | ❌       | ❌        |
| Visitantes      | ✅    | ✅         | ✅         | ❌      | ❌       | ❌        |

---

## 🚀 Ventajas de Esta Implementación

1. **Seguridad en Capas**
   - Frontend: Oculta opciones
   - Backend: Valida permisos
   - API: Protege endpoints

2. **Fácil de Mantener**
   - Permisos centralizados en `usuarios/permissions.py`
   - Reutilización de decoradores

3. **Flexible**
   - Fácil agregar nuevos roles
   - Fácil cambiar permisos de módulos

4. **User-Friendly**
   - Mensajes claros de error
   - Redirección automática
   - Menús adaptados al rol

---

## 📝 Archivos Modificados

1. **`usuarios/permissions.py`** - NUEVO
   - Decoradores personalizados
   - Clases de permisos REST
   - Funciones helper

2. **`sst_proyecto/urls.py`**
   - Agregados decoradores a vistas HTML

3. **`control_acceso/views.py`**
   - Permisos en ViewSets

4. **`usuarios/views.py`**
   - Permisos dinámicos según acción

5. **`mapas/views.py`**
   - Permisos en todos los ViewSets

6. **`templates/base.html`** - Ya existía
   - Menú dinámico por rol

---

## ✅ Sistema de Permisos Completamente Implementado

Ahora el sistema tiene **restricciones de seguridad robustas** en:
- ✅ Vistas HTML
- ✅ URLs
- ✅ APIs REST
- ✅ Frontend (menú dinámico)

**Un APRENDIZ ya NO puede acceder a Control de Acceso ni gestión de usuarios, incluso si escribe la URL directamente.**
