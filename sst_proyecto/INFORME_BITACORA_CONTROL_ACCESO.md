# INFORME TÉCNICO - BITÁCORA DE DESARROLLO
## Sistema SST - Centro Minero SENA

---

### 📋 INFORMACIÓN GENERAL

**Proyecto:** Sistema de Seguridad y Salud en el Trabajo - Centro Minero SENA
**Módulo Desarrollado:** Control de Acceso
**Rama de Trabajo:** `tenjo`
**Fecha:** Diciembre 2024
**Desarrollador:** Equipo de Desarrollo SST
**Tecnologías:** Django 4.2, Python 3.12, PostgreSQL/SQLite, Bootstrap 5, JavaScript ES6

---

## 🎯 OBJETIVOS DEL MÓDULO

### Objetivo General
Implementar un sistema integral de control de acceso para el Centro Minero SENA que permita gestionar, registrar y monitorear el ingreso y egreso de personas (estudiantes, instructores, personal administrativo, vigilancia, brigada de emergencias y visitantes) mediante tecnologías de identificación por código QR, registro manual y detección automática por geolocalización.

### Objetivos Específicos
1. Desarrollar un sistema de generación de códigos QR únicos para cada usuario del sistema
2. Implementar un escáner QR integrado en la interfaz web para registro de accesos
3. Crear APIs REST para gestión de registros de ingreso y egreso
4. Implementar un sistema de estadísticas en tiempo real del aforo del centro
5. Desarrollar alertas de capacidad máxima con validación de geocercas
6. Diseñar una interfaz responsiva y moderna para la gestión de accesos

---

## 🚀 DESARROLLO REALIZADO

### 1. SISTEMA DE CÓDIGOS QR

#### Implementación
Se desarrolló un sistema completo de generación de códigos QR personalizados utilizando la librería `qrcode` y `Pillow` para Python.

**Archivos Creados:**
- `control_acceso/utils.py` - Módulo de utilidades

**Funcionalidades Implementadas:**

```python
def generar_qr_usuario(usuario):
    """
    Genera un código QR único para un usuario
    - Codifica: SST-USUARIO-{id}-{documento}
    - Incluye: Nombre, documento, rol
    - Formato: PNG en base64
    - Tamaño: Optimizado para escaneo móvil
    """
```

**Características:**
- ✅ Códigos QR únicos e irrepetibles por usuario
- ✅ Información visual del usuario (nombre, documento, rol)
- ✅ Codificación en base64 para transmisión web
- ✅ Nivel de corrección de errores alto (ERROR_CORRECT_H)
- ✅ Descarga directa en formato PNG

**Endpoints API:**
- `GET /api/auth/usuarios/mi_qr/` - Generar QR del usuario autenticado
- `GET /api/auth/usuarios/{id}/generar_qr/` - Generar QR de cualquier usuario

**Resultado:** Sistema completamente funcional que permite a cada usuario obtener su código QR personalizado para acceso al centro.

---

### 2. ESCANEO DE CÓDIGOS QR

#### Implementación
Integración de la librería `html5-qrcode` para escaneo de códigos QR directamente desde el navegador usando la cámara del dispositivo.

**Archivos Modificados:**
- `templates/control_acceso.html` - Interfaz con modal de escaneo

**Funcionalidades Implementadas:**

**JavaScript Frontend:**
```javascript
// Escáner QR con detección automática
function iniciarEscanerQR() {
    html5QrcodeScanner = new Html5QrcodeScanner(
        "reader",
        { fps: 10, qrbox: {width: 250, height: 250} },
        false
    );
    html5QrcodeScanner.render(onScanSuccess, onScanFailure);
}
```

**Lógica de Negocio:**
- Si el usuario NO está en el centro → Registra **INGRESO**
- Si el usuario YA está en el centro → Registra **EGRESO**
- Detección automática del estado actual
- Validación de ubicación mediante geocercas
- Verificación de aforo antes de permitir ingreso

**Endpoint API:**
- `POST /api/acceso/registros/escanear_qr/`

**Parámetros:**
```json
{
  "codigo_qr": "SST-USUARIO-1-1234567890",
  "latitud": 5.5339,
  "longitud": -73.3674
}
```

