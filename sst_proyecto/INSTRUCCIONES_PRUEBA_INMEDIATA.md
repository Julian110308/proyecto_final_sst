# 🔧 SOLUCIÓN APLICADA - Instrucciones de Prueba

## ✅ PROBLEMAS SOLUCIONADOS

### 1. Login no funcionaba ❌ → ✅ SOLUCIONADO
**Problema:** Las contraseñas no estaban hasheadas correctamente
**Solución:** Ejecuté script `resetear_passwords.py` que rehasheo todas las contraseñas
**Resultado:** Autenticación verificada y funcionando

### 2. Template de login con conflictos ❌ → ✅ SOLUCIONADO
**Problema:** El template personalizado `login.html` podría tener conflictos
**Solución:** Creé `login_simple.html` - versión limpia y funcional
**Resultado:** Formulario directo que usa Django LoginView correctamente

### 3. Email de recuperación no aparecía ❌ → ✅ EXPLICADO
**Problema:** Buscabas el email en tu bandeja de entrada
**Solución:** En modo desarrollo, los emails NO se envían - aparecen en la CONSOLA del servidor
**Resultado:** Instrucciones claras abajo sobre dónde ver el email

---

## 🔑 CREDENCIALES ACTUALIZADAS Y VERIFICADAS

Todas estas credenciales han sido verificadas y funcionan:

### Usuario ADMINISTRATIVO (Acceso Total):
```
Usuario: admin
Contraseña: admin123
```

### Usuario APRENDIZ (Acceso Limitado):
```
Usuario: julian
Contraseña: password123
```

### Otros Usuarios:
```
Usuario: dario
Contraseña: password123

Usuario: ruben
Contraseña: password123

Usuario: Tenjo
Contraseña: password123

Usuario: kevin
Contraseña: password123
```

---

## 📝 PRUEBA 1: LOGIN BÁSICO

### Paso 1: Abrir el navegador
```
URL: http://localhost:8000/accounts/login/
```

### Paso 2: Ingresar credenciales
```
Usuario: admin
Contraseña: admin123
```

### Paso 3: Hacer clic en "Iniciar Sesión"

### ✅ Resultado Esperado:
- Debe redirigir al dashboard principal
- NO debe mostrar "usuario o contraseña incorrectos"
- Debe aparecer el nombre del usuario en la parte superior

### ❌ Si sigue sin funcionar:
1. Presiona F12 en el navegador
2. Ve a la pestaña "Console" (Consola)
3. Busca errores en rojo
4. Toma captura de pantalla y dime qué dice

---

## 📧 PRUEBA 2: RECUPERACIÓN DE CONTRASEÑA

### IMPORTANTE: Los emails NO llegan a tu correo

En modo desarrollo, los emails se muestran en la **CONSOLA DEL SERVIDOR** (la terminal donde corre Django).

### Paso 1: Solicitar recuperación
```
1. Ir a: http://localhost:8000/accounts/login/
2. Click en "¿Olvidaste tu contraseña?"
3. Ingresar: admin@sena.edu.co
4. Click en "Enviar enlace de recuperación"
```

### Paso 2: Ver el email en la CONSOLA

**NO busques en tu correo electrónico** ✋

En su lugar:
1. Ve a la **terminal/consola donde corre Django**
2. Busca un bloque de texto que comienza con:
   ```
   Content-Type: text/html; charset="utf-8"
   MIME-Version: 1.0
   Subject: Recuperación de Contraseña - Sistema SST Centro Minero SENA
   From: SST Centro Minero <noreply@centrominerosst.com>
   To: admin@sena.edu.co
   ```
3. Dentro de ese bloque, busca una línea que dice:
   ```
   http://localhost:8000/accounts/reset/MQ/xxxxxx-xxxxxxxxx/
   ```
4. **ESE es el enlace de recuperación**

### Paso 3: Usar el enlace
```
1. Copiar el enlace completo (desde http hasta el final)
2. Pegarlo en el navegador
3. Presionar Enter
4. Ingresar nueva contraseña (2 veces)
5. Click en "Restablecer Contraseña"
```

### ✅ Resultado Esperado:
- Página de éxito con cuenta regresiva
- Redirect automático al login en 5 segundos
- Puedes iniciar sesión con la nueva contraseña

---

## 🔐 PRUEBA 3: PERMISOS POR ROL

### Test A: Usuario ADMIN (debe tener acceso completo)

1. **Login:**
   ```
   Usuario: admin
   Contraseña: admin123
   ```

2. **Intentar acceder a Control de Acceso:**
   ```
   URL: http://localhost:8000/control-acceso/
   ```

3. **✅ Resultado esperado:** Debe entrar sin problemas

