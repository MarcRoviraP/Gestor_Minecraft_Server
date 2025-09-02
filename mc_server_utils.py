import requests
import os
import re
import json
import psutil
import threading
import asyncio
import aiohttp
import xml.etree.ElementTree as ET

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
    
def getAllNeoforgeVersions():
   
    url = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"

    # Descargar XML
    response = requests.get(url)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    # Extraer versiones
    versions = [v.text for v in root.findall(".//versions/version")]

    # Filtrar major.minor únicos
    filtered_major_minor = sorted(set(".".join(v.split(".")[:2]) for v in versions))
    filtered_major_minor.reverse()  # Mayor a menor

    last_versions = []

    for mm in filtered_major_minor:
        # Filtrar solo las versiones de este major.minor
        subset = [v for v in versions if v.startswith(mm)]

        # Ordenar por el 3er octeto numérico
        subset_sorted = sorted(
            subset,
            key=lambda v: int(re.match(r'\d+', v.split(".")[2]).group()),
            reverse=True
        )

        # Tomar la mayor
        last_versions.append(f"1.{mm} - {subset_sorted[0]}")
    last_versions.pop()
    return last_versions

def downloadJARNeoforge(version, ruta_destino):
    #https://maven.neoforged.net/releases/net/neoforged/neoforge/21.8.34/neoforge-21.8.34-installer.jar
    url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{version}/neoforge-{version}-installer.jar"
    download_file(ruta_destino, url)

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



def obtener_todos_mods(tipo, version, offset=0, stop=99999999999999, limit=100, filtro=None):
    """
    Descarga todos los mods de un tipo y versión usando la API de Modrinth.
    Si se pasa `filtro`, solo devuelve mods cuyo nombre comience con ese filtro.
    """

    async def obtener_todos_mods_async(tipo, version, offset=0, stop=99999999999999, limit=100, filtro=None):
        todos_mods = []

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
                    ]),
                }

                # Si hay filtro, lo mandamos como `query`
                if filtro:
                    params["query"] = filtro  

                async with session.get("https://api.modrinth.com/v2/search", params=params) as response:
                    data = await response.json()
                    hits = data.get("hits", [])
                    if not hits:
                        break

                    # Aquí aplicamos el "empieza con"
                    if filtro:
                        hits = [
                            mod for mod in hits
                            if mod["title"].lower().startswith(filtro.lower())
                        ]

                    todos_mods.extend(hits)

                    if len(todos_mods) >= stop:
                        break
                    offset += limit

        return todos_mods

    return asyncio.run(obtener_todos_mods_async(tipo, version, offset, stop, limit, filtro))


def descargarMod(mod_id, ruta_destino,mod_name):
    
    
    def descargarModAsync(mod_id, ruta_destino,mod_name):
        
    
        url = f"https://api.modrinth.com/v2/version/{mod_id}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            if data:
                files = data.get("files", [])
                download_url = files[0].get("url") 
                print("Mod ID:", mod_id)
                
                mod_path = os.path.join(ruta_destino, f"{mod_name.replace(' ','_')}.jar")

                download_file(mod_path, download_url)
                return mod_path
            else:
                print("No se encontró ninguna versión del mod.")
        else:
            print("Error al obtener el mod:", response.status_code)
        return None
    hilo = threading.Thread(target=descargarModAsync, args=(mod_id, ruta_destino,mod_name))
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

def stopServer(server):

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
                    if nombre == server:
                        proc.terminate()
                    return

        except Exception as e:
            print("Error al acceder al proceso:", e)
    return