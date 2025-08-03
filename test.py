import requests
from bs4 import BeautifulSoup

def get_forge_versions(minecraft_version):
    base_url = "https://maven.minecraftforge.net/net/minecraftforge/forge/"
    headers = {
        "User-Agent": "Mozilla/5.0 (MarcCraftBot v1.0)"
    }
    response = requests.get(base_url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    versions = []

    for a in soup.find_all('a'):
        href = a.get('href')
        if href and href.startswith(minecraft_version):
            href = href.strip('/')
            installer_url = f"{base_url}{href}/forge-{href}-installer.jar"
            versions.append(installer_url)

    return versions

# Probar con una versión
mc_version = "1.16.5"
forge_versions = get_forge_versions(mc_version)

print(f"Forge installers para Minecraft {mc_version}:")
for v in forge_versions:
    print(v)
