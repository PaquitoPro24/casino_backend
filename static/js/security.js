// ========== MEDIDAS DE SEGURIDAD GLOBALES - ROYAL CRUMBS ==========
// Este script previene zoom, copiar/pegar, y otras acciones no deseadas
// en todas las páginas del sitio (excepto juegos)

(function () {
    'use strict';

    // Deshabilitar menú contextual (clic derecho)
    document.addEventListener('contextmenu', function (e) {
        e.preventDefault();
        return false;
    });

    // Deshabilitar selección de texto
    document.addEventListener('selectstart', function (e) {
        e.preventDefault();
        return false;
    });

    // Deshabilitar copiar
    document.addEventListener('copy', function (e) {
        e.preventDefault();
        return false;
    });

    // Deshabilitar cortar
    document.addEventListener('cut', function (e) {
        e.preventDefault();
        return false;
    });

    // Deshabilitar pegar
    document.addEventListener('paste', function (e) {
        e.preventDefault();
        return false;
    });

    // Deshabilitar arrastrar
    document.addEventListener('dragstart', function (e) {
        e.preventDefault();
        return false;
    });

    // Deshabilitar teclas de inspección y zoom
    document.addEventListener('keydown', function (e) {
        // F12 (DevTools)
        if (e.key === 'F12') {
            e.preventDefault();
            return false;
        }

        // Ctrl+Shift+I / Cmd+Option+I (Inspeccionar)
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'I') {
            e.preventDefault();
            return false;
        }

        // Ctrl+Shift+J / Cmd+Option+J (Consola)
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'J') {
            e.preventDefault();
            return false;
        }

        // Ctrl+Shift+C / Cmd+Option+C (Selector de elementos)
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            return false;
        }

        // Ctrl+U / Cmd+U (Ver código fuente)
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            return false;
        }

        // Ctrl+S / Cmd+S (Guardar página)
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            return false;
        }

        // Ctrl+P / Cmd+P (Imprimir)
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            e.preventDefault();
            return false;
        }

        // Ctrl+Plus / Ctrl+Minus (Zoom in/out)
        if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '-' || e.key === '=' || e.key === '_')) {
            e.preventDefault();
            return false;
        }

        // Ctrl+0 (Reset zoom)
        if ((e.ctrlKey || e.metaKey) && e.key === '0') {
            e.preventDefault();
            return false;
        }
    });

    // Prevenir zoom con rueda del mouse + Ctrl
    document.addEventListener('wheel', function (e) {
        if (e.ctrlKey) {
            e.preventDefault();
        }
    }, { passive: false });

    // Prevenir zoom táctil (pinch)
    document.addEventListener('touchmove', function (e) {
        if (e.touches.length > 1) {
            e.preventDefault();
        }
    }, { passive: false });

    // Prevenir zoom con gestos táctiles
    document.addEventListener('gesturestart', function (e) {
        e.preventDefault();
    });

    document.addEventListener('gesturechange', function (e) {
        e.preventDefault();
    });

    document.addEventListener('gestureend', function (e) {
        e.preventDefault();
    });

    // Aplicar estilos CSS para prevenir selección
    const style = document.createElement('style');
    style.textContent = `
        * {
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
            -webkit-touch-callout: none;
            -webkit-user-drag: none;
        }
        
        /* Permitir selección solo en inputs y textareas */
        input, textarea {
            -webkit-user-select: text;
            -moz-user-select: text;
            -ms-user-select: text;
            user-select: text;
        }
    `;
    document.head.appendChild(style);

    console.log('🔒 Royal Crumbs Security: Protecciones activadas');
})();
