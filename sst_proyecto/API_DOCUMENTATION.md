# 🚀 DOCUMENTACIÓN API - SISTEMA SST CENTRO MINERO

## 📋 INFORMACIÓN GENERAL
- **URL Base**: `http://localhost:8000/api/`
- **Autenticación**: Token Authentication
- **Token**: `e54d7383d11145390ad535d8e9a2673e3716136e`
- **Headers**: `Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e`

---

## 🔐 AUTENTICACIÓN

### Login
**Endpoint:** `POST /api/auth/usuarios/login/`

**Descripción:** Permite autenticar un usuario y obtener su token de acceso.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/usuarios/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"Julian\", \"password\": \"julian12345\"}"
```

**Body:**
```json
{
  "username": "Julian",
  "password": "julian12345"
}
```

---

## 👥 USUARIOS

### Perfil
**Endpoint:** `GET /api/auth/usuarios/perfil/`

**Descripción:** Obtiene la información del perfil del usuario autenticado.

**Request:**
```bash
curl -X GET http://localhost:8000/api/auth/usuarios/perfil/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

### Listar Usuarios
**Endpoint:** `GET /api/auth/usuarios/`

**Descripción:** Lista todos los usuarios del sistema.

**Request:**
```bash
curl -X GET http://localhost:8000/api/auth/usuarios/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

### Crear Usuario
**Endpoint:** `POST /api/auth/usuarios/`

**Descripción:** Crea un nuevo usuario en el sistema.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/usuarios/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"nuevo_usuario\", \"password\": \"clave123\", \"rol\": \"APRENDIZ\"}"
```

**Body:**
```json
{
  "username": "nuevo_usuario",
  "password": "clave123",
  "rol": "APRENDIZ"
}
```

**Parámetros:**
- `username` (string, requerido): Nombre de usuario único
- `password` (string, requerido): Contraseña del usuario
- `rol` (string, requerido): Rol del usuario (APRENDIZ, INSTRUCTOR, ADMIN, etc.)

---

## 🚪 CONTROL ACCESO

### Registrar Ingreso
**Endpoint:** `POST /api/acceso/registros/registrar_ingreso/`

**Descripción:** Registra el ingreso de un usuario al centro minero con su ubicación GPS.

**Request:**
```bash
curl -X POST http://localhost:8000/api/acceso/registros/registrar_ingreso/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e" \
  -H "Content-Type: application/json" \
  -d "{\"latitud\": 5.5339, \"longitud\": -73.3674}"
```

**Body:**
```json
{
  "latitud": 5.5339,
  "longitud": -73.3674
}
```

**Parámetros:**
- `latitud` (float, requerido): Coordenada de latitud GPS
- `longitud` (float, requerido): Coordenada de longitud GPS

### Registrar Egreso
**Endpoint:** `POST /api/acceso/registros/registrar_egreso/`

**Descripción:** Registra la salida de un usuario del centro minero con su ubicación GPS.

**Request:**
```bash
curl -X POST http://localhost:8000/api/acceso/registros/registrar_egreso/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e" \
  -H "Content-Type: application/json" \
  -d "{\"latitud\": 5.5339, \"longitud\": -73.3674}"
```

**Body:**
```json
{
  "latitud": 5.5339,
  "longitud": -73.3674
}
```

### Estado Actual
**Endpoint:** `GET /api/acceso/registros/mi_estado/`

**Descripción:** Consulta el estado actual de acceso del usuario (dentro/fuera del centro).

**Request:**
```bash
curl -X GET http://localhost:8000/api/acceso/registros/mi_estado/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

### Verificar Geocerca
**Endpoint:** `POST /api/acceso/geocercas/verificar_ubicacion/`

**Descripción:** Verifica si una ubicación GPS está dentro de la geocerca del centro minero.

**Request:**
```bash
curl -X POST http://localhost:8000/api/acceso/geocercas/verificar_ubicacion/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e" \
  -H "Content-Type: application/json" \
  -d "{\"latitud\": 5.5339, \"longitud\": -73.3674}"
