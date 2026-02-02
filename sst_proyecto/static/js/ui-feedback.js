/**
 * UI Feedback System - Sistema de retroalimentación visual
 * Centro Minero SENA - Sistema SST
 */

class UIFeedback {
    /**
     * Muestra un toast/notificación temporal
     * @param {string} message - Mensaje a mostrar
     * @param {string} type - Tipo de alerta: success, danger, warning, info
     * @param {number} duration - Duración en milisegundos (default: 3000)
     */
    static showToast(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed top-0 end-0 m-4 shadow-lg`;
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        toast.style.animation = 'slideInRight 0.3s ease-out';

        // Icono según el tipo
        const icons = {
            success: 'bi-check-circle-fill',
            danger: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };

        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi ${icons[type]} me-3 fs-5"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        document.body.appendChild(toast);

        // Auto-dismiss
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, duration);

        return toast;
    }

    /**
     * Muestra overlay de carga sobre un elemento
     * @param {HTMLElement} element - Elemento sobre el cual mostrar el loading
     * @param {string} message - Mensaje opcional
     * @returns {HTMLElement} - El overlay creado (para poder removerlo después)
     */
    static showLoading(element, message = 'Cargando...') {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-sena mx-auto mb-3"></div>
                <p class="text-muted">${message}</p>
            </div>
        `;

        // Asegurar que el elemento padre tenga position relative
        const computedStyle = window.getComputedStyle(element);
        if (computedStyle.position === 'static') {
            element.style.position = 'relative';
        }

        element.appendChild(overlay);
        return overlay;
    }

    /**
     * Oculta el overlay de carga
     * @param {HTMLElement} overlay - El overlay a remover
     */
    static hideLoading(overlay) {
        if (overlay && overlay.parentNode) {
            overlay.style.opacity = '0';
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.remove();
                }
            }, 200);
        }
    }

    /**
     * Muestra confirmación antes de una acción
     * @param {string} message - Mensaje de confirmación
     * @param {string} title - Título del modal
     * @returns {Promise<boolean>} - true si confirma, false si cancela
     */
    static async confirm(message, title = '¿Está seguro?') {
        return new Promise((resolve) => {
            // Crear modal de confirmación
            const modal = document.createElement('div');
            modal.className = 'modal fade show';
            modal.style.display = 'block';
            modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
            modal.innerHTML = `
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${title}</h5>
                            <button type="button" class="btn-close" data-action="cancel"></button>
                        </div>
                        <div class="modal-body">
                            <p class="mb-0">${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-action="cancel">
                                Cancelar
                            </button>
                            <button type="button" class="btn btn-primary" data-action="confirm">
                                Confirmar
                            </button>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            // Event listeners
            modal.querySelectorAll('[data-action="cancel"]').forEach(btn => {
                btn.addEventListener('click', () => {
                    modal.remove();
                    resolve(false);
                });
            });

            modal.querySelector('[data-action="confirm"]').addEventListener('click', () => {
                modal.remove();
                resolve(true);
            });

            // Cerrar con ESC
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    modal.remove();
                    resolve(false);
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
        });
    }

    /**
     * Muestra indicador de progreso
     * @param {number} percentage - Porcentaje de 0 a 100
     * @param {string} message - Mensaje opcional
     */
    static showProgress(percentage, message = '') {
        let progressBar = document.getElementById('global-progress-bar');

        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.id = 'global-progress-bar';
            progressBar.className = 'position-fixed top-0 start-0 w-100';
            progressBar.style.zIndex = '9999';
            progressBar.innerHTML = `
                <div class="progress" style="height: 4px; border-radius: 0;">
                    <div class="progress-bar bg-primary" role="progressbar" style="width: 0%"></div>
                </div>
                ${message ? `<div class="bg-white text-center py-2 shadow-sm"><small>${message}</small></div>` : ''}
            `;
            document.body.appendChild(progressBar);
        }

        const bar = progressBar.querySelector('.progress-bar');
        bar.style.width = `${percentage}%`;

        if (percentage >= 100) {
            setTimeout(() => {
                progressBar.remove();
            }, 500);
        }
    }

    /**
     * Agrega clase de shake a un elemento (útil para errores)
     * @param {HTMLElement} element - Elemento a animar
     */
    static shake(element) {
        element.style.animation = 'shake 0.5s';
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }

    /**
     * Copia texto al portapapeles y muestra feedback
     * @param {string} text - Texto a copiar
     */
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Texto copiado al portapapeles', 'success', 2000);
            return true;
        } catch (err) {
            this.showToast('Error al copiar texto', 'danger');
            return false;
        }
    }
}

// Animación shake
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
        20%, 40%, 60%, 80% { transform: translateX(10px); }
    }

    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Exportar para uso global
window.UIFeedback = UIFeedback;
