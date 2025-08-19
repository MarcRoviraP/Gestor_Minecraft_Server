import xml.etree.ElementTree as ET
import requests
import re

# URL del archivo maven-metadata.xml
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

print("Últimas versiones por major.minor:", last_versions)
