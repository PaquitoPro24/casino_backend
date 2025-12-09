// Sistema de Internacionalización (i18n) para Royal Crumbs
// Soporta Español e Inglés

const translations = {
    es: {
        // Navegación y Menú
        'nav.home': 'Inicio',
        'nav.games': 'Juegos',
        'nav.wallet': 'Cartera',
        'nav.support': 'Soporte',
        'nav.account': 'Mi Cuenta',
        'nav.logout': 'Cerrar Sesión',
        
        // Cuenta
        'account.title': 'Mi Cuenta',
        'account.settings': 'Configuración',
        'account.bonuses': 'Bonos',
        'account.wallet': 'Cartera',
        'account.transactions': 'Transacciones',
        'account.history': 'Historial',
        
        // Juegos
        'games.title': 'Juegos',
        'games.roulette': 'Ruleta',
        'games.slots': 'Tragamonedas',
        'games.blackjack': 'Blackjack',
        'games.play': 'Jugar',
        'games.back': 'Volver',
        
        // Cartera
        'wallet.balance': 'Saldo',
        'wallet.deposit': 'Depositar',
        'wallet.withdraw': 'Retirar',
        'wallet.history': 'Historial',
        
        // Soporte
        'support.title': 'Soporte',
        'support.faq': 'Preguntas Frecuentes',
        'support.contact': 'Contacto',
        'support.terms': 'Términos y Condiciones',
        'support.privacy': 'Privacidad',
        
        // Botones generales
        'btn.save': 'Guardar',
        'btn.cancel': 'Cancelar',
        'btn.confirm': 'Confirmar',
        'btn.close': 'Cerrar',
        'btn.continue': 'Continuar',
        
        // Mensajes
        'msg.loading': 'Cargando...',
        'msg.success': 'Éxito',
        'msg.error': 'Error',
        'msg.welcome': 'Bienvenido',
        
        // Idioma
        'lang.select': 'Seleccionar Idioma',
        'lang.spanish': 'Español',
        'lang.english': 'English'
    },
    en: {
        // Navigation and Menu
        'nav.home': 'Home',
        'nav.games': 'Games',
        'nav.wallet': 'Wallet',
        'nav.support': 'Support',
        'nav.account': 'My Account',
        'nav.logout': 'Logout',
        
        // Account
        'account.title': 'My Account',
        'account.settings': 'Settings',
        'account.bonuses': 'Bonuses',
        'account.wallet': 'Wallet',
        'account.transactions': 'Transactions',
        'account.history': 'History',
        
        // Games
        'games.title': 'Games',
        'games.roulette': 'Roulette',
        'games.slots': 'Slots',
        'games.blackjack': 'Blackjack',
        'games.play': 'Play',
        'games.back': 'Back',
        
        // Wallet
        'wallet.balance': 'Balance',
        'wallet.deposit': 'Deposit',
        'wallet.withdraw': 'Withdraw',
        'wallet.history': 'History',
        
        // Support
        'support.title': 'Support',
        'support.faq': 'FAQ',
        'support.contact': 'Contact',
        'support.terms': 'Terms and Conditions',
        'support.privacy': 'Privacy',
        
        // General Buttons
        'btn.save': 'Save',
        'btn.cancel': 'Cancel',
        'btn.confirm': 'Confirm',
        'btn.close': 'Close',
        'btn.continue': 'Continue',
        
        // Messages
        'msg.loading': 'Loading...',
        'msg.success': 'Success',
        'msg.error': 'Error',
        'msg.welcome': 'Welcome',
        
        // Language
        'lang.select': 'Select Language',
        'lang.spanish': 'Español',
        'lang.english': 'English'
    }
};

// Obtener idioma actual (por defecto español)
function getCurrentLanguage() {
    return localStorage.getItem('language') || 'es';
}

// Establecer idioma
function setLanguage(lang) {
    if (!translations[lang]) {
        console.error('Idioma no soportado:', lang);
        return;
    }
    
    localStorage.setItem('language', lang);
    document.documentElement.lang = lang;
    translatePage();
    
    // Disparar evento personalizado para que otros componentes puedan reaccionar
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
}

// Traducir toda la página
function translatePage() {
    const lang = getCurrentLanguage();
    const elements = document.querySelectorAll('[data-i18n]');
    
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = translations[lang][key];
        
        if (translation) {
            // Si el elemento es un input/textarea, traducir el placeholder
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        }
    });
    
    // Actualizar el selector de idioma
    updateLanguageSelector();
}

// Actualizar el selector de idioma para mostrar el idioma actual
function updateLanguageSelector() {
    const selector = document.getElementById('language-selector');
    if (selector) {
        selector.value = getCurrentLanguage();
    }
}

// Inicializar el sistema de idiomas cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    const savedLang = getCurrentLanguage();
    document.documentElement.lang = savedLang;
    translatePage();
});

// Exportar funciones para uso global
window.i18n = {
    setLanguage,
    getCurrentLanguage,
    translatePage,
    t: function(key) {
        const lang = getCurrentLanguage();
        return translations[lang][key] || key;
    }
};
