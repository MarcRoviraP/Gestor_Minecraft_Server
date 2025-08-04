import requests
import json

def obtener_todos_mods(tipo,version):
    todos_mods = []
    offset = 0  # offset para paginación, no index
    limit = 100

    while True:
        params = {
            "limit": limit,
            "offset": offset,
            "facets": json.dumps([["project_types:mod"], [f"categories:{tipo}"], [f"versions:{version}"], ["server_side:optional", "server_side:required"]])  # Solo mods para forge
        }
        response = requests.get("https://api.modrinth.com/v2/search", params=params)
        data = response.json()
        hits = data.get("hits", [])
        if not hits:
            break  # no hay más mods que traer
        todos_mods.extend(hits)
        offset += limit
        print(f"Descargados {len(todos_mods)} mods hasta ahora...")

    return todos_mods

mods = obtener_todos_mods()
print(f"Total mods descargados: {len(mods)}")
for mod in mods:
    print(f"Mod: {mod['title']} latest: {mod['latest_version']}")
