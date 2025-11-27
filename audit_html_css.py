"""
Script para verificar que todos los archivos HTML tengan
referencias correctas a sus archivos CSS correspondientes
"""

import os
import re
from pathlib import Path

TEMPLATES_DIR = r"c:\Users\23e06\OneDrive\Imágenes\casino_backend\templates"
CSS_DIR = r"c:\Users\23e06\OneDrive\Imágenes\casino_backend\static\css"

def extract_css_reference(html_file):
    """Extrae la referencia CSS de un archivo HTML"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar url_for con CSS
    pattern = r"url_for\('static',\s*path='css/([^']+)'\)"
    match = re.search(pattern, content)
    
    if match:
        return match.group(1)
    
    # Buscar referencias directas (incorrectas)
    pattern2 = r'href=["\'](?:/static/css/|\.\./)([^"\']+\.css)["\']'
    match2 = re.search(pattern2, content)
    
    if match2:
        return f"DIRECT: {match2.group(1)}"
    
    # Buscar <style> inline
    if '<style>' in content or '<style ' in content:
        return "INLINE CSS"
    
    return None

def check_css_exists(css_filename):
    """Verifica si el archivo CSS existe"""
    css_path = os.path.join(CSS_DIR, css_filename)
    return os.path.exists(css_path)

def get_expected_css(html_filename):
    """Devuelve el nombre esperado del CSS basado en el HTML"""
    # Quitar extensión .html y agregar .css
    base_name = html_filename.replace('.html', '')
    return f"{base_name}.css"

def main():
    """Ejecuta la auditoría"""
    print("=" * 70)
    print("AUDITORIA DE CONEXIONES HTML -> CSS")
    print("=" * 70)
    print()
    
    html_files = sorted([f for f in os.listdir(TEMPLATES_DIR) if f.endswith('.html')])
    
    issues = []
    correct = []
    inline_css = []
    
    for html_file in html_files:
        html_path = os.path.join(TEMPLATES_DIR, html_file)
        css_ref = extract_css_reference(html_path)
        expected_css = get_expected_css(html_file)
        
        status = "OK"
        
        if css_ref is None:
            status = "MISSING"
            issues.append({
                'file': html_file,
                'issue': 'Sin referencia CSS',
                'expected': expected_css
            })
        elif css_ref == "INLINE CSS":
            status = "INLINE"
            inline_css.append(html_file)
        elif css_ref.startswith("DIRECT:"):
            status = "DIRECT"
            actual_css = css_ref.replace("DIRECT: ", "")
            issues.append({
                'file': html_file,
                'issue': f'Referencia directa: {actual_css}',
                'expected': f'Debe usar url_for()'
            })
        else:
            # Verificar si el CSS existe
            if check_css_exists(css_ref):
                status = "OK"
                correct.append({
                    'file': html_file,
                    'css': css_ref
                })
            else:
                status = "NOT_FOUND"
                issues.append({
                    'file': html_file,
                    'issue': f'CSS no existe: {css_ref}',
                    'expected': 'Crear el archivo CSS'
                })
        
        # Imprimir resultado
        symbol = {
            'OK': 'OK',
            'MISSING': '!!',
            'DIRECT': 'XX',
            'NOT_FOUND': '??',
            'INLINE': '**'
        }[status]
        
        print(f"[{symbol}] {html_file:<50} -> {css_ref or 'NONE'}")
    
    # Resumen
    print()
    print("=" * 70)
    print("RESUMEN")
    print("=" * 70)
    print(f"Total archivos HTML: {len(html_files)}")
    print(f"Correctos (url_for): {len(correct)}")
    print(f"Con CSS inline: {len(inline_css)}")
    print(f"Con problemas: {len(issues)}")
    print()
    
    if issues:
        print("PROBLEMAS ENCONTRADOS:")
        print("-" * 70)
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue['file']}")
            print(f"   Problema: {issue['issue']}")
            print(f"   Solucion: {issue['expected']}")
            print()
    
    if inline_css:
        print("ARCHIVOS CON CSS INLINE:")
        print("-" * 70)
        for f in inline_css:
            print(f"  - {f}")
        print()

if __name__ == "__main__":
    main()
