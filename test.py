import requests

def obtener_jar_servidor(version_id="1.20.1"):
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

descargar_server_jar(obtener_jar_servidor("1.20.1"), "server.jar")