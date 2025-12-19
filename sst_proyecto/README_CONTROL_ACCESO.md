# Módulo de Control de Acceso - Sistema SST Centro Minero SENA

## ✅ Estado de Implementación

El módulo de **Control de Acceso** ha sido completamente implementado con las siguientes características:

### Funcionalidades Implementadas

#### 1. **Generación de Códigos QR**
- ✅ Generación automática de códigos QR únicos para cada usuario
- ✅ Códigos QR personalizados con información del usuario (nombre, documento, rol)
- ✅ Descarga de códigos QR en formato PNG
- ✅ Endpoint API: `/api/auth/usuarios/mi_qr/` - Ver mi código QR
- ✅ Endpoint API: `/api/auth/usuarios/{id}/generar_qr/` - Generar QR de cualquier usuario

#### 2. **Escaneo de Códigos QR**
- ✅ Escáner QR integrado en la interfaz web usando la cámara
- ✅ Detección automática de ingreso/egreso
- ✅ Procesamiento inteligente: si el usuario está dentro, registra salida; si no, registra ingreso
- ✅ Endpoint API: `/api/acceso/registros/escanear_qr/`

#### 3. **Registro Manual de Acceso**
- ✅ Formulario para registro manual de ingresos
- ✅ Formulario para registro manual de egresos
- ✅ Selección de usuarios desde dropdown
- ✅ Endpoint API: `/api/acceso/registros/registrar_ingreso/`
- ✅ Endpoint API: `/api/acceso/registros/registrar_egreso/`

#### 4. **Estadísticas en Tiempo Real**
- ✅ Personas actualmente en el centro
- ✅ Total de ingresos del día
- ✅ Visitantes activos (sin salida registrada)
- ✅ Porcentaje de aforo actual con barra de progreso
- ✅ Actualización automática cada 30 segundos
- ✅ Endpoint API: `/api/acceso/registros/estadisticas/`

#### 5. **Sistema de Alertas de Aforo**
- ✅ Configuración de aforo máximo y mínimo
- ✅ Alerta visual cuando se acerca al límite (nivel ADVERTENCIA)
- ✅ Alerta crítica cuando se alcanza el máximo (nivel CRÍTICO)
- ✅ Animación de parpadeo en alertas críticas
- ✅ Bloqueo de nuevos ingresos cuando se alcanza aforo máximo
- ✅ Endpoint API: `/api/acceso/config-aforo/aforo_actual/`

#### 6. **Historial de Registros**
- ✅ Tabla con registros recientes (últimos 50)
- ✅ Filtros: Todos, Dentro, Salieron
- ✅ Información detallada: usuario, rol, hora ingreso/egreso, método, estado
- ✅ Indicadores visuales de estado (DENTRO/SALIÓ)
- ✅ Endpoint API: `/api/acceso/registros/registros_recientes/`

#### 7. **Geocercas (Perímetro Virtual)**
- ✅ Sistema de geocercas para validar ubicación
- ✅ Fórmula de Haversine para calcular distancias
- ✅ Validación de ubicación en registros automáticos
- ✅ Endpoint API: `/api/acceso/geocercas/`
- ✅ Endpoint API: `/api/acceso/geocercas/{id}/verificar_ubicacion/`

---

## 🚀 Cómo Usar el Módulo

### 1. Iniciar el Servidor

```bash
cd "c:\Users\as\Desktop\Proyecto sst\proyecto_final_sst\sst_proyecto"
python manage.py runserver
```

### 2. Acceder al Sistema

Abre tu navegador en: `http://localhost:8000`

**Credenciales de acceso:**
- Usuario: `admin`
- Contraseña: `admin123`

### 3. Navegar al Módulo

Desde el dashboard, haz clic en **"Control Acceso"** en el menú lateral o visita directamente:
```
http://localhost:8000/acceso/
```

---

## 📱 Funcionalidades Principales

### A. Ver Mi Código QR

