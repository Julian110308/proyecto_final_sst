# Configuración de Email para Recuperación de Contraseña

## Sistema SST - Centro Minero SENA

---

## 📧 Configuración de Gmail

Para que el sistema pueda enviar correos de recuperación de contraseña, necesitas configurar una cuenta de Gmail con una **Contraseña de Aplicación**.

### Paso 1: Habilitar Verificación en 2 Pasos

1. Ve a tu cuenta de Gmail: https://myaccount.google.com/
2. En el menú lateral, selecciona **"Seguridad"**
3. Busca la sección **"Verificación en 2 pasos"**
4. Haz clic en **"Comenzar"** y sigue los pasos para activarla

### Paso 2: Generar Contraseña de Aplicación

1. Una vez activada la verificación en 2 pasos, vuelve a **Seguridad**
2. Busca la opción **"Contraseñas de aplicaciones"**
3. Selecciona:
   - **Aplicación:** Correo
   - **Dispositivo:** Otro (nombre personalizado)
   - Escribe: "Sistema SST SENA"
4. Haz clic en **"Generar"**
5. **IMPORTANTE:** Copia la contraseña de 16 caracteres que aparece

### Paso 3: Configurar el Archivo .env

1. Abre el archivo `.env` en la carpeta `sst_proyecto/`
2. Busca la sección de configuración de email
3. Actualiza con tus datos:

```env
# Configuración de Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
DEFAULT_FROM_EMAIL=SST Centro Minero <tu_email@gmail.com>
```

**Ejemplo:**
```env
EMAIL_HOST_USER=sst.centrominero@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=SST Centro Minero <sst.centrominero@gmail.com>
```

### Paso 4: Verificar Configuración

1. Guarda el archivo `.env`
2. Reinicia el servidor Django:
   ```bash
   python manage.py runserver
   ```

---

## 🧪 Probar Recuperación de Contraseña

### Desde el Navegador:

1. Ve a: `http://localhost:8000/accounts/login/`
2. Haz clic en **"¿Olvidaste tu contraseña?"**
3. Ingresa un correo electrónico de prueba
4. Revisa el correo (incluyendo spam)
5. Haz clic en el enlace recibido
6. Ingresa tu nueva contraseña

### Desde la Consola (Solo para Desarrollo):

Si quieres probar sin configurar Gmail, puedes usar el backend de consola:

En `settings.py`, cambia temporalmente:
```python
# Para pruebas de desarrollo (emails se muestran en consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Con esto, los emails se mostrarán en la terminal donde corre Django.

---

## 🔒 Seguridad

### Buenas Prácticas:

1. **Nunca compartas la contraseña de aplicación**
2. **No subas el archivo .env a Git** (ya está en .gitignore)
3. **Usa un email específico para el sistema** (recomendado)
4. **Revoca contraseñas de aplicación** si sospechas compromiso

### Emails Recomendados:

- ✅ `sst.centrominero@gmail.com`
- ✅ `notificaciones.sena@gmail.com`
- ✅ `sistema.sst@gmail.com`
- ❌ Tu email personal

---

## ⚙️ Otras Opciones de Configuración

### Usar Otro Servidor SMTP:

Si no quieres usar Gmail, puedes usar otros servicios:

#### Outlook/Hotmail:
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@outlook.com
EMAIL_HOST_PASSWORD=tu_contraseña
```

#### SendGrid (Profesional):
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=tu_api_key_de_sendgrid
```

#### Mailgun (Profesional):
```env
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@tu-dominio.mailgun.org
EMAIL_HOST_PASSWORD=tu_contraseña_mailgun
```

---

## 🐛 Solución de Problemas

### Error: "SMTPAuthenticationError"
**Causa:** Usuario o contraseña incorrectos
**Solución:**
- Verifica que el email sea correcto
- Asegúrate de usar la contraseña de aplicación, no tu contraseña de Gmail
- Genera una nueva contraseña de aplicación

### Error: "SMTPServerDisconnected"
**Causa:** Problema de conexión con Gmail
**Solución:**
- Verifica tu conexión a internet
- Comprueba que el puerto 587 no esté bloqueado por firewall
- Intenta con `EMAIL_PORT=465` y `EMAIL_USE_SSL=True`

### El correo no llega
**Posibles causas:**
1. El email fue a la carpeta de spam
2. El email del usuario no existe en la base de datos
3. Hay un error en la configuración SMTP

**Soluciones:**
1. Revisa la carpeta de spam
2. Verifica que el usuario tenga email registrado:
   ```python
   python manage.py shell
   >>> from usuarios.models import Usuario
   >>> Usuario.objects.filter(email='correo@ejemplo.com').exists()
   ```
3. Revisa los logs del servidor Django

### El enlace expiró
**Causa:** El enlace de recuperación tiene 1 hora de validez
**Solución:**
- Solicita un nuevo enlace de recuperación
- En `settings.py`, puedes cambiar el tiempo:
  ```python
  PASSWORD_RESET_TIMEOUT = 3600  # 1 hora (en segundos)
  ```

---

## 📝 Verificación Rápida

### Checklist de Configuración:

- [ ] Verificación en 2 pasos activada en Gmail
- [ ] Contraseña de aplicación generada
- [ ] Archivo `.env` actualizado con email y contraseña
- [ ] Servidor Django reiniciado
- [ ] Prueba de envío realizada
- [ ] Email recibido correctamente

---

## 💡 Consejos Adicionales

### Para Desarrollo:
```python
# settings.py (solo desarrollo)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```
Los emails se mostrarán en la consola.

### Para Pruebas:
```python
# settings.py (archivo temporal)
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'emails'
```
Los emails se guardarán en archivos.

### Para Producción:
```python
# settings.py (producción)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# + configuración SMTP real
```

---

## 🎯 Resultado Final

Una vez configurado correctamente:

1. ✅ Los usuarios pueden hacer clic en "¿Olvidaste tu contraseña?"
2. ✅ Reciben un email con enlace de recuperación
3. ✅ El enlace los dirige a un formulario para crear nueva contraseña
4. ✅ La contraseña se actualiza exitosamente
5. ✅ Pueden iniciar sesión con la nueva contraseña

---

## 📞 Soporte

Si tienes problemas con la configuración, verifica:
- Los logs del servidor Django
- La consola donde corre `python manage.py runserver`
- El archivo `settings.py` tenga la configuración correcta

**Nota:** En desarrollo, puedes usar el backend de consola para ver los emails sin necesidad de configurar Gmail.
