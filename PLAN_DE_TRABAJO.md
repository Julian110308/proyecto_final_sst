# Plan de Trabajo - Proyecto SST SENA

## Estado Actual del Proyecto

| Categoría | Estado |
|-----------|--------|
| Funcionalidades Completas | 98% |
| Funcionalidades Parciales | 1% |
| Funcionalidades Pendientes | 1% |

### Progreso Fase 1 (COMPLETADA - Febrero 2026)
- [x] 1.1 Modulo de Equipamiento (Brigada) - Conectado con BD real
- [x] 1.2 Registro de Asistencia (Instructor) - Vista y API implementadas
- [x] 1.3 Sistema de Alertas/Notificaciones - App completa con modelo y API

### Progreso Fase 2 (COMPLETADA - Febrero 2026)
- [x] 2.1 Tablas dinamicas con AJAX - Auto-refresh cada 30s en Vigilancia y Brigada
- [x] 2.2 Indicadores en tiempo real - Aforo cada 15s, equipos cada 60s, badges "EN VIVO"
- [x] 2.3 Boton de activacion de emergencia - Modal completo con formulario y geolocalizacion

### Progreso Fase 3 (COMPLETADA - Febrero 2026)
- [x] 3.1 Servicio centralizado de notificaciones (usuarios/services.py)
- [x] 3.2 Notificacion automatica de emergencias → Brigada y Admin
- [x] 3.3 Notificacion automatica de incidentes → Admin e Instructor
- [x] 3.4 Notificacion de equipos que requieren revision → Brigada
- [x] 3.5 Servicio de verificacion de visitantes que exceden tiempo → Vigilancia
- [x] 3.6 Notificacion de aforo critico → Vigilancia y Admin
- [x] 3.7 Badge de notificaciones en navbar con polling cada 30s
- [x] 3.8 APIs: /api/auth/notificaciones/no_leidas/, marcar_leida/, marcar_todas_leidas/

### Progreso Fase 4 (COMPLETADA - Febrero 2026)
- [x] 4.1 Dashboard Aprendiz: Grafica de asistencia mensual con Chart.js
- [x] 4.1 Dashboard Aprendiz: Widget de contactos de emergencia
- [x] 4.1 Dashboard Aprendiz: Acceso rapido a reportar incidente
- [x] 4.2 Dashboard Instructor: Grafica de asistencia por ficha (barras de progreso)
- [x] 4.2 Dashboard Instructor: Lista de aprendices con estado presente/ausente
- [x] 4.4 Dashboard Vigilancia: Alertas de aforo visual con sonido
- [x] 4.5 Dashboard Brigada: Panel de emergencia con timeline interactivo
- [x] 4.5 Dashboard Brigada: Estadisticas del mes y tiempos de respuesta

### Progreso Fase 5 (COMPLETADA - Febrero 2026)
- [x] 5.2 API /api/auth/estadisticas/dashboard/ - Estadisticas consolidadas
- [x] 5.2 API /api/auth/estadisticas/asistencia-por-ficha/ - Asistencia por ficha
- [x] 5.2 API /api/auth/estadisticas/asistencia-aprendices/ - Lista de aprendices con estado
- [x] 5.2 API /api/emergencias/brigada/mi-disponibilidad/ - Toggle disponibilidad
- [x] 5.2 API /api/emergencias/brigada/estadisticas/ - Stats de brigada
- [x] 5.3 Permisos por accion en EmergenciaViewSet y EstadisticasViewSet

### Progreso Fase 6 (COMPLETADA - Febrero 2026)
- [x] 6.1 Generador de reportes PDF (existente)
- [x] 6.1 Generador de reportes Excel (excel_generator.py con openpyxl)
- [x] 6.1 Generador de reportes CSV (csv_generator.py)
- [x] 6.1 Reporte de aforo diario/semanal/mensual
- [x] 6.1 Reporte de incidentes por periodo
- [x] 6.1 Reporte de asistencia por programa/ficha
- [x] 6.1 Reporte de seguridad y emergencias
- [x] 6.2 Endpoint /reportes/api/aforo/?formato=pdf|excel|csv|json
- [x] 6.2 Endpoint /reportes/api/incidentes/?formato=pdf|excel|csv|json
- [x] 6.2 Endpoint /reportes/api/asistencia/?formato=pdf|excel|csv|json
- [x] 6.2 Endpoint /reportes/api/seguridad/?formato=pdf|excel|csv|json
- [x] 6.3 Comando manage.py generar_reportes para cron
- [x] 6.3 Tareas Celery para reportes programados (tasks.py)
- [x] 6.3 Vista frontend para generar/descargar reportes (index.html actualizado)