**Resultado:** Sistema de escaneo QR completamente operativo con detección inteligente de ingreso/egreso.

---

### 3. REGISTRO MANUAL DE ACCESO

#### Implementación
Sistema de registro manual mediante formularios para casos donde el escaneo QR no esté disponible.

**Archivos Modificados:**
- `control_acceso/views.py` - ViewSets con endpoints
- `control_acceso/serializers.py` - Validadores

**Funcionalidades Implementadas:**

**Endpoints API:**
- `POST /api/acceso/registros/registrar_ingreso/`
- `POST /api/acceso/registros/registrar_egreso/`

**Validaciones:**
1. ✅ Usuario existe en el sistema
2. ✅ No hay ingreso duplicado (para ingreso)
3. ✅ Existe un ingreso activo (para egreso)
4. ✅ Aforo no excedido
5. ✅ Ubicación dentro de geocerca (modo automático)

**Características:**
- Selección de usuario desde dropdown
- Múltiples métodos: Manual, QR, Automático
- Campo de notas opcional
- Validación en tiempo real

**Resultado:** Sistema de registro manual robusto como respaldo del escaneo QR.

---

### 4. ESTADÍSTICAS EN TIEMPO REAL

#### Implementación
Dashboard con métricas actualizadas automáticamente cada 30 segundos.

**Archivos Modificados:**
- `control_acceso/utils.py` - Funciones de estadísticas
- `control_acceso/views.py` - Endpoint de estadísticas

**Métricas Implementadas:**

```python
def obtener_estadisticas_hoy():
    return {
        'ingresos_hoy': int,         # Total de ingresos del día
        'personas_dentro': int,       # Personas actualmente en el centro
        'visitantes_activos': int,    # Visitantes sin salida registrada
        'aforo': {
            'personas_dentro': int,
            'aforo_maximo': int,
            'aforo_minimo': int,
            'porcentaje': float,
            'alerta': str,            # NORMAL, ADVERTENCIA, CRITICO
            'mensaje': str
        }
    }
```

**Endpoint API:**
- `GET /api/acceso/registros/estadisticas/`

**Visualización:**
- 4 tarjetas con métricas principales
- Gráfico de barra de porcentaje de aforo
- Códigos de color según nivel de alerta
- Actualización automática vía JavaScript

**Resultado:** Dashboard en tiempo real que permite monitoreo constante del estado del centro.

---

### 5. SISTEMA DE ALERTAS DE AFORO

#### Implementación
Sistema de validación de capacidad máxima con tres niveles de alerta.

**Archivos Creados/Modificados:**
- `control_acceso/models.py` - Modelo ConfiguracionAforo
- `control_acceso/utils.py` - Función verificar_aforo_actual()

**Configuración:**
```python
class ConfiguracionAforo(models.Model):
    aforo_maximo = 2000      # Capacidad máxima
    aforo_minimo = 1800      # Umbral de advertencia
    mensaje_alerta = str     # Mensaje personalizado
    activo = bool
```

**Niveles de Alerta:**

| Nivel | Condición | Acción | Color |
|-------|-----------|--------|-------|
| **NORMAL** | personas < aforo_minimo | Permitir ingreso | Verde |
| **ADVERTENCIA** | personas >= aforo_minimo | Mostrar alerta visual | Amarillo |
| **CRÍTICO** | personas >= aforo_maximo | Bloquear nuevos ingresos | Rojo |

**Características:**
- ✅ Validación antes de cada registro de ingreso
- ✅ Mensaje de error cuando se alcanza aforo máximo
- ✅ Alerta visual con animación en interfaz
- ✅ Configuración dinámica desde base de datos

**Endpoint API:**
- `GET /api/acceso/config-aforo/aforo_actual/`

**Resultado:** Sistema de control de aforo efectivo que previene sobrecupo del centro.

---

### 6. GEOCERCAS Y VALIDACIÓN DE UBICACIÓN

#### Implementación
Sistema de perímetro virtual usando la fórmula de Haversine para cálculo de distancias.

**Archivos Modificados:**
- `control_acceso/models.py` - Modelo Geocerca
- `mapas/services.py` - Función calcular_distancia()

