# Guía de Prueba - Recuperación de Contraseña

## Sistema SST - Centro Minero SENA

---

## ✅ SISTEMA LISTO PARA PROBAR

El sistema está configurado en **MODO DESARROLLO**. Los emails se mostrarán en la consola del servidor, no necesitas configurar Gmail.

---

## 🧪 PASOS PARA PROBAR

### 1. Asegúrate que el servidor esté corriendo

```bash
python manage.py runserver
```

Deberías ver este mensaje en la consola:
```
======================================================================
MODO DESARROLLO: Emails se mostraran en la consola
Para usar Gmail, configura EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en .env
======================================================================
```

### 2. Abre el navegador

Ve a: **http://localhost:8000/accounts/login/**

### 3. Haz clic en "¿Olvidaste tu contraseña?"

Te llevará a: `http://localhost:8000/accounts/password-reset/`

### 4. Ingresa un email de prueba

Usa cualquiera de estos emails de usuarios existentes:

- `admin@sena.edu.co` (Usuario: admin)
- `julian@gmail.com` (Usuario: julian - Aprendiz)
- `dario@gmail.com` (Usuario: dario - Brigada)
- `kebintenjo@gmail.com` (Usuario: Tenjo - Administrativo)

### 5. Haz clic en "Enviar Instrucciones"

Verás una pantalla de confirmación.

### 6. IMPORTANTE: Revisa la CONSOLA del servidor

En la terminal donde corre Django, verás algo como esto:

```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 8bit
Subject: =?utf-8?b?UmVjdXBlcmFjacOzbiBkZSBDb250cmFzZcOxYSAtIFNpc3RlbWEgU1NU?=
 =?utf-8?b?IENlbnRybyBNaW5lcm8gU0VOQQ==?=
From: SST Centro Minero <noreply@centrominerosst.com>
To: admin@sena.edu.co
Date: ...
Message-ID: ...
-------------------------------------------------------------------------------

Recuperación de Contraseña
Sistema SST - Centro Minero SENA

Hola,

Recibimos una solicitud para restablecer la contraseña de tu cuenta...

ENLACE: http://localhost:8000/accounts/reset/MQ/c5q8mo-...

...
```

### 7. Copia el enlace de la consola

Busca la línea que dice algo como:
```
http://localhost:8000/accounts/reset/MQ/c5q8mo-abc123...
```

### 8. Pega el enlace en el navegador

Te llevará al formulario de nueva contraseña.

### 9. Ingresa una nueva contraseña

Requisitos:
- Mínimo 8 caracteres
- No puede ser completamente numérica
- No puede ser muy común

Ejemplos válidos:
- `NuevaPass123`
- `Admin2024!`
- `Segura123`

### 10. Confirma la contraseña

Ingresa la misma contraseña dos veces.

### 11. Haz clic en "Restablecer Contraseña"

Verás una pantalla de éxito con redirección automática en 5 segundos.

### 12. Inicia sesión con la nueva contraseña

Usa tu usuario y la nueva contraseña que acabas de crear.

---

## 📊 USUARIOS DE PRUEBA

| Usuario | Email | Rol | Contraseña Actual |
|---------|-------|-----|-------------------|
| admin | admin@sena.edu.co | Administrativo | admin123 |
| julian | julian@gmail.com | Aprendiz | password123 |
| dario | dario@gmail.com | Brigada | password123 |
| Tenjo | kebintenjo@gmail.com | Administrativo | password123 |
| kevin | tenjo@gmail.com | Aprendiz | password123 |

---

## ✅ CHECKLIST DE PRUEBA

- [ ] Servidor corriendo y mostrando "MODO DESARROLLO"
- [ ] Login funciona normalmente
- [ ] Enlace "¿Olvidaste tu contraseña?" visible
- [ ] Formulario de recuperación se muestra
- [ ] Ingreso email y envío exitoso
- [ ] Email aparece en la consola del servidor
- [ ] Copiado enlace de recuperación
- [ ] Formulario de nueva contraseña se muestra
- [ ] Contraseña cambiada exitosamente
- [ ] Login funciona con nueva contraseña

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### No veo el email en la consola

**Problema:** El servidor no muestra el email
**Solución:**
1. Verifica que el mensaje "MODO DESARROLLO" aparezca al iniciar
2. Asegúrate de estar mirando la consola correcta
3. El email aparece inmediatamente después de hacer clic en "Enviar"

### El enlace no funciona

**Problema:** "Enlace inválido" al hacer clic
**Solución:**
1. Asegúrate de copiar el enlace COMPLETO
2. El enlace expira en 1 hora
3. Solo se puede usar UNA VEZ

### Error al cambiar contraseña

**Problema:** "Las contraseñas no coinciden" o similar
**Solución:**
1. Verifica que ambas contraseñas sean idénticas
2. Asegúrate de cumplir los requisitos mínimos
3. Evita contraseñas muy comunes como "12345678"

### No puedo iniciar sesión después

**Problema:** La nueva contraseña no funciona
**Solución:**
1. Verifica que viste el mensaje de éxito
2. Intenta resetear de nuevo
3. Revisa la consola del servidor por errores

---

## 🚀 CONFIGURAR GMAIL PARA PRODUCCIÓN

Cuando quieras usar envío real de emails:

1. **Obtén una contraseña de aplicación de Gmail:**
   - Ve a: https://myaccount.google.com/security
   - Activa verificación en 2 pasos
   - Ve a "Contraseñas de aplicaciones"
   - Genera una para "Correo"

2. **Edita el archivo .env:**
   ```env
   EMAIL_HOST_USER=tu_email@gmail.com
   EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx
   ```

3. **Reinicia el servidor:**
   ```bash
   python manage.py runserver
   ```

4. **Verifica el mensaje:**
   Deberías ver:
   ```
   SMTP configurado correctamente: tu_email@gmail.com
   ```

---

## 📝 NOTAS IMPORTANTES

1. **MODO DESARROLLO**: Los emails solo se muestran en consola, no se envían realmente
2. **Enlaces de un solo uso**: Cada enlace solo funciona UNA VEZ
3. **Expiración**: Los enlaces expiran en 1 HORA
4. **Seguridad**: Las contraseñas se encriptan antes de guardarse
5. **Emails únicos**: Cada usuario debe tener un email diferente

---

## ✨ FUNCIONA PERFECTAMENTE

El sistema está **100% funcional** y listo para usar. En modo desarrollo no necesitas configurar nada, solo probar!

¿Algún problema? Revisa la consola del servidor donde corre Django.