---

## FASE 1: Corrección de Funcionalidades Críticas
**Prioridad: ALTA | Impacto: Todos los roles**

### 1.1 Completar Módulo de Equipamiento (Brigada)
- [ ] Crear vista `equipos_brigada_view` que consuma datos reales de `EquipamientoSeguridad`
- [ ] Implementar API `/api/brigada/equipos/` para CRUD de equipamiento
- [ ] Agregar funcionalidad para actualizar estado de equipos
- [ ] Implementar alertas de equipos próximos a revisión

**Archivos a modificar:**
- `sst_proyecto/urls.py` (línea 328)
- `mapas/views.py` o crear `brigada/views.py`
- `templates/dashboard/brigada/equipos.html`

### 1.2 Implementar Registro de Asistencia (Instructor)
- [ ] Crear vista `registrar_asistencia_view`
- [ ] Implementar API `/api/instructor/registrar-asistencia/`
- [ ] Agregar lógica AJAX para guardar asistencia sin recargar página
- [ ] Conectar con modelo `RegistroAcceso` o crear modelo `Asistencia`

**Archivos a crear/modificar:**
- `usuarios/views.py` - Nueva vista
- `sst_proyecto/urls.py` - Nueva URL
- `templates/dashboard/instructor/registrar_asistencia.html`

### 1.3 Completar Sistema de Alertas (Aprendiz)
- [ ] Crear modelo `Notificacion` centralizado
- [ ] Implementar API `/api/notificaciones/`
- [ ] Conectar template `mis_alertas.html` con datos reales
- [ ] Implementar WebSocket o polling para alertas en tiempo real

**Archivos a crear:**
- `notificaciones/models.py`
- `notificaciones/views.py`
- `notificaciones/serializers.py`

---

## FASE 2: Integración de Datos en Tiempo Real (COMPLETADA)
**Prioridad: ALTA | Impacto: Vigilancia, Brigada, Admin**

### 2.1 Tablas Dinámicas con AJAX
- [x] Tabla de accesos recientes (Vigilancia) - conectar con API existente
- [x] Tabla de emergencias activas (Brigada) - conectar con API existente
- [x] Tabla de visitantes activos (Vigilancia) - conectar con API existente
- [x] Actualización automática cada 30 segundos
- [x] Auto-refresh inteligente (se detiene cuando la pagina no es visible)

**Archivos modificados:**
- `templates/dashboard/vigilancia.html` - Auto-refresh con setInterval
- `templates/dashboard/brigada.html` - Auto-refresh con setInterval
- `emergencias/serializers.py` - Campos adicionales tipo_nombre, usuario_nombre

### 2.2 Indicadores en Tiempo Real
- [x] Contador de aforo actualizado cada 15 segundos
- [x] Estado de emergencia global (card dinamico)
- [x] Disponibilidad de brigadistas (lista dinamica)
- [x] Estado de equipos por tipo (barras de progreso dinamicas)
- [x] Indicador de ultima actualizacion en header
- [x] Badges "EN VIVO" en secciones criticas

### 2.3 Botón de Activación de Emergencia
- [x] Modal completo con formulario de emergencia
- [x] Seleccion de tipo de emergencia desde API
- [x] Captura de geolocalizacion automatica
- [x] Campos: descripcion, ubicacion, personas afectadas, requiere evacuacion
- [x] Usa endpoint existente `/api/emergencias/emergencias/`
- [x] Notifica a brigada automaticamente via modelo NotificacionEmergencia

---

## FASE 3: Sistema de Notificaciones Centralizado (COMPLETADA)
**Prioridad: MEDIA | Impacto: Todos los roles**

### 3.1 Modulo de Notificaciones (integrado en app usuarios)
```
usuarios/
├── models.py      # Modelo Notificacion con tipos y prioridades
├── views.py       # NotificacionViewSet (CRUD, no_leidas, marcar_leida)
├── serializers.py # NotificacionSerializer con tiempo_transcurrido
└── services.py    # NotificacionService - Logica centralizada de envio
```