**Modelo de Datos:**
```python
class Geocerca(models.Model):
    nombre = str                    # "Centro Minero SENA Sogamoso"
    centro_latitud = 5.5339        # Coordenadas del centro
    centro_longitud = -73.3674
    radio_metros = 200             # Radio de validación
    activo = bool
```

**Algoritmo de Validación:**
```python
def punto_esta_dentro(self, latitud, longitud):
    """
    Usa la fórmula de Haversine para calcular distancia
    Retorna True si está dentro del radio
    """
    distancia = calcular_distancia(
        self.centro_latitud,
        self.centro_longitud,
        latitud,
        longitud
    )
    return distancia <= self.radio_metros
```

**Aplicación:**
- Validación en registros automáticos
- Verificación opcional en registros manuales
- Logs de ubicación en cada acceso

**Resultado:** Sistema de geocercas funcional que valida ubicación geográfica de los accesos.

---

### 7. INTERFAZ DE USUARIO

#### Implementación
Diseño moderno y responsivo usando Bootstrap 5 y CSS personalizado.

**Archivos Creados/Modificados:**
- `templates/control_acceso.html` - Interfaz completa

**Componentes de la Interfaz:**

**1. Dashboard de Estadísticas**
- 4 tarjetas con métricas en tiempo real
- Iconos descriptivos (Bootstrap Icons)
- Colores temáticos del SENA (verde)
- Animaciones suaves en hover

**2. Tabla de Registros**
- Listado de últimos 50 registros
- Filtros: Todos / Dentro / Salieron
- Información detallada por registro
- Badges de estado visual

**3. Modal de Escaneo QR**
- Visor de cámara integrado
- Botón para cambiar cámara
- Resultado visual del escaneo
- Feedback inmediato

**4. Modal de Registro Manual**
- Formulario con validación
- Selección de usuario
- Selección de método
- Campo de notas

**5. Modal Mi QR**
- Visualización del código QR personal
- Botón de descarga
- Información del usuario

**Características Responsive:**
- ✅ Adaptable a dispositivos móviles
- ✅ Menú colapsable en pantallas pequeñas
- ✅ Tablas con scroll horizontal
- ✅ Modales optimizados para móvil

**Resultado:** Interfaz profesional, intuitiva y completamente funcional.

---

## 📊 ARQUITECTURA TÉCNICA

### Modelos de Base de Datos

```python
# 1. Geocerca - Perímetro virtual
class Geocerca(models.Model):
    nombre, descripcion
    centro_latitud, centro_longitud, radio_metros
    activo, fecha_creacion

# 2. RegistroAcceso - Historial de entradas/salidas
class RegistroAcceso(models.Model):
    usuario (FK)
    tipo: INGRESO/EGRESO
    fecha_hora_ingreso, fecha_hora_egreso
    latitud_ingreso, longitud_ingreso
    latitud_egreso, longitud_egreso
    metodo_ingreso, metodo_egreso: MANUAL/QR/AUTOMATICO
    notas

# 3. ConfiguracionAforo - Configuración de capacidad
class ConfiguracionAforo(models.Model):
    aforo_maximo, aforo_minimo
    mensaje_alerta
    activo
```

### APIs REST Implementadas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/auth/usuarios/mi_qr/` | Obtener mi código QR |
| GET | `/api/auth/usuarios/{id}/generar_qr/` | Generar QR de usuario |
| POST | `/api/acceso/registros/escanear_qr/` | Procesar escaneo QR |
| POST | `/api/acceso/registros/registrar_ingreso/` | Registro manual de ingreso |
| POST | `/api/acceso/registros/registrar_egreso/` | Registro manual de egreso |
| GET | `/api/acceso/registros/estadisticas/` | Obtener estadísticas |
| GET | `/api/acceso/registros/registros_recientes/` | Listar registros recientes |
| GET | `/api/acceso/config-aforo/aforo_actual/` | Estado actual del aforo |
| GET | `/api/acceso/geocercas/` | Listar geocercas |
| POST | `/api/acceso/geocercas/{id}/verificar_ubicacion/` | Validar ubicación |

**Total de Endpoints:** 10 APIs completamente funcionales

---

## 🛠️ HERRAMIENTAS Y TECNOLOGÍAS

