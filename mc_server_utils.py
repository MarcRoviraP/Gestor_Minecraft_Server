import requests

def obtener_versiones_minecraft():
    url = "https://piston-meta.mojang.com/mc/game/version_manifest.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        versiones = [v["id"] for v in data["versions"] if v["type"] == "release"]
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

