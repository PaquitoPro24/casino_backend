"""
Script para optimizar automaticamente todos los archivos CSS
convirtiendo valores fijos a responsive con clamp()
"""

import os
import re

CSS_DIR = r"c:\Users\23e06\OneDrive\Imágenes\casino_backend\static\css"

# Patrones de optimizacion
OPTIMIZATIONS = {
    # Font sizes
    r'font-size:\s*34px': 'font-size: clamp(28px, 6vw, 34px)',
    r'font-size:\s*32px': 'font-size: clamp(26px, 5.5vw, 32px)',
    r'font-size:\s*28px': 'font-size: clamp(22px, 5vw, 28px)',
    r'font-size:\s*24px': 'font-size: clamp(20px, 4.5vw, 24px)',
    r'font-size:\s*22px': 'font-size: clamp(18px, 4vw, 22px)',
    r'font-size:\s*20px': 'font-size: clamp(17px, 3.8vw, 20px)',
    r'font-size:\s*19px': 'font-size: clamp(16px, 3.5vw, 19px)',
    r'font-size:\s*18px': 'font-size: clamp(16px, 3.5vw, 18px)',
    r'font-size:\s*17px': 'font-size: clamp(15px, 3.3vw, 17px)',
    r'font-size:\s*16px': 'font-size: clamp(14px, 3vw, 16px)',
    r'font-size:\s*15px': 'font-size: clamp(13px, 2.8vw, 15px)',
    r'font-size:\s*14px': 'font-size: clamp(12px, 2.5vw, 14px)',
    r'font-size:\s*13px': 'font-size: clamp(11px, 2.3vw, 13px)',
    
    #Padding
    r'padding:\s*20px': 'padding: clamp(16px, 3vw, 20px)',
    r'padding:\s*18px': 'padding: clamp(14px, 3vw, 18px)',
    r'padding:\s*16px': 'padding: clamp(12px, 2.5vw, 16px)',
    r'padding:\s*14px': 'padding: clamp(11px, 2.3vw, 14px)',
    r'padding:\s*12px': 'padding: clamp(10px, 2vw, 12px)',
}

# Breakpoints to add if missing
RESPONSIVE_SECTION = """

/* ============================================================
   RESPONSIVE BREAKPOINTS
   ============================================================ */

@media (min-width: 640px) {
  .rc-container {
    max-width: 600px;
    padding-left: clamp(20px, 4vw, 32px);
    padding-right: clamp(20px, 4vw, 32px);
  }
}

@media (min-width: 768px) {
  .rc-container {
    max-width: 700px;
  }
  
  .rc-screen-title {
    font-size: clamp(26px, 5.5vw, 32px);
  }
}

@media (min-width: 1024px) {
  .rc-container {
    max-width: 800px;
    padding-bottom: 100px;
  }
}
"""

def optimize_css_file(filepath):
    """Optimiza un archivo CSS individual"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Aplicar optimizaciones
    for pattern, replacement in OPTIMIZATIONS.items():
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Agregar section responsiva si no existe suficiente responsive
    if content.count('@media') < 2:
        content = content.rstrip() + RESPONSIVE_SECTION
    
    # Guardar si hubo cambios
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Procesa todos los archivos CSS"""
    optimized_count = 0
    
    for filename in os.listdir(CSS_DIR):
        if filename.endswith('.css'):
            filepath = os.path.join(CSS_DIR, filename)
            try:
                if optimize_css_file(filepath):
                    optimized_count += 1
                    print(f"OK Optimizado: {filename}")
                else:
                    print(f"-- Sin cambios: {filename}")
            except Exception as e:
                print(f"ERROR en {filename}: {str(e)}")
    
    print(f"\nTotal optimizados: {optimized_count} archivos")

if __name__ == "__main__":
    main()
