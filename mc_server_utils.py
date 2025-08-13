import requests
import os
import re
import json
import psutil
import threading
import asyncio
import aiohttp

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
    
def getAllFabricVersions():
    url = "https://meta.fabricmc.net/v2/versions/game/"
    
    data = requests.get(url)
    stableVersions = [version["version"] for version in data.json() if version["stable"]]
    return stableVersions

def downloadJARFabric(version, ruta_destino):
    loaderURL = "https://meta.fabricmc.net/v2/versions/loader/"
    dataLoader = requests.get(loaderURL)
    versionLoader = [v["version"] for v in dataLoader.json() if v["stable"]][0]

    installerURL = "https://meta.fabricmc.net/v2/versions/installer/"
    dataInstaller = requests.get(installerURL)
    versionInstaller = [v["version"] for v in dataInstaller.json() if v["stable"]][0]

    url = f"https://meta.fabricmc.net/v2/versions/loader/{version}/{versionLoader}/{versionInstaller}/server/jar"
    download_file(ruta_destino, url)

def getAllForgeVersions():
    url = "https://api.curseforge.com/v1/minecraft/modloader"

    global globalforgeVersions
    globalforgeVersions = requests.get(url)

def downloadJARInstallerForge(mcVersion, forgeVersion, ruta_destino):
    url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{mcVersion}-{forgeVersion}/forge-{mcVersion}-{forgeVersion}-installer.jar"
    download_file(ruta_destino, url)

def download_file(ruta_destino, url):
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        with open(ruta_destino, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print("✅ Descargado correctamente:", ruta_destino)
    else:
        print("❌ Error al descargar:", response.status_code)
        
def obtener_todos_mods(tipo,version):
        """
        Descarga todos los mods de un tipo y versión usando la API de Modrinth.
        Esta función es un wrapper síncrono para la función asíncrona interna.
        """

        async def obtener_todos_mods_async(tipo, version, stop=99999999999999, limit=100):
            todos_mods = []
            offset = 0

            async with aiohttp.ClientSession() as session:
                while True:
                    params = {
                        "limit": limit,
                        "offset": offset,
                        "facets": json.dumps([
                            ["project_types:mod"],
                            [f"categories:{tipo}"],
                            [f"versions:{version}"],
                            ["server_side:optional", "server_side:required"]
                        ])
                    }
                    async with session.get("https://api.modrinth.com/v2/search", params=params) as response:
                        data = await response.json()
                        hits = data.get("hits", [])
                        if not hits:
                            break
                        todos_mods.extend(hits)
                        if stop <= len(todos_mods):
                            break
                        offset += limit
                        

            return todos_mods

        # Ejecutar la función asíncrona y devolver el resultado
        return asyncio.run(obtener_todos_mods_async(tipo, version))

def descargarMod(mod_id, ruta_destino):
    
    
    def descargarModAsync(mod_id, ruta_destino):
        
    
        url = f"https://api.modrinth.com/v2/version/{mod_id}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data:
                files = data.get("files", [])
                download_url = files[0].get("url") 
                mod_name = files[0].get("filename")
                mod_path = os.path.join(ruta_destino, f"{mod_name}")

                download_file(mod_path, download_url)
                return mod_path
            else:
                print("No se encontró ninguna versión del mod.")
        else:
            print("Error al obtener el mod:", response.status_code)
        return None
    hilo = threading.Thread(target=descargarModAsync, args=(mod_id, ruta_destino))
    hilo.start()

def getOnlineServers():
    
    listaServer = []
    # Iterar sobre todos los procesos del sistema
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Solo procesos que usan Java
            if "java" in proc.info['name'].lower():
                cmdline = " ".join(proc.info['cmdline'])
                
                if any(keyword in cmdline for keyword in ["vanilla", "forge", "fabric", "neoforge"]):
                    
                    path = cmdline.replace("\\", "/")
                    path = path.split("servers")[1]
                    nombre = path.split("/")[1]
                    
                    listaServer.append(nombre)
                    print(nombre)

        except Exception as e:
            print("Error al acceder al proceso:", e)
    return listaServer
    