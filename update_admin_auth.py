import os
import re

# Directory containing the templates
templates_dir = r"c:\Users\23e06\OneDrive\Documentos\casino_backend-1\templates"

# List of admin HTML files to update
admin_files = [
    "admin-gestion-usuarios.html",
    "admin-info-general.html",
    "admin-usuarios.html",
    "admin-administradores.html",
    "admin-usuario-perfil.html",
    "admin-administrador-perfil.html",
    "admin-juegos.html",
    "admin-promociones.html",
    "admin-configuracion-bloquear-ip.html"
]

def update_admin_file(filepath):
    """Update an admin HTML file to use centralized authentication"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if 'admin-auth.js' in content:
            print(f"[OK] {os.path.basename(filepath)} - Already updated")
            return
        
        # Add script tag in head section (after the last link tag)
        if '<script src="{{ url_for(\'static\', path=\'js/admin-auth.js\') }}"></script>' not in content:
            content = re.sub(
                r'(</head>)',
                r'  <script src="{{ url_for(\'static\', path=\'js/admin-auth.js\') }}"></script>\n\1',
                content,
                count=1
            )
        
        # Replace the inline auth check with centralized function
        old_auth_pattern = r'<script>\s*document\.addEventListener\("DOMContentLoaded",\s*\(\)\s*=>\s*{\s*const\s+adminRol\s*=\s*\(localStorage\.getItem\("user_role"\)\s*\|\|\s*""\)\.toLowerCase\(\)\.trim\(\);\s*if\s*\(adminRol\s*!==\s*\'administrador\'\s*&&\s*adminRol\s*!==\s*\'auditor\'\)\s*{\s*(?:alert\("Acceso denegado\."\);\s*)?window\.location\.href\s*=\s*"/login";\s*(?:return;\s*)?}\s*(?:}\);\s*</script>|(?=try\s*{))'
        
        new_auth_code = '''<script>
    document.addEventListener("DOMContentLoaded", () => {
      checkAdminAuth();'''
        
        content = re.sub(old_auth_pattern, new_auth_code, content, flags=re.DOTALL)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] {os.path.basename(filepath)} - Updated successfully")
        
    except Exception as e:
        print(f"[ERROR] {os.path.basename(filepath)} - Error: {e}")

# Update all files
print("Updating admin HTML files...")
print("=" * 50)

for filename in admin_files:
    filepath = os.path.join(templates_dir, filename)
    if os.path.exists(filepath):
        update_admin_file(filepath)
    else:
        print(f"[SKIP] {filename} - File not found")

print("=" * 50)
print("Done!")