### 3.2 Tipos de Notificaciones Implementados
- [x] Emergencia reportada → Brigada, Admin (emergencias/views.py)
- [x] Incidente critico → Admin, Instructor (reportes/views_incidentes.py)
- [x] Aprendiz sin registro de acceso → Instructor (servicio disponible)
- [x] Equipo requiere revision → Brigada (mapas/views.py)
- [x] Visitante excede tiempo → Vigilancia (servicio disponible para cron)
- [x] Aforo critico → Vigilancia, Admin (control_acceso/views.py)

### 3.3 Canales de Notificación
- [x] In-app (badge en navbar con polling cada 30s)
- [ ] Email (opcional, configurar SMTP)
- [ ] Push notification (futuro - PWA)

---

## FASE 4: Mejoras de Dashboard por Rol (EN PROGRESO)
**Prioridad: MEDIA | Impacto: UX de cada rol**

### 4.1 Dashboard Aprendiz
- [x] Agregar gráfica de asistencia mensual (Chart.js)
- [ ] Mostrar próximas capacitaciones SST
- [x] Widget de contactos de emergencia
- [x] Acceso rápido a reportar incidente

### 4.2 Dashboard Instructor
- [x] Gráfica de asistencia por ficha (barras de progreso dinamicas)
- [x] Lista de aprendices con estado (presente/ausente hoy)
- [ ] Alertas de aprendices con inasistencias frecuentes
- [ ] Exportar lista de asistencia a Excel

### 4.3 Dashboard Administrativo
- [ ] Panel de estadísticas globales
- [ ] Gráficas de tendencias (incidentes, accesos, emergencias)
- [ ] Reportes automatizados
- [ ] Configuración completa del sistema

### 4.4 Dashboard Vigilancia
- [x] Mapa con personas en tiempo real (markers por rol)
- [x] Alertas de aforo (visual + sonido al superar 90%)
- [x] Registro rápido de visitantes (tabla con acciones)
- [x] Historial de accesos con auto-refresh

### 4.5 Dashboard Brigada
- [x] Panel de emergencia con timeline interactivo
- [x] Timeline con filtros (todas/activas/resueltas)
- [x] Acciones rapidas (Atender/Resolver) desde timeline
- [x] Estadisticas del mes (activas, resueltas, tasa resolucion)
- [x] Tiempos de respuesta (promedio, mejor, meta)
- [ ] Checklist de equipos por zona
- [ ] Comunicación entre brigadistas

---

## FASE 5: APIs y Backend Pendientes (EN PROGRESO)
**Prioridad: MEDIA | Impacto: Escalabilidad**

### 5.1 Reactivar Funcionalidad QR (Opcional)
- [ ] Descomentar métodos `generar_qr()` y `mi_qr()` en `usuarios/views.py`
- [ ] Descomentar `escanear_qr()` en `control_acceso/views.py`
- [ ] Implementar lector QR con cámara (JavaScript)
- [ ] Validar QR y registrar acceso automático

### 5.2 APIs Faltantes
- [x] `GET /api/auth/estadisticas/dashboard/` - Estadísticas consolidadas
- [x] `GET /api/auth/estadisticas/asistencia-por-ficha/` - Asistencia por ficha
- [x] `GET /api/auth/estadisticas/asistencia-aprendices/` - Lista aprendices con estado
- [x] `POST /api/emergencias/brigada/mi-disponibilidad/` - Toggle disponibilidad
- [x] `GET /api/emergencias/brigada/estadisticas/` - Estadísticas de brigada
- [ ] `GET /api/reportes/exportar/{formato}/` - Exportar a PDF/Excel

### 5.3 Validaciones y Seguridad
- [x] Permisos específicos por acción en EstadisticasViewSet
- [x] Permisos específicos por acción en EmergenciaViewSet
- [x] Clases de permisos: EsBrigadaOAdministrativo, EsVigilanciaOAdministrativo
- [ ] Sanitizar inputs en formularios
- [ ] Rate limiting en APIs críticas
- [ ] Logs de auditoría para acciones sensibles

---

## FASE 6: Reportes y Exportación (COMPLETADA)
**Prioridad: BAJA | Impacto: Admin, Instructor**