```

**Body:**
```json
{
  "latitud": 5.5339,
  "longitud": -73.3674
}
```

---

## 🗺️ MAPAS

### Punto Encuentro Más Cercano
**Endpoint:** `GET /api/mapas/puntos-encuentro/mas_cercano/`

**Descripción:** Encuentra el punto de encuentro más cercano a una ubicación específica.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/mapas/puntos-encuentro/mas_cercano/?lat=5.5339&lon=-73.3674" \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

**Parámetros de Query:**
- `lat` (float, requerido): Latitud de la ubicación actual
- `lon` (float, requerido): Longitud de la ubicación actual

### Equipamientos Cercanos
**Endpoint:** `GET /api/mapas/equipamientos/cercanos/`

**Descripción:** Lista los equipamientos de seguridad cercanos dentro de un radio específico.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/mapas/equipamientos/cercanos/?lat=5.5339&lon=-73.3674&radio=500" \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

**Parámetros de Query:**
- `lat` (float, requerido): Latitud de la ubicación actual
- `lon` (float, requerido): Longitud de la ubicación actual
- `radio` (integer, opcional): Radio de búsqueda en metros (default: 500)

### Listar Edificios
**Endpoint:** `GET /api/mapas/edificios/`

**Descripción:** Lista todos los edificios del centro minero.

**Request:**
```bash
curl -X GET http://localhost:8000/api/mapas/edificios/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

---

## 🚨 EMERGENCIAS

### Botón de Pánico
**Endpoint:** `POST /api/emergencias/emergencias/boton_panico/`

**Descripción:** Activa una alerta de emergencia desde la ubicación del usuario.

**Request:**
```bash
curl -X POST http://localhost:8000/api/emergencias/emergencias/boton_panico/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e" \
  -H "Content-Type: application/json" \
  -d "{\"tipo\": 1, \"descripcion\": \"Emergencia prueba\", \"latitud\": 5.5339, \"longitud\": -73.3674}"
```

**Body:**
```json
{
  "tipo": 1,
  "descripcion": "Emergencia prueba",
  "latitud": 5.5339,
  "longitud": -73.3674
}
```

**Parámetros:**
- `tipo` (integer, requerido): Tipo de emergencia (1: Médica, 2: Incendio, 3: Evacuación, etc.)
- `descripcion` (string, requerido): Descripción detallada de la emergencia
- `latitud` (float, requerido): Coordenada de latitud de la emergencia
- `longitud` (float, requerido): Coordenada de longitud de la emergencia

### Emergencias Activas
**Endpoint:** `GET /api/emergencias/emergencias/activas/`

**Descripción:** Lista todas las emergencias activas en el centro minero.

**Request:**
```bash
curl -X GET http://localhost:8000/api/emergencias/emergencias/activas/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

### Atender Emergencia
**Endpoint:** `POST /api/emergencias/emergencias/{id}/atender/`

**Descripción:** Marca una emergencia como atendida por el personal autorizado.

**Request:**
```bash
curl -X POST http://localhost:8000/api/emergencias/emergencias/1/atender/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

**Parámetros de URL:**
- `id` (integer, requerido): ID de la emergencia a atender

### Contactos Emergencia
**Endpoint:** `GET /api/emergencias/contactos/`

**Descripción:** Lista los contactos de emergencia registrados en el sistema.

**Request:**
```bash
curl -X GET http://localhost:8000/api/emergencias/contactos/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

---

## 📊 REPORTES

### Dashboard
**Endpoint:** `GET /api/reportes/dashboard/`

**Descripción:** Obtiene los datos principales del dashboard del sistema.

**Request:**
```bash
curl -X GET http://localhost:8000/api/reportes/dashboard/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

### Reporte Aforo
**Endpoint:** `GET /api/reportes/aforo/`

**Descripción:** Genera un reporte del aforo de personas en el centro minero durante un período de tiempo.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/reportes/aforo/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31" \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

**Parámetros de Query:**
- `fecha_inicio` (date, requerido): Fecha de inicio del reporte (formato: YYYY-MM-DD)
- `fecha_fin` (date, requerido): Fecha de fin del reporte (formato: YYYY-MM-DD)