1. En la página de Control de Acceso, haz clic en el botón **"Mi Código QR"**
2. Se mostrará tu código QR personalizado
3. Puedes descargarlo haciendo clic en **"Descargar QR"**

**API:**
```bash
GET /api/auth/usuarios/mi_qr/
```

**Respuesta:**
```json
{
  "usuario_id": 1,
  "nombre": "Administrador Sistema",
  "documento": "1234567890",
  "rol": "Administrativo",
  "qr_image": "base64_encoded_image..."
}
```

### B. Escanear Código QR

1. Haz clic en **"Escanear QR"**
2. Permite el acceso a la cámara cuando el navegador lo solicite
3. Coloca el código QR frente a la cámara
4. El sistema automáticamente:
   - Registra **ingreso** si la persona no está dentro
   - Registra **egreso** si la persona ya está dentro
5. Verás una confirmación visual del registro

**API:**
```bash
POST /api/acceso/registros/escanear_qr/
Content-Type: application/json

{
  "codigo_qr": "SST-USUARIO-1-1234567890",
  "latitud": 5.5339,
  "longitud": -73.3674
}
```

**Respuesta (Ingreso):**
```json
{
  "success": true,
  "tipo": "INGRESO",
  "mensaje": "Ingreso registrado - Administrador Sistema",
  "usuario": {
    "nombre": "Administrador Sistema",
    "documento": "1234567890",
    "rol": "Administrativo"
  },
  "aforo": {
    "personas_dentro": 1,
    "aforo_maximo": 2000,
    "porcentaje": 0.05,
    "alerta": "NORMAL"
  }
}
```

### C. Registro Manual

1. Haz clic en **"Registro Manual"**
2. Selecciona el tipo: **Ingreso** o **Egreso**
3. Busca y selecciona el usuario
4. Selecciona el método: Manual, QR, Automático
5. Haz clic en **"Registrar"**

**API - Registrar Ingreso:**
```bash
POST /api/acceso/registros/registrar_ingreso/
Content-Type: application/json

{
  "usuario_id": 1,
  "latitud": 5.5339,
  "longitud": -73.3674,
  "metodo": "MANUAL"
}
```

**API - Registrar Egreso:**
```bash
POST /api/acceso/registros/registrar_egreso/
Content-Type: application/json

{
  "usuario_id": 1,
  "latitud": 5.5339,
  "longitud": -73.3674,
  "metodo": "MANUAL"
}
```

### D. Ver Estadísticas

Las estadísticas se actualizan automáticamente cada 30 segundos y muestran:

- **Personas en Centro**: Cuántas personas están actualmente dentro
- **Ingresos Hoy**: Total de ingresos registrados hoy
- **Visitantes Activos**: Visitantes que no han registrado salida
- **Capacidad**: Porcentaje de aforo actual con indicador visual

**API:**
```bash
GET /api/acceso/registros/estadisticas/
```

**Respuesta:**
```json
{
  "ingresos_hoy": 15,
  "personas_dentro": 8,
  "visitantes_activos": 2,
  "aforo": {
    "personas_dentro": 8,
    "aforo_maximo": 2000,
    "aforo_minimo": 1800,
    "porcentaje": 0.4,
    "alerta": "NORMAL",
    "mensaje": ""
  }
}
```

### E. Configurar Aforo

**API:**
```bash
GET /api/acceso/config-aforo/
POST /api/acceso/config-aforo/
PUT /api/acceso/config-aforo/{id}/
```

**Datos de Configuración:**
```json
{
  "aforo_maximo": 2000,
  "aforo_minimo": 1800,
  "mensaje_alerta": "Se está alcanzando el aforo máximo del centro",
  "activo": true
}
```

---

## 🔒 Seguridad y Validaciones

### Validaciones Implementadas

1. **Duplicados de Ingreso**: No se permite registrar ingreso si el usuario ya está dentro
2. **Validación de Egreso**: Solo se puede registrar egreso si hay un ingreso activo
3. **Aforo Máximo**: Se bloquea el registro de nuevos ingresos cuando se alcanza el aforo máximo
4. **Geocerca**: En modo automático, se valida que la ubicación esté dentro del perímetro del centro
5. **Autenticación**: Todas las operaciones requieren autenticación

