import psutil

def buscarProcesosMinecraft():
    print("🔍 Buscando procesos de Minecraft...\n")

    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Solo procesos que usan Java
            if "java" in proc.info['name'].lower():
                cmdline = " ".join(proc.info['cmdline'])
                
                if "server.jar" in cmdline or "minecraft_server" in cmdline:
                    print(f"🟢 PID {proc.info['pid']}: {cmdline}")
                elif any(keyword in cmdline for keyword in ["vanilla", "forge", "fabric", "paper", "spigot"]):
                    print(f"🟡 PID {proc.info['pid']}: {cmdline}")
                else:
                    # Java pero no identificado como servidor MC
                    pass

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
        
buscarProcesosMinecraft()