### Reporte Incidentes
**Endpoint:** `GET /api/reportes/incidentes/`

**Descripción:** Genera un reporte de incidentes y emergencias registrados.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/reportes/incidentes/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31" \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

**Parámetros de Query:**
- `fecha_inicio` (date, requerido): Fecha de inicio del reporte (formato: YYYY-MM-DD)
- `fecha_fin` (date, requerido): Fecha de fin del reporte (formato: YYYY-MM-DD)

### Reporte Asistencia
**Endpoint:** `GET /api/reportes/asistencia/`

**Descripción:** Genera un reporte de asistencia de aprendices por ficha de formación.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/reportes/asistencia/?ficha=2558106&fecha_inicio=2024-01-01&fecha_fin=2024-01-31" \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

**Parámetros de Query:**
- `ficha` (integer, requerido): Número de ficha de formación
- `fecha_inicio` (date, requerido): Fecha de inicio del reporte (formato: YYYY-MM-DD)
- `fecha_fin` (date, requerido): Fecha de fin del reporte (formato: YYYY-MM-DD)

---

## 📝 NOTAS IMPORTANTES

### Coordenadas del Centro Minero
- **Latitud**: 5.5339
- **Longitud**: -73.3674
- **Ubicación**: Centro Minero SENA, Sogamoso, Boyacá, Colombia

### Roles de Usuario
- `APRENDIZ`: Estudiante en formación
- `INSTRUCTOR`: Docente o instructor
- `ADMIN`: Administrador del sistema
- `BRIGADISTA`: Personal de emergencias
- `SEGURIDAD`: Personal de vigilancia

### Tipos de Emergencias
1. Emergencia Médica
2. Incendio
3. Evacuación
4. Accidente Laboral
5. Otro

### ⚠️ Códigos de Respuesta HTTP

| Código | Estado | Descripción |
|--------|--------|-------------|
| **200** | ✅ OK | Solicitud exitosa |
| **201** | ✅ Creado | Recurso creado exitosamente |
| **400** | ❌ Bad Request | Error en los datos enviados |
| **401** | ❌ No autenticado | Token inválido o no proporcionado |
| **403** | ❌ Sin permisos | No tiene autorización para acceder al recurso |
| **404** | ❌ No encontrado | Recurso no encontrado |
| **500** | ❌ Error del servidor | Error interno del servidor |

### 🔑 Autenticación Requerida
**Token:** `e54d7383d11145390ad535d8e9a2673e3716136e`

**Headers requeridos:**
```
Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e
```

Para todos los endpoints (excepto login), debes incluir este header de autenticación en cada petición.

---

## 🔧 CONFIGURACIÓN INICIAL

Para usar esta API necesitas:

1. **Obtener un Token de Autenticación**: Hacer login con tus credenciales
2. **Incluir el Token**: En cada petición mediante el header `Authorization: Token <tu_token>`
3. **Especificar Content-Type**: Para peticiones POST/PUT usar `Content-Type: application/json`

---

## 📱 EJEMPLO DE FLUJO COMPLETO

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/usuarios/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "Julian", "password": "julian12345"}'
```

### 2. Registrar Ingreso
```bash
curl -X POST http://localhost:8000/api/acceso/registros/registrar_ingreso/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e" \
  -H "Content-Type: application/json" \
  -d '{"latitud": 5.5339, "longitud": -73.3674}'
```

### 3. Consultar Estado
```bash
curl -X GET http://localhost:8000/api/acceso/registros/mi_estado/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e"
```

### 4. Registrar Egreso
```bash
curl -X POST http://localhost:8000/api/acceso/registros/registrar_egreso/ \
  -H "Authorization: Token e54d7383d11145390ad535d8e9a2673e3716136e" \
  -H "Content-Type: application/json" \
  -d '{"latitud": 5.5339, "longitud": -73.3674}'
```

---

**Versión:** 1.0  
**Última actualización:** 2024  
**Contacto:** Centro Minero SENA Sogamoso