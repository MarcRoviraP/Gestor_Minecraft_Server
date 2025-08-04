import requests
import os
import re

globalforgeVersions = []
def obtener_versiones_minecraft():
    #JARs disponibles apartir de la versión 1.2.5
    
    url = "https://piston-meta.mojang.com/mc/game/version_manifest.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        versiones = [v["id"] for v in data["versions"] if v["type"] == "release"]
        for i in range(6):
            versiones.pop()  # Eliminar las últimas 6 versiones

        return versiones
    else:
        print("Error al obtener las versiones:", response.status_code)
        return []
    
def obtener_jar_servidor(version_id):
    manifest = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest.json").json()
    entry = next((v for v in manifest["versions"] if v["id"] == version_id), None)
    if not entry:
        raise ValueError(f"Versión {version_id} no encontrada")
    version_json = requests.get(entry["url"]).json()
    return version_json["downloads"]["server"]["url"]

def descargar_server_jar(url, ruta_destino):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print("✅ Descargado correctamente:", ruta_destino)
    else:
        print("❌ Error al descargar:", response.status_code)

def detectar_version_minecraft(carpeta_servidor):
    log_path = os.path.join(carpeta_servidor, "logs", "latest.log")
    if not os.path.exists(log_path):
        log_path = os.path.join(carpeta_servidor, "server.log")
        

    with open(log_path, "r", encoding="utf-8") as log_file:
        for linea in log_file:
            if "Starting minecraft server version" in linea:
                match = re.search(r"version\s+([\d.]+)", linea)
                if match:
                    return match.group(1)
    return "N/A"

def getRecommendedForgeVersion(version):
    global globalforgeVersions
    if globalforgeVersions.status_code == 200:
        data = globalforgeVersions.json()
        # Filtrar por versión y recomendado
        filtered = [
            mod for mod in data.get("data", [])
            if mod.get("gameVersion") == version and mod.get("recommended")
        ]
        
        if filtered:
            return filtered[0].get("name")
        else:
            print("No se encontró una versión recomendada de Forge para la versión de Minecraft especificada.")
            return None
    else:
        print("Error al obtener la versión recomendada de Forge:", globalforgeVersions.status_code)
        return None
def getMinecraftVersionFromForge():
    global globalforgeVersions
    listGameVersions = []

    if not globalforgeVersions:
        getAllForgeVersions()
    data = globalforgeVersions.json()

    filtered = [
        mod for mod in data.get("data", [])
        if mod.get("recommended") ]
    if filtered:
        for mod in filtered:
            version = mod.get("gameVersion")
            # Comprobar si la versión es menor que 1.5.2
            if (
                version not in listGameVersions and
                tuple(map(int, version.split("."))) >= (1, 5, 2)
            ):
                listGameVersions.append(version)
        listGameVersions.sort(key=lambda x: tuple(map(int, x.split('.'))))
        listGameVersions.reverse()  # Ordenar de mayor a menor
        return listGameVersions
def getAllForgeVersions():
    url = "https://api.curseforge.com/v1/minecraft/modloader"

    global globalforgeVersions
    globalforgeVersions = requests.get(url)

def downloadJARInstallerForge(mcVersion, forgeVersion, ruta_destino):
    url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{mcVersion}-{forgeVersion}/forge-{mcVersion}-{forgeVersion}-installer.jar"
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print("✅ Descargado correctamente:", ruta_destino)
    else:
        print("❌ Error al descargar:", response.status_code)