---

### Test B: Usuario APRENDIZ (acceso limitado)

1. **Cerrar sesión** (si estás logueado)

2. **Login:**
   ```
   Usuario: julian
   Contraseña: password123
   ```

3. **Intentar acceder a Control de Acceso:**
   ```
   URL: http://localhost:8000/control-acceso/
   ```

4. **❌ Resultado esperado:** Debe redirigir y mostrar mensaje de error

5. **Intentar acceder a Mapas:**
   ```
   URL: http://localhost:8000/mapas/
   ```

6. **✅ Resultado esperado:** Debe entrar sin problemas

---

## 🖥️ ESTADO DEL SERVIDOR

### Verificar que el servidor está corriendo:

1. Busca la terminal/consola donde ejecutas Django
2. Debe mostrar algo como:
   ```
   Starting development server at http://127.0.0.1:8000/
   Quit the server with CTRL-BREAK.
   ```

### Si el servidor NO está corriendo:

```bash
cd "c:\Users\as\Desktop\Proyecto sst\proyecto_final_sst\sst_proyecto"
python manage.py runserver
```

---

## 📋 CHECKLIST DE VERIFICACIÓN

Marca cada prueba que hayas completado:

### Login:
- [ ] Abrí http://localhost:8000/accounts/login/
- [ ] Ingresé admin / admin123
- [ ] Pude entrar al dashboard
- [ ] Veo mi nombre de usuario en la página

### Recuperación de Contraseña:
- [ ] Solicité recuperación para admin@sena.edu.co
- [ ] Vi el email EN LA CONSOLA del servidor (no en mi email)
- [ ] Copié el enlace de la consola
- [ ] Abrí el enlace en el navegador
- [ ] Cambié la contraseña exitosamente
- [ ] Pude iniciar sesión con la nueva contraseña

### Permisos:
- [ ] Login como admin → Pude acceder a /control-acceso/
- [ ] Login como julian → NO pude acceder a /control-acceso/
- [ ] Login como julian → SÍ pude acceder a /mapas/

---

## 🚨 POSIBLES PROBLEMAS

### Problema: "Página no se puede mostrar"
**Solución:**
- Verifica que el servidor esté corriendo
- Verifica la URL: `http://localhost:8000` (no https)

### Problema: Sigue diciendo "usuario o contraseña incorrectos"
**Solución:**
1. Presiona F12 en el navegador
2. Ve a "Network" (Red)
3. Intenta hacer login de nuevo
4. Busca la petición "login"
5. Click derecho → Copy → Copy as cURL
6. Mándame esa información

### Problema: No veo el email en la consola
**Solución:**
- Asegúrate de estar viendo la terminal CORRECTA (donde corre Django)
- El email aparece INMEDIATAMENTE después de solicitar recuperación
- Busca líneas que empiecen con "Content-Type:" o "Subject:"

---

## 📞 SOPORTE

### Si algo no funciona:

1. **Toma captura de pantalla de:**
   - La pantalla del navegador mostrando el error
   - La consola del servidor (terminal)
   - La consola del navegador (F12 → Console)

2. **Dime exactamente:**
   - Qué prueba estabas haciendo (Login, Recuperación, Permisos)
   - Qué credenciales usaste
   - Qué error apareció

3. **Yo puedo:**
   - Revisar los logs del servidor
   - Verificar la configuración
   - Crear más scripts de diagnóstico

---

## 🎯 ARCHIVOS IMPORTANTES

### Scripts de utilidad:
- `resetear_passwords.py` - Resetear contraseñas (ya ejecutado)
- `test_login_simple.py` - Diagnóstico de autenticación
- `check_form_fields.py` - Verificar campos del formulario

### Templates:
- `login_simple.html` - Login funcional (EN USO AHORA)
- `login.html` - Login original (desactivado temporalmente)

### Documentación:
- `SOLUCION_LOGIN.md` - Explicación del problema anterior
- `INSTRUCCIONES_PRUEBA_INMEDIATA.md` - Este archivo
- `VERIFICACION_SISTEMA_COMPLETO.md` - Estado general

---

## ✅ CONFIRMACIÓN

**Estado actual del sistema:**
- ✅ Servidor corriendo en http://127.0.0.1:8000/
- ✅ Contraseñas reseteadas y verificadas
- ✅ Login simple activado
- ✅ Autenticación funcionando (verificado con script)
- ✅ Email backend configurado (modo consola)
- ✅ Permisos por rol implementados

**¡TODO ESTÁ LISTO PARA PROBAR!**

---

**Última actualización:** 26 de Diciembre, 2025 - 11:35
**Estado:** ✅ LISTO PARA PRUEBAS