### 6.1 Generación de Reportes
- [x] Reporte de aforo diario/semanal/mensual
- [x] Reporte de incidentes por período
- [x] Reporte de asistencia por programa/ficha
- [x] Reporte de emergencias y tiempos de respuesta

### 6.2 Formatos de Exportación
- [x] PDF con ReportLab (existente, mejorado)
- [x] Excel con openpyxl (nuevo: excel_generator.py)
- [x] CSV para datos crudos (nuevo: csv_generator.py)

### 6.3 Programación de Reportes
- [x] Usar modelo `ConfiguracionReporte` existente
- [x] Implementar Celery para tareas programadas (tasks.py)
- [x] Comando manage.py generar_reportes para cron
- [x] Envío automático por email (configurado en tasks.py)

---

## FASE 7: Optimización y Escalabilidad
**Prioridad: BAJA | Impacto: Rendimiento**

### 7.1 Base de Datos
- [ ] Agregar índices en campos frecuentemente consultados
- [ ] Optimizar queries con `select_related` y `prefetch_related`
- [ ] Implementar paginación en listados grandes

### 7.2 Caché
- [ ] Cachear estadísticas del dashboard (Redis)
- [ ] Cachear configuración de aforo
- [ ] Invalidar caché en cambios relevantes

### 7.3 Frontend
- [ ] Minificar CSS/JS
- [ ] Lazy loading de imágenes
- [ ] Compresión de respuestas (gzip)

---

## FASE 8: Funcionalidades Futuras
**Prioridad: FUTURA | Impacto: Expansión**

### 8.1 App Móvil / PWA
- [ ] Convertir a Progressive Web App
- [ ] Notificaciones push
- [ ] Modo offline básico

### 8.2 Integración Externa
- [ ] API de SENA para validar documentos
- [ ] Integración con bomberos/ambulancia
- [ ] Sistema de cámaras (CCTV)

### 8.3 Machine Learning
- [ ] Predicción de incidentes por patrones
- [ ] Detección de anomalías en accesos
- [ ] Optimización de rutas de evacuación

---

## Cronograma Sugerido

| Fase | Descripción | Dependencias |
|------|-------------|--------------|
| **1** | Corrección Funcionalidades Críticas | Ninguna |
| **2** | Integración Tiempo Real | Fase 1 |
| **3** | Sistema Notificaciones | Fase 1, 2 |
| **4** | Mejoras Dashboard | Fase 1, 2, 3 |
| **5** | APIs Backend | Fase 1 |
| **6** | Reportes y Exportación | Fase 4, 5 |
| **7** | Optimización | Fase 1-6 |
| **8** | Funcionalidades Futuras | Fase 1-7 |

---

## Resumen de Archivos a Crear

```
sst_proyecto/
├── notificaciones/           # NUEVA APP
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   └── services.py
│
├── templates/
│   ├── components/           # WIDGETS REUTILIZABLES
│   │   ├── widget_aforo.html
│   │   ├── widget_accesos.html
│   │   ├── widget_emergencias.html
│   │   └── widget_mapa_mini.html
│   │
│   └── notificaciones/
│       └── lista.html
│
└── static/
    └── js/
        ├── realtime.js       # Actualización en tiempo real
        ├── emergencia.js     # Activación de emergencia
        └── notificaciones.js # Manejo de notificaciones
```

---

## Resumen de APIs a Crear

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/notificaciones/` | GET | Listar notificaciones del usuario |
| `/api/notificaciones/{id}/leer/` | POST | Marcar como leída |
| `/api/brigada/equipos/` | GET, PUT | CRUD equipamiento |
| `/api/brigada/disponibilidad/` | POST | Toggle disponibilidad |
| `/api/emergencias/activar/` | POST | Activar emergencia |
| `/api/instructor/asistencia/` | GET, POST | Gestión asistencia |
| `/api/estadisticas/global/` | GET | Estadísticas consolidadas |
| `/api/reportes/exportar/` | GET | Generar reporte |

---

## Notas Importantes

1. **Priorizar Fase 1 y 2** - Son las que tienen mayor impacto en la usabilidad
2. **Mantener compatibilidad** - No romper funcionalidades existentes
3. **Documentar cambios** - Actualizar este plan conforme se avance
4. **Testing** - Crear tests para cada nueva funcionalidad
5. **Git** - Hacer commits pequeños y descriptivos por cada tarea completada

---

*Última actualización: Febrero 2026*
