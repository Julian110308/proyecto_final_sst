/**
 * Form Validation - Validación de formularios en tiempo real
 * Centro Minero SENA - Sistema SST
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar validación para todos los formularios con clase .needs-validation
    const forms = document.querySelectorAll('.needs-validation');

    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');

        // Validar en blur (cuando pierde el foco)
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });

            // Validar mientras escribe si ya hay un error mostrado
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });

        // Validar al enviar el formulario
        form.addEventListener('submit', function(event) {
            let isValid = true;

            inputs.forEach(input => {
                if (!validateField(input)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                event.preventDefault();
                event.stopPropagation();

                // Mostrar toast de error
                if (window.UIFeedback) {
                    window.UIFeedback.showToast('Por favor corrija los errores en el formulario', 'danger');
                }

                // Scroll al primer campo con error
                const firstInvalid = form.querySelector('.is-invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }

            form.classList.add('was-validated');
        });
    });

    /**
     * Valida un campo individual
     * @param {HTMLElement} field - Campo a validar
     * @returns {boolean} - true si es válido, false si no
     */
    function validateField(field) {
        // Limpiar validación previa
        field.classList.remove('is-valid', 'is-invalid');

        // Obtener o crear contenedor de feedback
        let feedback = field.parentElement.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentElement.appendChild(feedback);
        }

        // Validación HTML5 nativa
        if (!field.checkValidity()) {
            field.classList.add('is-invalid');
            feedback.textContent = field.validationMessage;
            return false;
        }

        // Validaciones personalizadas
        const customValidations = {
            // Validación de email
            email: (value) => {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(value)) {
                    return 'Ingrese un correo electrónico válido';
                }
                return null;
            },

            // Validación de documento (Colombia)
            documento: (value) => {
                if (!/^\d{6,10}$/.test(value)) {
                    return 'El documento debe contener entre 6 y 10 dígitos';
                }
                return null;
            },

            // Validación de teléfono (Colombia)
            telefono: (value) => {
                if (!/^\d{7,10}$/.test(value)) {
                    return 'El teléfono debe contener entre 7 y 10 dígitos';
                }
                return null;
            },

            // Validación de contraseña fuerte
            password: (value) => {
                if (value.length < 8) {
                    return 'La contraseña debe tener al menos 8 caracteres';
                }
                if (!/[A-Z]/.test(value)) {
                    return 'La contraseña debe contener al menos una mayúscula';
                }
                if (!/[a-z]/.test(value)) {
                    return 'La contraseña debe contener al menos una minúscula';
                }
                if (!/[0-9]/.test(value)) {
                    return 'La contraseña debe contener al menos un número';
                }
                return null;
            }
        };

        // Aplicar validaciones personalizadas según data-validate
        const validateType = field.dataset.validate;
        if (validateType && customValidations[validateType]) {
            const error = customValidations[validateType](field.value);
            if (error) {
                field.classList.add('is-invalid');
                feedback.textContent = error;
                return false;
            }
        }

        // Validación de confirmación de contraseña
        if (field.dataset.match) {
            const matchField = document.getElementById(field.dataset.match);
            if (matchField && field.value !== matchField.value) {
                field.classList.add('is-invalid');
                feedback.textContent = 'Las contraseñas no coinciden';
                return false;
            }
        }

        // Campo válido
        field.classList.add('is-valid');
        feedback.textContent = '';
        return true;
    }

    /**
     * Validación de fuerza de contraseña con indicador visual
     */
    const passwordFields = document.querySelectorAll('input[type="password"][data-strength]');
    passwordFields.forEach(field => {
        const strengthIndicator = document.createElement('div');
        strengthIndicator.className = 'password-strength mt-2';
        strengthIndicator.innerHTML = `
            <div class="progress" style="height: 4px;">
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            </div>
            <small class="text-muted"></small>
        `;
        field.parentElement.appendChild(strengthIndicator);

        field.addEventListener('input', function() {
            const value = this.value;
            let strength = 0;
            let label = '';
            let colorClass = '';

            if (value.length >= 8) strength += 25;
            if (/[a-z]/.test(value)) strength += 25;
            if (/[A-Z]/.test(value)) strength += 25;
            if (/[0-9]/.test(value)) strength += 15;
            if (/[^a-zA-Z0-9]/.test(value)) strength += 10;

            if (strength < 40) {
                label = 'Débil';
                colorClass = 'bg-danger';
            } else if (strength < 70) {
                label = 'Media';
                colorClass = 'bg-warning';
            } else {
                label = 'Fuerte';
                colorClass = 'bg-success';
            }

            const bar = strengthIndicator.querySelector('.progress-bar');
            const text = strengthIndicator.querySelector('small');

            bar.style.width = `${strength}%`;
            bar.className = `progress-bar ${colorClass}`;
            text.textContent = value.length > 0 ? `Seguridad: ${label}` : '';
        });
    });

    /**
     * Toggle de visibilidad de contraseña
     */
    const passwordToggles = document.querySelectorAll('[data-password-toggle]');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const targetId = this.dataset.passwordToggle;
            const target = document.getElementById(targetId);

            if (target.type === 'password') {
                target.type = 'text';
                this.querySelector('i').classList.replace('bi-eye', 'bi-eye-slash');
            } else {
                target.type = 'password';
                this.querySelector('i').classList.replace('bi-eye-slash', 'bi-eye');
            }
        });
    });

    /**
     * Auto-formateo de campos
     */
    // Documento: solo números
    const documentoInputs = document.querySelectorAll('input[data-validate="documento"]');
    documentoInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '');
        });
    });

    // Teléfono: solo números
    const telefonoInputs = document.querySelectorAll('input[data-validate="telefono"]');
    telefonoInputs.forEach(input => {
        input.addEventListener('input', function() {
            this.value = this.value.replace(/\D/g, '');
        });
    });

    // Email: lowercase automático
    const emailInputs = document.querySelectorAll('input[type="email"], input[data-validate="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            this.value = this.value.toLowerCase();
        });
    });
});
