#!/usr/bin/env python3
"""
Script para agregar el script de seguridad global a todas las páginas HTML
del sitio (excepto los juegos que ya tienen su propia seguridad)
"""

import os
import re
from pathlib import Path

# Directorio de templates
TEMPLATES_DIR = Path(r"c:\Users\23e06\Videos\proyectos uni\casino_backend\templates")

# Script de seguridad a agregar
SECURITY_SCRIPT = '''  <script src="{{ url_for('static', path='js/security.js') }}"></script>'''

# Archivos a excluir (juegos y otros que no necesitan el script)
EXCLUDE_FILES = {
    'play_game.html',  # Página que carga juegos
    'offline.html',     # Página offline
    'loading.html'      # Página de carga
}

def should_process_file(filename):
    """Determina si un archivo debe ser procesado"""
    if filename in EXCLUDE_FILES:
        return False
    if not filename.endswith('.html'):
        return False
    return True

def has_security_script(content):
    """Verifica si el archivo ya tiene el script de seguridad"""
    return "security.js" in content

def add_security_script(filepath):
    """Agrega el script de seguridad antes del cierre de </body>"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Si ya tiene el script, no hacer nada
        if has_security_script(content):
            print(f"  [OK] {filepath.name} - Ya tiene el script de seguridad")
            return False
        
        # Buscar el cierre de </body>
        if '</body>' not in content:
            print(f"  [WARN] {filepath.name} - No tiene etiqueta </body>")
            return False
        
        # Agregar el script antes de </body>
        new_content = content.replace('</body>', f'{SECURITY_SCRIPT}\n</body>')
        
        # Guardar el archivo
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  [ADD] {filepath.name} - Script agregado")
        return True
        
    except Exception as e:
        print(f"  [ERROR] {filepath.name} - Error: {e}")
        return False

def main():
    print("Agregando script de seguridad global a todas las paginas...\n")
    
    processed = 0
    skipped = 0
    errors = 0
    
    # Procesar todos los archivos HTML
    for filepath in TEMPLATES_DIR.glob('*.html'):
        if should_process_file(filepath.name):
            if add_security_script(filepath):
                processed += 1
            else:
                if has_security_script(filepath.read_text(encoding='utf-8')):
                    skipped += 1
                else:
                    errors += 1
        else:
            print(f"  [SKIP] {filepath.name} - Excluido")
            skipped += 1
    
    print(f"\nResumen:")
    print(f"  Procesados: {processed}")
    print(f"  Omitidos: {skipped}")
    print(f"  Errores: {errors}")
    print(f"\nProceso completado!")

if __name__ == "__main__":
    main()
