"""
Live Server para desarrollo móvil
Ejecuta la aplicación FastAPI y abre Chrome en modo dispositivo móvil
"""
import subprocess
import time
import webbrowser
import os
import sys

def main():
    print("🚀 Iniciando servidor de desarrollo móvil...")
    print("=" * 60)
    
    # URL del servidor
    url = "http://localhost:8000"
    
    # Configurar Chrome para modo móvil (iPhone 12 Pro)
    chrome_path = None
    
    # Buscar Chrome en ubicaciones comunes de Windows
    chrome_locations = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    
    for location in chrome_locations:
        if os.path.exists(location):
            chrome_path = location
            break
    
    if not chrome_path:
        print("⚠️  No se encontró Chrome. Se abrirá en el navegador predeterminado.")
        print("    Para mejor experiencia, instala Google Chrome.")
    
    # Iniciar el servidor FastAPI en segundo plano
    print("\n📡 Iniciando servidor FastAPI...")
    print(f"🌐 URL: {url}")
    print("\n⚙️  Configuración:")
    print("   - Tamaño: 360x800 (móvil)")
    print("   - User Agent: iPhone 12 Pro")
    print("   - Hot Reload: Activado")
    print("\n" + "=" * 60)
    
    try:
        # Comando para iniciar uvicorn con hot reload
        server_cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        # Iniciar servidor
        server_process = subprocess.Popen(
            server_cmd,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Esperar a que el servidor inicie
        print("\n⏳ Esperando a que el servidor inicie...")
        time.sleep(3)
        
        # Abrir navegador en modo móvil
        if chrome_path:
            print("\n🌐 Abriendo Chrome en modo móvil...")
            # Argumentos para Chrome en modo móvil
            chrome_args = [
                chrome_path,
                f"--app={url}",
                "--window-size=360,800",
                "--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
                "--disable-extensions",
                "--disable-plugins",
                "--no-first-run",
                "--no-default-browser-check"
            ]
            subprocess.Popen(chrome_args)
        else:
            print("\n🌐 Abriendo navegador predeterminado...")
            webbrowser.open(url)
        
        print("\n✅ Servidor iniciado correctamente!")
        print("\n📱 Instrucciones:")
        print("   1. El navegador se abrió en modo móvil (360x800)")
        print("   2. Presiona F12 para abrir DevTools")
        print("   3. Haz clic en el ícono de dispositivo móvil (Ctrl+Shift+M)")
        print("   4. Selecciona 'iPhone 12 Pro' o 'Responsive'")
        print("\n⚡ Hot Reload activado - Los cambios se reflejarán automáticamente")
        print("\n🛑 Para detener el servidor: Presiona Ctrl+C")
        print("=" * 60)
        
        # Mantener el script corriendo
        server_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servidor...")
        server_process.terminate()
        server_process.wait()
        print("✅ Servidor detenido correctamente")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if 'server_process' in locals():
            server_process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main()