### Backend
- **Django 4.2.7** - Framework web principal
- **Django REST Framework** - APIs REST
- **Python 3.12** - Lenguaje de programación
- **qrcode** - Generación de códigos QR
- **Pillow** - Procesamiento de imágenes
- **python-decouple** - Gestión de variables de entorno

### Frontend
- **Bootstrap 5.3** - Framework CSS
- **Bootstrap Icons** - Iconografía
- **html5-qrcode** - Escaneo de QR en navegador
- **JavaScript ES6** - Interactividad
- **Fetch API** - Comunicación con backend

### Base de Datos
- **SQLite** - Desarrollo
- **PostgreSQL** - Producción (configurado)

### Control de Versiones
- **Git** - Control de versiones
- **GitHub** - Repositorio remoto
- **Rama:** `tenjo`

---

## 📈 RESULTADOS Y LOGROS

### Funcionalidades Completadas
- ✅ **100%** - Sistema de códigos QR
- ✅ **100%** - Escaneo QR con cámara
- ✅ **100%** - Registro manual
- ✅ **100%** - Estadísticas en tiempo real
- ✅ **100%** - Sistema de alertas de aforo
- ✅ **100%** - Geocercas y validación
- ✅ **100%** - Interfaz de usuario
- ✅ **100%** - Documentación técnica

### Métricas del Código

**Archivos Creados:**
- `control_acceso/utils.py` - 238 líneas
- `README_CONTROL_ACCESO.md` - 400+ líneas
- `.env.example` - 30 líneas
- `poblar_db.py` - 343 líneas

**Archivos Modificados:**
- `control_acceso/views.py` - +280 líneas
- `control_acceso/serializers.py` - +70 líneas
- `usuarios/views.py` - +30 líneas
- `templates/control_acceso.html` - +500 líneas
- `sst_proyecto/settings.py` - +5 líneas

**Total:**
- **Líneas agregadas:** +2,025
- **Líneas eliminadas:** -113
- **Archivos afectados:** 9

### Commit Realizado
```
Commit: df4ddcc5
Rama: tenjo
Mensaje: "Implementar módulo completo de Control de Acceso"
Fecha: Diciembre 2024
```

---

## 🧪 PRUEBAS Y VALIDACIÓN

### Pruebas Realizadas

**1. Generación de Códigos QR**
- ✅ QR único por usuario
- ✅ Información correcta en imagen
- ✅ Escaneo exitoso con dispositivos móviles
- ✅ Descarga en formato PNG

**2. Escaneo de QR**
- ✅ Detección automática ingreso/egreso
- ✅ Validación de códigos inválidos
- ✅ Feedback visual correcto
- ✅ Actualización de estadísticas

**3. Registro Manual**
- ✅ Validación de duplicados
- ✅ Verificación de aforo
- ✅ Registro correcto en base de datos
- ✅ Mensajes de error apropiados

**4. Estadísticas**
- ✅ Cálculos correctos
- ✅ Actualización automática
- ✅ Visualización precisa
- ✅ Performance óptima

**5. Sistema de Alertas**
- ✅ Detección de niveles correcta
- ✅ Bloqueo de ingreso en aforo máximo
- ✅ Mensajes visuales apropiados
- ✅ Configuración dinámica

### Datos de Prueba Creados

**Script:** `poblar_db.py`

**Usuarios creados:**
- 1 Administrador
- 1 Instructor
- 1 Personal de Vigilancia
- 1 Brigada de Emergencias
- 3 Aprendices
- 2 Visitantes

**Configuraciones:**
- 1 Geocerca (Centro Minero SENA Sogamoso)
- 1 Configuración de Aforo (2000 personas)

---

## 📝 DOCUMENTACIÓN GENERADA

### Archivos de Documentación

1. **README_CONTROL_ACCESO.md**
   - Guía completa de uso
   - Documentación de APIs
   - Ejemplos de código
   - Solución de problemas
   - Arquitectura técnica

2. **.env.example**
   - Plantilla de configuración
   - Variables de entorno
   - Ejemplos para producción

3. **Este Informe (INFORME_BITACORA_CONTROL_ACCESO.md)**
   - Bitácora completa del desarrollo
   - Decisiones técnicas
   - Resultados obtenidos

---

