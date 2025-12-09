# Sistema de Internacionalización (i18n) - Royal Crumbs

## 📋 Descripción

Sistema de cambio de idioma global que permite a los usuarios cambiar entre Español e Inglés en toda la aplicación.

## 🌍 Idiomas Soportados

- 🇪🇸 **Español** (es) - Idioma por defecto
- 🇬🇧 **English** (en)

## 🎯 Características

- ✅ Cambio de idioma persistente (usa localStorage)
- ✅ Traducción automática de toda la página
- ✅ Selector de idioma en el menú de cuenta
- ✅ Soporte para elementos HTML dinámicos
- ✅ API JavaScript para traducciones programáticas

## 📝 Cómo Usar

### 1. Incluir el Script

Agrega el script i18n en tus páginas HTML:

```html
<script src="{{ url_for('static', path='js/i18n.js') }}"></script>
```

### 2. Marcar Elementos para Traducción

Usa el atributo `data-i18n` con la clave de traducción:

```html
<!-- Texto normal -->
<h1 data-i18n="nav.home">Inicio</h1>

<!-- Botones -->
<button data-i18n="btn.save">Guardar</button>

<!-- Placeholders -->
<input type="text" data-i18n="search.placeholder" placeholder="Buscar...">
```

### 3. Agregar Nuevas Traducciones

Edita el archivo `static/js/i18n.js` y agrega las claves en ambos idiomas:

```javascript
const translations = {
    es: {
        'mi.nueva.clave': 'Texto en español'
    },
    en: {
        'mi.nueva.clave': 'Text in English'
    }
};
```

### 4. Usar en JavaScript

```javascript
// Obtener traducción
const texto = window.i18n.t('nav.home');

// Cambiar idioma programáticamente
window.i18n.setLanguage('en');

// Obtener idioma actual
const lang = window.i18n.getCurrentLanguage();

// Escuchar cambios de idioma
window.addEventListener('languageChanged', function(e) {
    console.log('Nuevo idioma:', e.detail.language);
});
```

## 🎨 Selector de Idioma

El selector de idioma está ubicado en:
- **Ruta**: `/account` (Mi Cuenta)
- **Posición**: Al final de la lista de opciones

## 📦 Archivos del Sistema

```
static/js/i18n.js          # Sistema principal de traducción
templates/account.html      # Página con selector de idioma
```

## 🔧 Configuración

El idioma se guarda en `localStorage` con la clave `language`:

```javascript
// Español (por defecto)
localStorage.setItem('language', 'es');

// Inglés
localStorage.setItem('language', 'en');
```

## 📚 Claves de Traducción Disponibles

### Navegación
- `nav.home` - Inicio / Home
- `nav.games` - Juegos / Games
- `nav.wallet` - Cartera / Wallet
- `nav.support` - Soporte / Support
- `nav.account` - Mi Cuenta / My Account

### Cuenta
- `account.title` - Mi Cuenta / My Account
- `account.settings` - Configuración / Settings
- `account.bonuses` - Bonos / Bonuses
- `account.wallet` - Cartera / Wallet

### Juegos
- `games.title` - Juegos / Games
- `games.roulette` - Ruleta / Roulette
- `games.slots` - Tragamonedas / Slots
- `games.blackjack` - Blackjack / Blackjack
- `games.play` - Jugar / Play
- `games.back` - Volver / Back

### Botones
- `btn.save` - Guardar / Save
- `btn.cancel` - Cancelar / Cancel
- `btn.confirm` - Confirmar / Confirm
- `btn.close` - Cerrar / Close

### Mensajes
- `msg.loading` - Cargando... / Loading...
- `msg.success` - Éxito / Success
- `msg.error` - Error / Error
- `msg.welcome` - Bienvenido / Welcome

## 🚀 Ejemplo Completo

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Mi Página</title>
</head>
<body>
    <!-- Elementos con traducción -->
    <h1 data-i18n="nav.home">Inicio</h1>
    <button data-i18n="btn.save">Guardar</button>
    
    <!-- Selector de idioma -->
    <select id="language-selector" onchange="window.i18n.setLanguage(this.value)">
        <option value="es">🇪🇸 Español</option>
        <option value="en">🇬🇧 English</option>
    </select>
    
    <!-- Script i18n -->
    <script src="/static/js/i18n.js"></script>
</body>
</html>
```

## 💡 Notas Importantes

1. **Persistencia**: El idioma seleccionado se guarda automáticamente y persiste entre sesiones
2. **Idioma por defecto**: Si no hay idioma guardado, se usa Español (es)
3. **Actualización automática**: Al cambiar el idioma, toda la página se traduce automáticamente
4. **Compatibilidad**: Funciona en todos los navegadores modernos que soportan localStorage

## 🔄 Actualizar Traducciones

Para actualizar las traducciones sin recargar la página:

```javascript
window.i18n.translatePage();
```

## 📞 Soporte

Para agregar más idiomas o claves de traducción, edita el archivo `static/js/i18n.js`.
