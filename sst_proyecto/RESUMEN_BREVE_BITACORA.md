# RESUMEN BREVE - BITÁCORA DE DESARROLLO
## Módulo de Control de Acceso - Sistema SST Centro Minero SENA

---

## 1. SISTEMA DE CÓDIGOS QR

Se implementó un sistema de generación automática de códigos QR únicos para cada usuario del centro. Cada código QR incluye información codificada del usuario (ID y número de documento) junto con datos visuales como nombre completo, documento y rol. Se utilizó la librería `qrcode` de Python con nivel de corrección de errores alto, generando imágenes en formato PNG codificadas en base64 para fácil transmisión web. Los usuarios pueden visualizar y descargar su código QR personal desde la interfaz web.

---

## 2. ESCANEO DE CÓDIGOS QR

Se integró un escáner QR funcional directamente en el navegador web usando la librería `html5-qrcode`, que permite usar la cámara del dispositivo móvil o computadora. El sistema implementa lógica inteligente: cuando se escanea un código QR, automáticamente detecta si el usuario está dentro del centro o no, registrando un ingreso si no está presente, o un egreso si ya está dentro. Esto elimina la necesidad de seleccionar manualmente el tipo de registro, agilizando significativamente el proceso de control de acceso.

---

## 3. REGISTRO MANUAL DE ACCESO

Como alternativa al escaneo QR, se desarrolló un sistema de registro manual mediante formularios web. Permite a personal autorizado (vigilancia, administrativo) registrar manualmente ingresos y egresos seleccionando el usuario de una lista, especificando el método de registro (manual, QR o automático) y agregando notas opcionales. El sistema valida automáticamente que no existan ingresos duplicados y que el usuario tenga permisos para registrar salidas solo si tiene un ingreso previo activo.

---

## 4. ESTADÍSTICAS EN TIEMPO REAL

Se creó un dashboard con métricas actualizadas automáticamente cada 30 segundos mediante JavaScript. Muestra cuatro indicadores principales: personas actualmente en el centro, total de ingresos del día, visitantes activos sin salida registrada, y porcentaje de capacidad ocupada. Las estadísticas se calculan en el backend usando consultas optimizadas a la base de datos y se presentan con gráficos visuales, códigos de color según niveles de alerta, y animaciones suaves para mejor experiencia de usuario.

---

## 5. SISTEMA DE ALERTAS DE AFORO

Se implementó un sistema de control de capacidad máxima con tres niveles de alerta: NORMAL (cuando hay espacio disponible), ADVERTENCIA (cuando se acerca al límite configurado), y CRÍTICO (cuando se alcanza el aforo máximo). Cuando el nivel es crítico, el sistema automáticamente bloquea nuevos registros de ingreso, mostrando un mensaje de error. Las alertas se visualizan con banners animados en la interfaz y códigos de color distintivos (verde, amarillo, rojo), permitiendo al personal tomar decisiones informadas sobre el control de acceso.

---

## 6. GEOCERCAS Y VALIDACIÓN DE UBICACIÓN

Se desarrolló un sistema de geocercas (perímetros virtuales) usando la fórmula matemática de Haversine para calcular distancias geográficas. El Centro Minero SENA en Sogamoso está definido con coordenadas específicas (latitud 5.5339, longitud -73.3674) y un radio de 200 metros. Cuando se intenta un registro automático, el sistema valida que las coordenadas GPS del dispositivo estén dentro de este perímetro, rechazando registros que se hagan fuera del área permitida. Esto previene registros fraudulentos desde ubicaciones remotas.

---

## 7. INTERFAZ DE USUARIO

Se diseñó una interfaz web moderna y responsiva usando Bootstrap 5, con paleta de colores institucionales del SENA (tonos verdes). La interfaz incluye un dashboard con tarjetas de estadísticas, tabla de registros recientes con filtros (Todos/Dentro/Salieron), y tres modales interactivos: uno para escanear códigos QR con la cámara, otro para registro manual con formulario, y uno adicional para visualizar y descargar el código QR personal. Todo está optimizado para funcionar correctamente tanto en computadoras de escritorio como en dispositivos móviles.

---

## 8. APIS REST

Se desarrollaron 10 endpoints RESTful completamente funcionales que permiten la integración con aplicaciones móviles o sistemas externos. Los endpoints incluyen operaciones para generar códigos QR, procesar escaneos, registrar ingresos/egresos manualmente, obtener estadísticas en tiempo real, consultar el estado del aforo, validar ubicaciones contra geocercas, y listar registros recientes. Todos los endpoints están protegidos con autenticación y devuelven respuestas en formato JSON estandarizado.

---

## 9. SEGURIDAD

Se implementaron múltiples capas de seguridad: autenticación obligatoria en todos los endpoints mediante tokens REST y sesiones Django, autorización basada en roles de usuario (cada rol tiene permisos específicos), validación exhaustiva de datos usando serializers de Django REST Framework, protección CSRF en formularios web, y sanitización de inputs para prevenir inyección de código. El sistema también registra logs de todos los accesos con ubicación GPS para auditoría.

---

## 10. BASE DE DATOS

Se crearon tres modelos principales: **Geocerca** (almacena perímetros virtuales con coordenadas y radio), **RegistroAcceso** (historial completo de ingresos/egresos con timestamps, ubicación GPS, método usado y usuario), y **ConfiguracionAforo** (configuración dinámica de capacidad máxima y mínima del centro). Estos modelos están optimizados con índices en campos de búsqueda frecuente y relaciones de clave foránea apropiadas para mantener integridad referencial.

---

## 11. DOCUMENTACIÓN

Se generó documentación técnica completa incluyendo: un archivo README con guía de uso del módulo, ejemplos de llamadas a las APIs con código, solución de problemas comunes, descripción de la arquitectura técnica, y este informe de bitácora detallando todo el proceso de desarrollo. La documentación está escrita en formato Markdown para fácil visualización en GitHub y editores de código.

---

## 12. TESTING Y DATOS DE PRUEBA

Se creó un script automatizado (`poblar_db.py`) que genera datos de prueba consistentes: 6 usuarios con diferentes roles (admin, instructor, vigilancia, brigada, aprendices), 2 visitantes, 1 geocerca configurada para el Centro Minero, y 1 configuración de aforo con capacidad de 2000 personas. Todos los usuarios de prueba tienen contraseña estandarizada (`password123`) para facilitar las pruebas durante el desarrollo.

---

## 13. CONTROL DE VERSIONES

Todo el desarrollo se realizó en la rama `tenjo` del repositorio Git, siguiendo buenas prácticas de versionamiento. Se creó un commit consolidado con mensaje descriptivo detallando todos los cambios realizados. El commit incluye 9 archivos (4 nuevos, 5 modificados) con un total de 2,025 líneas agregadas. Los cambios fueron exitosamente subidos al repositorio remoto en GitHub para respaldo y colaboración.

---

## 14. RESULTADOS FINALES

Se completó al 100% el módulo de Control de Acceso con todas las funcionalidades planificadas operativas. El sistema permite registrar accesos mediante tres métodos (QR, manual, automático), monitorear en tiempo real el estado del centro, controlar el aforo máximo, y mantener un historial completo de todos los movimientos. La interfaz es intuitiva y fácil de usar, y las APIs permiten futuras integraciones con aplicaciones móviles nativas.

---

**Total de palabras: ~800**
**Fecha:** Diciembre 2024
**Estado:** ✅ COMPLETADO

---

*Este resumen puede ser copiado directamente a tu bitácora académica*