## 🔐 SEGURIDAD IMPLEMENTADA

### Validaciones de Seguridad

1. **Autenticación**
   - ✅ Todos los endpoints requieren autenticación
   - ✅ Sistema de tokens REST
   - ✅ Sesiones de Django

2. **Autorización**
   - ✅ Permisos por rol de usuario
   - ✅ Validación de permisos en cada acción
   - ✅ Restricciones según tipo de usuario

3. **Validación de Datos**
   - ✅ Serializers con validación
   - ✅ Validación de tipos de datos
   - ✅ Sanitización de inputs

4. **Protección CSRF**
   - ✅ Tokens CSRF en formularios
   - ✅ Validación en requests POST

---

## 🚧 DESAFÍOS Y SOLUCIONES

### Desafío 1: Problema con el Login
**Problema:** Error "usuario o contraseña incorrectos" al intentar hacer login

**Causa:** Backend de autenticación no configurado en settings.py

**Solución:**
```python
# settings.py
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
```

**Resultado:** Login funcionando correctamente

---

### Desafío 2: Emojis en Windows
**Problema:** UnicodeEncodeError al ejecutar scripts con emojis en Windows

**Causa:** Codificación cp1252 en consola de Windows

**Solución:** Eliminación de emojis en scripts, uso de texto plano

**Resultado:** Scripts ejecutándose sin errores

---

### Desafío 3: Finales de Línea (CRLF vs LF)
**Problema:** Advertencias de Git sobre conversión de finales de línea

**Causa:** Diferencias entre sistemas operativos (Windows vs Linux)

**Solución:** Configuración de Git y normalización de archivos

**Resultado:** Commits limpios sin advertencias críticas

---

## 📅 PRÓXIMOS PASOS

### Módulos Pendientes

1. **Módulo de Emergencias** (Prioridad Alta)
   - Botón de pánico funcional
   - Gestión de emergencias
   - Notificaciones a brigada
   - Protocolos de evacuación

2. **Módulo de Mapas** (Prioridad Media)
   - Visualización con Leaflet
   - Puntos de interés
   - Rutas de evacuación
   - Ubicación en tiempo real

3. **Módulo de Reportes** (Prioridad Media)
   - Generación de PDF
   - Exportación a Excel
   - Gráficos estadísticos
   - Reportes personalizados

4. **Dashboards por Rol** (Prioridad Baja)
   - Personalización según usuario
   - Widgets configurables
   - Accesos rápidos

---

## 💡 CONCLUSIONES

### Logros Principales

1. **Sistema Robusto:** Se implementó un módulo completo de control de acceso con 10 endpoints API funcionales

2. **Tecnología Moderna:** Uso de códigos QR y escaneo en navegador demuestra adopción de tecnologías actuales

3. **Experiencia de Usuario:** Interfaz intuitiva y responsiva que facilita el uso del sistema

4. **Escalabilidad:** Arquitectura preparada para crecimiento futuro del sistema

5. **Documentación:** Documentación técnica completa que facilita mantenimiento

### Impacto del Proyecto

- **Seguridad:** Mejora significativa en el control de acceso al centro
- **Eficiencia:** Reducción de tiempos de registro (QR vs manual)
- **Trazabilidad:** Historial completo de todos los accesos
- **Prevención:** Sistema de alertas previene sobrecupo
- **Monitoreo:** Estadísticas en tiempo real para toma de decisiones

### Aprendizajes

- Integración de tecnologías frontend y backend
- Desarrollo de APIs REST robustas
- Implementación de sistemas de seguridad
- Gestión de geocercas y validación geográfica
- Trabajo con códigos QR en aplicaciones web

---

## 👥 EQUIPO DE DESARROLLO

**Desarrollador Principal:** Equipo SST Centro Minero
**Rama de Trabajo:** `tenjo`
**Repositorio:** https://github.com/Julian110308/proyecto_final_sst
**Framework:** Django 4.2.7
**Versión del Sistema:** 1.0.0

---

**Fecha del Informe:** Diciembre 2024
**Estado del Módulo:** ✅ COMPLETADO Y FUNCIONAL

---

*Este informe ha sido generado como parte de la bitácora de desarrollo del Sistema SST - Centro Minero SENA*