### Permisos por Rol

- **ADMINISTRATIVO**: Acceso completo a todo
- **VIGILANCIA**: Puede registrar accesos, ver estadísticas
- **INSTRUCTOR**: Puede ver estadísticas y registros de sus aprendices
- **BRIGADA**: Acceso limitado según necesidades de emergencia
- **APRENDIZ**: Solo puede ver su propio código QR
- **VISITANTE**: Sin acceso al módulo

---

## 📊 Arquitectura del Módulo

### Modelos

1. **Geocerca**: Define el perímetro virtual del centro
2. **RegistroAcceso**: Almacena ingresos y egresos
3. **ConfiguracionAforo**: Configuración de capacidad máxima

### Utilidades (utils.py)

- `generar_qr_usuario()`: Genera código QR para usuarios
- `generar_qr_visitante()`: Genera código QR para visitantes
- `decodificar_qr()`: Decodifica un código QR
- `verificar_aforo_actual()`: Verifica el estado del aforo
- `obtener_estadisticas_hoy()`: Obtiene estadísticas del día

### Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/auth/usuarios/mi_qr/` | Ver mi código QR |
| GET | `/api/auth/usuarios/{id}/generar_qr/` | Generar QR de usuario |
| POST | `/api/acceso/registros/escanear_qr/` | Escanear código QR |
| POST | `/api/acceso/registros/registrar_ingreso/` | Registrar ingreso manual |
| POST | `/api/acceso/registros/registrar_egreso/` | Registrar egreso manual |
| GET | `/api/acceso/registros/estadisticas/` | Obtener estadísticas |
| GET | `/api/acceso/registros/registros_recientes/` | Listar registros recientes |
| GET | `/api/acceso/config-aforo/aforo_actual/` | Estado actual del aforo |
| GET | `/api/acceso/geocercas/` | Listar geocercas |

---

## 🎨 Interfaz Web

La interfaz incluye:

- **Dashboard de Estadísticas**: 4 tarjetas con métricas en tiempo real
- **Alerta de Aforo**: Banner visible cuando se acerca al límite
- **Tabla de Registros**: Historial con filtros (Todos/Dentro/Salieron)
- **Modal de Escaneo QR**: Escáner integrado con la cámara
- **Modal de Registro Manual**: Formulario para registros manuales
- **Modal Mi QR**: Visualización y descarga del código QR personal

---

## 🧪 Próximos Pasos

Una vez que termines de probar este módulo, puedes continuar con:

1. **Módulo de Emergencias** - Gestión de emergencias y botón de pánico
2. **Módulo de Mapas** - Visualización geoespacial del centro con Leaflet
3. **Módulo de Reportes** - Generación de reportes en PDF/Excel

---

## 📝 Notas Técnicas

- Se requiere **qrcode** y **Pillow** instalados (ya incluidos)
- La librería **html5-qrcode** se carga desde CDN para el escáner web
- El sistema usa **Haversine** para calcular distancias geográficas
- Actualización automática vía **JavaScript Fetch API** cada 30 segundos
- Compatible con dispositivos móviles (responsive design)

---

## 🐛 Solución de Problemas

### La cámara no funciona
- Asegúrate de estar usando **HTTPS** o **localhost**
- Permite el acceso a la cámara cuando el navegador lo solicite
- Verifica que tu navegador soporte getUserMedia()

### Error al generar QR
- Verifica que **qrcode** y **Pillow** estén instalados
- Ejecuta: `pip install qrcode[pil] pillow`

### Las estadísticas no se actualizan
- Revisa la consola del navegador (F12) para ver errores
- Verifica que el servidor esté corriendo
- Comprueba que las URLs de API sean correctas

---

**¡Módulo de Control de Acceso completamente funcional!** 🎉
