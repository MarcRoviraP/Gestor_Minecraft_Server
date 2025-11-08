import pathlib
import platform
import sys
import os
import subprocess
import shutil
import json
import zipfile
import requests
import uuid
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from functools import partial
from pathlib import Path

from ImgCache import ImageCache
from fs_utils import mkdir_if_not_exists
from iconDownloader import IconDownloader, IconResult
from mainwindow import Ui_MainWindow
import mc_server_utils
import fs_utils


base_path = os.path.join(os.path.expanduser("~"), "MinecraftServers")
server_path = os.path.join(base_path, "servers")
jars_path = os.path.join(base_path, "jars")


[mkdir_if_not_exists(path) for path in [server_path, jars_path]]

class Window(QMainWindow):
    def __init__(self, cache, parent=None):
        super().__init__(parent)
        self.cache = cache
        self.offsetMods = 0
        self.listaServidoresOnline = []
        self.listaServidoresOnline = mc_server_utils.getOnlineServers()
        self.lastServer = ""
        self.setWindowTitle("Gestor de Servidores Minecraft")
        self.main_window = Ui_MainWindow()
        self.main_window.setupUi(self)
        
        self.difficulty_radio_group = QButtonGroup(self)
        self.difficulty_radio_group.addButton(self.main_window.peacefulBtn, 0)
        self.difficulty_radio_group.addButton(self.main_window.easyBtn, 1)
        self.difficulty_radio_group.addButton(self.main_window.normalBtn, 2)
        self.difficulty_radio_group.addButton(self.main_window.hardBtn, 3)
        
        
        self.gamemode_radio_group = QButtonGroup(self)
        self.gamemode_radio_group.addButton(self.main_window.survivalBtn, 0)
        self.gamemode_radio_group.addButton(self.main_window.creativeBtn, 1)
        self.gamemode_radio_group.addButton(self.main_window.adventureBtn, 2)
        self.gamemode_radio_group.addButton(self.main_window.spectatorBtn, 3)
        
        self.main_window.modWidget.setVisible(False)
        
        # Timer para buscar mods
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        # Whitelist 
        self.main_window.configurePropertiesWidget.setVisible(False)
        self.main_window.widgetWhiteList.setVisible(self.main_window.Whitelist.isChecked())

        def comprobarServidoresOnline():
            listaAux = mc_server_utils.getOnlineServers()

            if listaAux != self.listaServidoresOnline:
                self.listaServidoresOnline = listaAux
                print("Servidores en línea:", self.listaServidoresOnline)
                self.reloadServers()
        self.timer = QTimer(self)
        
        self.timer.timeout.connect(comprobarServidoresOnline)
        self.timer.start(5000)  # Comprobar cada 5 segundos

        def showWhiteList(checked):
            if checked:
                self.reloadWhiteList()
                print("Reload checked")

            self.main_window.widgetWhiteList.setVisible(checked)
        self.main_window.Whitelist.toggled.connect(showWhiteList)

        #Abrir dialogo de crear servidor
        self.main_window.createServerBtn.clicked.connect(self.spawnDialog)
        
        # Recargar servidores al iniciar
        self.reloadServers()
        
        # Add player list
        self.main_window.buttonAddWhiteList.clicked.connect(self.insertUserWhiteList)
        #Save properties
        self.main_window.saveProperties.clicked.connect(self.saveProperties)

        #Crear directorio base si no existe
        self.crearBaseFolders()
        

    def exportModPack(self, server):
        rutaServer = os.path.join(server_path, server)
        rutaMods = os.path.join(rutaServer, "mods")
    
        print(f"Exportando modpack para el servidor {server}...")
    
        # Todos los .jar dentro de la carpeta mods
        jars = [os.path.join(rutaMods, f) for f in os.listdir(rutaMods) if f.endswith(".jar")]
    
        # Pedir al usuario dónde guardar el zip
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo ZIP",
            str(pathlib.Path.home() / f"{server}_mods.zip"),
            "Zip Files (*.zip)"
        )
    
        if filename:
            with zipfile.ZipFile(filename, "w") as zipf:
                for jar in jars:
                    # Solo meter "mods/archivo.jar" en el zip
                    arcname = os.path.join("mods", os.path.basename(jar))
                    zipf.write(jar, arcname)
    
            print(f"ZIP guardado en: {filename}")
    

    def saveProperties(self):
        ruta = os.path.join(server_path, self.lastServer)
        if not os.path.exists(ruta):
            print(f"El servidor {self.lastServer} no existe.")
            return

        properties_path = os.path.join(ruta, "server.properties")
        new_properties = {
            "difficulty": self.difficulty_radio_group.checkedButton().text().lower(),
            "gamemode": self.gamemode_radio_group.checkedButton().text().lower(),
            "max-players": str(self.main_window.players.value()),
            "view-distance": str(self.main_window.chunks.value()),
            "server-port": str(self.main_window.portNumber.value()),
            "motd": self.main_window.serverNameEdit.text(),
            "online-mode": "true" if self.main_window.onlineMode.isChecked() else "false",
            "white-list": "true" if self.main_window.Whitelist.isChecked() else "false",
            "pvp": "true" if self.main_window.pvp.isChecked() else "false"
        }

        # Leer propiedades existentes
        existing = {}
        if os.path.exists(properties_path):
            with open(properties_path, "r") as f:
                for line in f:
                    if "=" in line:
                        key, value = line.strip().split("=", 1)
                        existing[key] = value

        # Actualizar/añadir propiedades
        existing.update(new_properties)

        # Escribir todas las propiedades
        with open(properties_path, "w") as f:
            for key, value in existing.items():
                f.write(f"{key}={value}\n")

        print("Propiedades guardadas correctamente.")
        
        self.loadProperties(self.lastServer)
        
    def loadProperties(self,server):
        self.lastServer = server
        ruta = os.path.join(server_path, server)
        if not os.path.exists(ruta):
            print(f"El servidor {server} no existe.")
            return
        
        properties_path = os.path.join(ruta, "server.properties")
        if not os.path.exists(properties_path):
            print("No se encontró el archivo server.properties.")
            return

        with open(properties_path, 'r') as f:
            properties = f.read()
            #print(f"Propiedades del servidor {server}:\n{properties}")

        for line in properties.splitlines():
            if line.startswith("difficulty="):
                difficulty = line.split("=")[1].strip()
                if difficulty == "peaceful":
                    self.main_window.peacefulBtn.setChecked(True)
                elif difficulty == "easy":
                    self.main_window.easyBtn.setChecked(True)
                elif difficulty == "normal":
                    self.main_window.normalBtn.setChecked(True)
                elif difficulty == "hard":
                    self.main_window.hardBtn.setChecked(True)

            elif line.startswith("gamemode="):
                gamemode = line.split("=")[1].strip()
                if gamemode == "survival":
                    self.main_window.survivalBtn.setChecked(True)
                elif gamemode == "creative":
                    self.main_window.creativeBtn.setChecked(True)
                elif gamemode == "adventure":
                    self.main_window.adventureBtn.setChecked(True)
                elif gamemode == "spectator":
                    self.main_window.spectatorBtn.setChecked(True)
                    
            elif line.startswith("max-players="):
                max_players = line.split("=")[1].strip()
                self.main_window.players.setValue(int(max_players))
            elif line.startswith("view-distance="):
                view_distance = line.split("=")[1].strip()
                self.main_window.chunks.setValue(int(view_distance))
            elif line.startswith("server-port="):
                server_port = line.split("=")[1].strip()
                self.main_window.portNumber.setValue(int(server_port))
            elif line.startswith("motd="):
                motd = line.split("=")[1].strip()
                self.main_window.serverNameEdit.setText(motd)
            elif line.startswith("online-mode="):
                online_mode = line.split("=")[1].strip()
                self.main_window.onlineMode.setChecked(online_mode.lower() == "true")
            elif line.startswith("white-list="):
                white_list = line.split("=")[1].strip()
                self.main_window.Whitelist.setChecked(white_list.lower() == "true")
            elif line.startswith("pvp="):
                pvp = line.split("=")[1].strip()
                self.main_window.pvp.setChecked(pvp.lower() == "true")
                
        # Recargar la lista blanca de forma asíncrona después de cargar las propiedades
        QTimer.singleShot(10, self.reloadWhiteList)
        print("Reload load properties")

    def insertUserWhiteList(self):
        user_name = self.main_window.nametagPlayer.text()
        if user_name:
            write_list_path = os.path.join(server_path, self.lastServer, "whitelist.json")
            if not os.path.exists(write_list_path):
                with open(write_list_path, 'w') as f:
                    json.dump([], f)
            with open(write_list_path, 'r+') as f:
                white_list = json.load(f)
                # Verificar si el usuario ya está en la lista
                if any(user['name'] == user_name for user in white_list):
                    print(f"El usuario {user_name} ya está en la lista blanca.")
                    return
                
                url = f"https://api.mojang.com/users/profiles/minecraft/{user_name}"
                
                response = requests.get(url)
                if response.status_code != 200:
                    self.showWarningDialog(f"❌ Error al obtener el usuario {user_name}", "Error al obtener usuario")
                    return
                user_data = response.json()
                if not user_data:
                    self.showWarningDialog(f"❌ Usuario {user_name} no encontrado.", "Usuario no encontrado")
                    return
                user_id = user_data.get("id", user_name)

                user_id = str(uuid.UUID(user_id))  # Convertir a UUID si es necesario
                user_name = user_data.get("name", user_name)
                # Añadir el nuevo usuario
                white_list.append({"uuid": user_id, "name": user_name})
                f.seek(0)
                f.write(json.dumps(white_list, indent=4))
                f.truncate()

            self.reloadWhiteList()
            print("Reload insert")
            self.main_window.nametagPlayer.clear()

    def reloadWhiteList(self):
        
        self.main_window.whiteList.clear()
        ruta = os.path.join(server_path, self.lastServer)
        if not os.path.exists(ruta):
            print(f"El servidor {self.lastServer} no existe.")
            return
        
        white_list_path = os.path.join(ruta, "whitelist.json")
        if not os.path.exists(white_list_path):
            print("No se encontró el archivo whitelist.json.")
            return
        
        with open(white_list_path, 'r') as f:
            white_list = json.load(f)
        self.thread_pool_users = getattr(self, 'thread_pool_users', QThreadPool())
        
        self.avatar_signals = IconResult()
        self.avatar_signals.finished.connect(self.icon_ready)
        icon_labels = {}  # para mapear widgets y actualizarlos luego
        for entry in white_list:
            nameTag = entry.get('name', 'Unknown')
            item = QListWidgetItem()
            borrarButton = QPushButton("")
            borrarButton.setProperty("btnType", "icon")
            borrarButton.setIconSize(QSize(24, 24))
            borrarButton.setIcon(QIcon(fs_utils.resource_path("minecraft/ico/delete.png")))
            borrarButton.setToolTip("Borrar de la lista blanca")
            borrarButton.clicked.connect(partial(self.removeUserFromWhiteList, entry))
            
            iconLabel = QLabel()
            iconLabel.setFixedSize(32, 32)
            icon_labels[nameTag] = iconLabel

            widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(iconLabel)
            layout.addWidget(QLabel(nameTag))
            layout.addStretch()
            layout.addWidget(borrarButton)
            layout.addStretch()
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())
            self.main_window.whiteList.addItem(item)
            self.main_window.whiteList.setItemWidget(item, widget)
            
            avatar_url = f"https://minotar.net/avatar/{nameTag}/32"
            
            if avatar_url:
                downloader = IconDownloader(avatar_url, self.cache, iconLabel,self.avatar_signals)
                self.thread_pool_users.start(downloader)
            
            
    def removeUserFromWhiteList(self, entry):
        # Find the QListWidgetItem corresponding to the entry
        for i in range(self.main_window.whiteList.count()):
            item = self.main_window.whiteList.item(i)
            widget = self.main_window.whiteList.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel)
                if label and label.text() == entry.get('name'):
                    self.main_window.whiteList.removeItemWidget(item)
                    self.main_window.whiteList.takeItem(i)
                    break
        ruta = os.path.join(server_path, self.lastServer, "whitelist.json")
        if not os.path.exists(ruta):
            print(f"El servidor {self.lastServer} no existe.")
            return
        with open(ruta, 'r+') as f:
            white_list = json.load(f)
            # Filtrar la lista blanca para eliminar el usuario
            white_list = [user for user in white_list if user.get('name') != entry.get('name')]
            f.seek(0)
            f.write(json.dumps(white_list, indent=4))
            f.truncate()

    def reloadServers(self):
        self.main_window.listServers.clear()
        servidores = os.listdir(server_path)

        for server in servidores:
            online = server in self.listaServidoresOnline
            uri_server = os.path.join(server_path, server)
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(15)

            # Si el servidor está en línea
            if online:
                widget.setStyleSheet("""
                    QWidget {
                        background-color: #1f3b4d;
                        margin-bottom: 3px;
                    }
                """)
            # Icono servidor
            img = QLabel()
            icon_path = fs_utils.resource_path(os.path.join(uri_server, "server-icon.png"))
            if os.path.exists(icon_path):
                ico = QIcon(icon_path)
                img.setPixmap(ico.pixmap(64, 64))
            else:
                img.setPixmap(QPixmap(64, 64))  # Placeholder vacío

            # Nombre
            nombre = QLabel(server)
            nombre.setStyleSheet("font-weight: bold; font-size: 14px;")

            # Version info
            version = "N/A"
            tipo = "Desconocido"
            ruta_jar = ""
            ram_min = 1024
            ram_max = 2048

            version_file = os.path.join(uri_server, "versions.txt")
            try:
                with open(version_file, "r") as f:
                    version = f.readline().strip()
                    tipo = f.readline().strip()
                    ram_min = int(f.readline().strip())
                    ram_max = int(f.readline().strip())

             
                    jars = [f for f in os.listdir(uri_server) if f.endswith(".jar")]
                    ruta_jar = os.path.join(uri_server, jars[0]) if jars else ""

            except Exception as e:
                print(f"Error al leer '{version_file}' en '{server}': {e}")
                start_server_button = QPushButton("Recargar la APP")
                start_server_button.setEnabled(False)
                if not hasattr(self, "_reload_timer") or not self._reload_timer.isActive():
                    self._reload_timer = QTimer(self)
                    self._reload_timer.setSingleShot(True)
                    self._reload_timer.timeout.connect(self.reloadServers)
                    self._reload_timer.start(10000)
            else:
                
                if online:
                    # Botón cerrar servidor
                    stop_server_button = QPushButton("STOP")
                    stop_server_button.clicked.connect(partial(self.stopServer, server))
                else:
                    # Botón iniciar servidor
                    start_server_button = QPushButton("START")
                    # Obtener el valor correcto de 'version' para pasar a startServer
                    split_version = version.split()
                    print(f"Version split: {split_version}")
                    if len(split_version) > 1:
                        version = split_version[0]
                        version_param = split_version[2]
                    else:
                        version_param = version
                    start_server_button.clicked.connect(partial(self.startServer, server, ram_min, ram_max, ruta_jar, tipo, version_param))

            # Botón carpeta
            folder_button = QPushButton(QIcon(fs_utils.resource_path("minecraft/ico/folder.png")), "")
            folder_button.setToolTip("Abrir carpeta del servidor")
            folder_button.setProperty("btnType", "icon")
            folder_button.setFixedSize(32, 32)
            folder_button.clicked.connect(partial(QDesktopServices.openUrl, QUrl.fromLocalFile(uri_server)))

            # Botón Mods si aplica
            mods_button = QPushButton("Mods")
            mods_button.setToolTip("Abrir lista de mods")
            mods_button.setFixedHeight(32)
            mods_button.clicked.connect(partial(self.enterModsContext, server, tipo, version))
            # Layout texto
            version_label = QLabel(f"Versión: {version} ({tipo})")
            version_label.setStyleSheet("color: gray; font-size: 12px;")

            info_layout = QVBoxLayout()
            info_layout.addWidget(nombre)
            info_layout.addWidget(version_label)

            # Añadir al layout principal
            layout.addWidget(img)
            layout.addLayout(info_layout)
            layout.addStretch()
            layout.addWidget(folder_button)
            if tipo.lower() != "vanilla":
                layout.addWidget(mods_button)
            
            btnsLayout = QVBoxLayout()
            if online:
                layout.addWidget(stop_server_button)
            else:
                layout.addWidget(start_server_button)

            # Finalizar item en QListWidget
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, server)
            self.main_window.listServers.addItem(item)
            self.main_window.listServers.setItemWidget(item, widget)

        self.main_window.listServers.itemClicked.connect(self.handle_item_click)
       
    def stopServer(self, server):
        mc_server_utils.stopServer(server)
    def enterModsContext(self, server, tipo, version):

        print("Entrando al contexto de mods...")
        
        
        # Obtener mods instalados
        self.modsInstalados = os.listdir(os.path.join(server_path, server, "mods")) if os.path.exists(os.path.join(server_path, server, "mods")) else []
        self.modsInstalados = [mod.replace("_", " ").replace(".jar", "") for mod in self.modsInstalados]
        print(f"Mods instalados en {server}: {self.modsInstalados}")
        
        self.main_window.modWidget.setVisible(True)
        self.main_window.configurePropertiesWidget.setVisible(False)
        self.search_timer.timeout.connect(partial(self.showMods, server, tipo, version))

        self.main_window.editBuscarMods.textChanged.connect(partial(self.search_timer.start, 200))  # Iniciar el timer con un delay de 200 ms
        self.showMods(server, tipo, version)
        self.showInstalledMods(server)


        self.main_window.modsListWidget.verticalScrollBar().valueChanged.connect(
            partial(self.scrollModsList, server=server, tipo=tipo, version=version)
        )
        
        #Exportar mods
        self.main_window.exportModPack.clicked.connect(partial(self.exportModPack, server))
        self.main_window.exportModPack.setToolTip("Exportar mods instalados en un archivo ZIP")
    def scrollModsList(self, value, server, tipo, version):
        maximum = self.main_window.modsListWidget.verticalScrollBar().maximum()
        if maximum == 0:
            return
        if value >= maximum and not self.tope:
            print(f"Scroll bar alcanzó el máximo: {maximum}")
            self.offsetMods += 100
            self.showMods(server, tipo, version, append=True)

    def showInstalledMods(self, server):
        print("Mostrando mods instalados...")
        self.main_window.instaledModsList.clear()
        for mod in self.modsInstalados:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)

            name_label = QLabel(mod)

            delete_button = QPushButton("❌")
            delete_button.setToolTip("Desinstalar mod")
            delete_button.clicked.connect(
                partial(self.uninstall_mod, mod, server)
            )
            layout.addWidget(name_label)
            layout.addStretch()
            layout.addWidget(delete_button)

            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.main_window.instaledModsList.addItem(item)
            self.main_window.instaledModsList.setItemWidget(item, widget)

    def uninstall_mod(self, mod: str, server: str):
        try:
            # Construye la ruta esperada
            mods_folder = Path(server_path) / server / "mods"
            safe_name = mod.replace(" ", "_") + ".jar"
            mod_path = mods_folder / safe_name

            # Resuelve enlaces simbólicos y normaliza
            mod_path = mod_path.resolve()

            # Verifica que esté dentro de la carpeta mods
            if not mod_path.is_relative_to(mods_folder.resolve()):
                raise ValueError("Ruta de mod no válida.")

            if not mod_path.is_file():
                self.showWarningDialog("El mod no existe.", "Error")
                return

            mod_path.unlink()
            self.modsInstalados.remove(mod)
            self.showInstalledMods(server)

        except ValueError as e:
            self.showWarningDialog(str(e), "Error de seguridad")
        except Exception as e:
            self.showWarningDialog(f"No se pudo desinstalar el mod: {e}", "Error")
        
    def showMods(self, server, tipo, version, append=False):
        print("Mostrando mods...")
        print("Versión:", version)
        filtro = self.main_window.editBuscarMods.text().strip()
        # Solo limpiar si es la primera carga
        if not append:
            self.tope = False
            self.main_window.modsListWidget.clear()
            self.offsetMods = 0

        stop = 100
        mods = mc_server_utils.obtener_todos_mods(
            tipo,
            version,
            offset=self.offsetMods,
            stop=stop,
            limit=100,
            filtro=filtro
        )

        self.tope = len(mods) < stop

        if not mods:
            if not append:  # Solo mostrar aviso si es la primera carga
                self.showWarningDialog("No se encontraron mods para este servidor.", "No hay mods")
            return

        self.thread_pool = getattr(self, 'thread_pool', QThreadPool())
        self.icon_signals = IconResult()
        self.icon_signals.finished.connect(self.icon_ready)
        self.icon_labels = getattr(self, 'icon_labels', {})

        for mod in mods:
            name_label = QLabel(mod['title'])
       

            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)

            icon_label = QLabel()
            icon_label.setFixedSize(32, 32)
            self.icon_labels[mod['slug']] = icon_label

            version_label = QLabel(f"Versión: {version}")
            name_label.setStyleSheet("font-weight: bold")
            name_label.setMaximumWidth(200)
            info_layout = QVBoxLayout()
            info_layout.addWidget(name_label)
            info_layout.addWidget(version_label)

            title = mod['title']
            download_button = QPushButton()
            if title in self.modsInstalados:
                download_button.setText("✔ Instalado")
                download_button.setToolTip("Mod ya instalado")
            else:
                download_button.setText("⬇ Descargar")
                download_button.setToolTip("Descargar mod")
                download_button.clicked.connect(
                    partial(self.descargar_mod, title, mod['latest_version'], server, download_button)
                )

            
            layout.addWidget(icon_label)
            layout.addLayout(info_layout)
            layout.addStretch()
            layout.addWidget(download_button)

            item = QListWidgetItem()
            item.setToolTip(title + " - " + version)
            item.setSizeHint(widget.sizeHint())
            self.main_window.modsListWidget.addItem(item)
            self.main_window.modsListWidget.setItemWidget(item, widget)

            url = mod.get('icon_url', '')
            if url:
                downloader = IconDownloader(url, self.cache, icon_label, self.icon_signals)
                self.thread_pool.start(downloader)

    def descargar_mod(self, title, version, server, download_button):
        destino = os.path.join(server_path, server, "mods")
        mc_server_utils.descargarMod(version, destino, title)
        download_button.setText("✔ Instalado")
        download_button.setToolTip("Mod ya instalado")
        download_button.clicked.disconnect()
        self.modsInstalados.append(title)
        self.showInstalledMods(server)

        print(f"Descargando mod {title} versión {version} a {destino}")
    def icon_ready(self, url, img_data, widget):
        #print(f"Icono listo para {url}")
        try:
            if img_data:
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                widget.setPixmap(pixmap.scaled(32, 32))
                #print(f"Icono descargado y asignado para {url}")
            else:
                widget.setText("❌")
                print(f"[IconDownloader] Error: No se pudo descargar el icono de {url}")
        except Exception as e:
            #print(f"[IconDownloader] Error: {e}")
            pass
        
    def handle_item_click(self, item):
        self.main_window.configurePropertiesWidget.setVisible(True)
        self.main_window.modWidget.setVisible(False)
        serverName = item.data(Qt.ItemDataRole.UserRole)
        
        self.loadProperties(serverName)

    def crearBaseFolders(self):
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            os.makedirs(os.path.join(jars_path))
            os.makedirs(os.path.join(server_path))
        return base_path

    def spawnDialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Crear Servidor")
        dlg.setGeometry(100, 100, 500, 300)
        dlg.setModal(True)

        # --- Widgets ---
        nombreLabel = QLabel("&Nombre del servidor:")
        nombreEdit = QLineEdit()
        nombreLabel.setBuddy(nombreEdit)

        versionLabel = QLabel("&Versión de Minecraft:")
        versionCombo = QComboBox()
        versionCombo.addItems(mc_server_utils.obtener_versiones_minecraft())  # Aquí puedes cargar dinámicamente
        versionLabel.setBuddy(versionCombo)

        tipoLabel = QLabel("&Tipo de servidor:")
        tipoCombo = QComboBox()
        tipoCombo.addItems(["Vanilla", "Forge", "Fabric","NeoForge"])
        tipoLabel.setBuddy(tipoCombo)

        minRamLabel = QLabel("RAM mínima (MB):")
        minRamSpin = QSpinBox()
        minRamSpin.setRange(512, 32000)
        minRamSpin.setValue(2048)

        maxRamLabel = QLabel("RAM máxima (MB):")
        maxRamSpin = QSpinBox()
        maxRamSpin.setRange(512, 64000)
        maxRamSpin.setValue(4096)

        seedLabel = QLabel("&Seed:")
        seedEdit = QLineEdit()
        seedLabel.setBuddy(seedEdit)
        # --- Botones ---
        createButton = QPushButton("Crear")
        cancelButton = QPushButton("Cancelar")
        
        # --- Checkbox ---
        
        hardcoreCheck = QCheckBox("Hardcore") 

        # --- Layouts ---
        formLayout = QFormLayout()
        formLayout.addRow(nombreLabel, nombreEdit)
        formLayout.addRow(tipoLabel, tipoCombo)
        formLayout.addRow(versionLabel, versionCombo)
        formLayout.addRow(minRamLabel, minRamSpin)
        formLayout.addRow(maxRamLabel, maxRamSpin)
        formLayout.addRow(seedLabel, seedEdit)
        formLayout.addRow(hardcoreCheck)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(createButton)
        buttonLayout.addWidget(cancelButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(buttonLayout)
        dlg.setLayout(mainLayout)

        # --- Conexiones ---
        tipoCombo.currentTextChanged.connect(lambda text: self.reloadVersions(text, versionCombo))

        createButton.clicked.connect(lambda: self.crearServidor(
            nombreEdit.text(),
            versionCombo.currentText(),
            tipoCombo.currentText(),
            minRamSpin.value(),
            maxRamSpin.value(),
            seedEdit.text(),
            hardcoreCheck.isChecked(),
            dlg
        ))
        cancelButton.clicked.connect(dlg.reject)

        
        dlg.exec()

    def reloadVersions(self, tipo, versionCombo):
        versionCombo.clear()
        if tipo == "Vanilla":
            versionCombo.addItems(mc_server_utils.obtener_versiones_minecraft())
        elif tipo == "Forge":
            versionCombo.addItems(mc_server_utils.getMinecraftVersionFromForge())
        elif tipo == "Fabric":
            versionCombo.addItems(mc_server_utils.getAllFabricVersions())
        elif tipo == "NeoForge":
            versionCombo.addItems(mc_server_utils.getAllNeoforgeVersions())
    
    def writeProperties(self, ruta, text):
        server_properties_path = os.path.join(ruta, "server.properties")
        # Si no existe, crea el fichero y escribe la línea
        if not os.path.exists(server_properties_path):
            with open(server_properties_path, "w") as f:
                f.write(text)
        else:
            # Si existe, añade la línea al final
            with open(server_properties_path, "a") as f:
                f.write(text)

        
    def aceptar_eula(self,base_path, nombre):

        actual_server_path = os.path.join(server_path, nombre)
        eula_path = os.path.join(actual_server_path, "eula.txt")

        os.makedirs(actual_server_path, exist_ok=True)

        if not os.path.exists(eula_path):
            with open(eula_path, "w") as f:
                f.write("# By changing the setting below to TRUE you are indicating your agreement to the EULA.\n")
                f.write("eula=true\n")
            print("Archivo eula.txt creado y EULA aceptada.")
            return

        with open(eula_path, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if line.startswith("eula="):
                if "true" in line.lower():
                    print("EULA ya aceptada.")
                    return
                else:
                    lines[i] = "eula=true\n"
                    with open(eula_path, "w") as f:
                        f.writelines(lines)
                    print("EULA modificada a true.")
                    return

        lines.append("eula=true\n")
        with open(eula_path, "w") as f:
            f.writelines(lines)
        print("EULA añadida y aceptada.")

    def showWarningDialog(self, message,title="Advertencia"):
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Icon.Warning)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.exec()

    # Dentro de tu clase Window
    def crearServidor(self, nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog):
        if not nombre.strip():
            self.showWarningDialog("El nombre del servidor no puede estar vacío.", "Error")
            return
        if (Path(server_path) / nombre).exists():
            self.showWarningDialog("Ya existe un servidor con ese nombre.", "Error")
            return

        # Crear barra de progreso
        self.progress = ProgressDialog(self, "Creando servidor...")
        self.progress.show()

        # Crear worker y thread
        self.thread = QThread()
        self.worker = ServerCreatorWorker(nombre, version, tipo, ram_min, ram_max, seed, hardcore)
        self.worker.moveToThread(self.thread)

        # Conectar señales
        self.thread.started.connect(self.worker.run)
        self.worker.message.connect(self.progress.set_texto)
        self.worker.progress.connect(self.progress.set_valor)
        self.worker.finished.connect(self._crearServidor_terminado)
        self.worker.error.connect(lambda msg: self.showWarningDialog(msg, "Error"))
        self.progress.cancelled.connect(self.worker.cancelar)

        # Lanzar
        self.thread.start()
        dialog.accept()

    def _crearServidor_terminado(self, ok):
        self.thread.quit()
        self.thread.wait()
        self.progress.finalizar()
        if ok:
            self.reloadServers()

    def setup_minecraft_server_neoforge(self, nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog):

        versionNeoForge = version.split()[2]
        jarName = f"{jars_path}/neoforge_{versionNeoForge}_server.jar"
        if not os.path.exists(jarName):
            mc_server_utils.downloadJARNeoforge(versionNeoForge, jarName)
            
        os.makedirs(os.path.join(server_path, nombre), exist_ok=True)
        
        command = [
            "java",
            "-jar",
            jarName,
            "--installServer"
            ]

        subprocess.run(command, cwd=f"{server_path}/{nombre}", check=True)

        self.writeBeforeLaunchSettings(nombre, seed, hardcore, version, tipo, ram_min, ram_max)
        serverJAR = f"{server_path}/{nombre}/{versionNeoForge}.jar"
        pathInternalJar = os.path.join(server_path, nombre,"libraries","net","neoforged","neoforge", versionNeoForge,f"neoforge-{versionNeoForge}-server.jar")
        pathUniversalInternalJar = os.path.join(server_path, nombre,"libraries","net","neoforged","neoforge", versionNeoForge,f"neoforge-{versionNeoForge}-universal.jar")
        if os.path.exists(pathInternalJar):
            shutil.copy(pathInternalJar, serverJAR)
        elif os.path.exists(pathUniversalInternalJar):
            shutil.copy(pathUniversalInternalJar, serverJAR)
        else:
            print("No se encontró el archivo JAR del servidor NeoForge.")
            self.showWarningDialog("No se encontró el archivo JAR del servidor NeoForge.", "Error al crear servidor")
            return
        self.startServer(nombre, ram_min, ram_max, serverJAR, tipo,versionNeoForge)
        dialog.accept()

    def setup_minecraft_server_fabric(self, nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog):

        jarName = f"{jars_path}/fabric_{version}_server.jar"
        if not os.path.exists(jarName):
            mc_server_utils.downloadJARFabric(version, jarName)
            print(jarName + " Descargado")
            
        os.makedirs(os.path.join(server_path, nombre), exist_ok=True)
        
        command = [
            "java",
            "-jar",
            jarName,
            "--installServer"
            ]

        subprocess.run(command, cwd=f"{server_path}/{nombre}", check=True)
        self.writeBeforeLaunchSettings(nombre, seed, hardcore, version, tipo, ram_min, ram_max)
        self.startServer(nombre, ram_min, ram_max, f"{server_path}/{nombre}/.fabric/server/{version}-server.jar", tipo,version)

        dialog.accept()


    def setup_minecraft_server_forge(self, nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog):

        forgeVersion = mc_server_utils.getRecommendedForgeVersion(version).split("-")[1]
        mcVersion = version
        
        installerName = (f"forge-{mcVersion}-{forgeVersion}-installer.jar")
        # Comprobar si el instalador ya existe
        if not os.path.exists(f"{jars_path}/{installerName}"):
            mc_server_utils.downloadJARInstallerForge(mcVersion, forgeVersion, f"{jars_path}/{installerName}")
        
        os.makedirs(os.path.join(server_path, nombre), exist_ok=True)
        
        command = [
            "java",
            "-jar",
            os.path.join(jars_path, installerName),
            "--installServer"
            ]

        subprocess.run(command, cwd=f"{server_path}/{nombre}", check=True)

        self.writeBeforeLaunchSettings(nombre, seed, hardcore, version, tipo, ram_min, ram_max)

        self.startServer(nombre, ram_min, ram_max, f"{server_path}/{nombre}/forge-{mcVersion}-{forgeVersion}-shim.jar", tipo,version)
        dialog.accept()

         
    def setup_minecraft_server_vanilla(self, nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog):
        nombreJar = f"{version}_server_vanilla.jar"

        if not os.path.exists(f"{jars_path}/{nombreJar}"):
            mc_server_utils.descargar_server_jar(
                mc_server_utils.obtener_jar_servidor(version),
                f"{jars_path}/{nombreJar}"
            )

        self.writeBeforeLaunchSettings(nombre, seed, hardcore, version,tipo,ram_min, ram_max)

        rutaJarInicial = os.path.join(jars_path, nombreJar)
        rutaJarFinal = os.path.join(server_path, nombre, "server_vanilla.jar")
        shutil.copy(rutaJarInicial, rutaJarFinal)
        # Lanzamos el servidor
        self.startServer(nombre, ram_min, ram_max, rutaJarFinal, tipo, version)

        print(f"Creando servidor '{nombre}' con versión {version}, tipo {tipo}, RAM {ram_min}-{ram_max}MB.")
        # Recargar la lista de servidores
        self.main_window.listServers.clear()
        dialog.accept()

    def writeBeforeLaunchSettings(self, nombre, seed, hardcore, version,tipo,ram_min=1024, ram_max=2048):
        ruta = os.path.join(server_path, nombre)
        # Aquí aceptamos la EULA automáticamente
        self.aceptar_eula(base_path, nombre)

        if not os.path.exists(f"{ruta}/versions.txt"):
            with open(f"{ruta}/versions.txt", "w") as f:
                f.write(f"{version}\n")
                f.write(f"{tipo}\n")
                f.write(f"{ram_min}\n")
                f.write(f"{ram_max}\n")
        if hardcore:
            self.writeProperties(ruta, "hardcore=true\n")
        if seed:
            self.writeProperties(ruta, f"level-seed={seed}\n")

        shutil.copy(fs_utils.resource_path("minecraft/ico/server-icon.png"), f"{server_path}/{nombre}/")

    def startServer(self, nombre, ram_min, ram_max, rutaJar,tipo,version):
        if tipo.lower() != "neoforge":
            jar_command = ["java", f"-Xms{ram_min}M", f"-Xmx{ram_max}M", "-jar", rutaJar, "nogui"]
        else:
                # Ajustar RAM en user_jvm_args.txt
            jvm_args_file = os.path.join(server_path, nombre, "user_jvm_args.txt")
            with open(jvm_args_file, "w", encoding="utf-8") as f:
                f.write(f"-Xms{ram_min}M\n")
                f.write(f"-Xmx{ram_max}M\n")
            jar_command = ["java", "@user_jvm_args.txt", f"@{os.path.join(server_path, nombre, "libraries/net/neoforged/neoforge", version, "win_args.txt")}", "nogui"]

        jar_command_str = " ".join(jar_command)
        cwd = os.path.join(server_path, nombre)
        operating_system = platform.system().lower()
        try:
            print("Iniciando servidor con comando:", jar_command_str)
            if operating_system == 'windows':
                subprocess.Popen(jar_command, cwd=cwd, creationflags=subprocess.CREATE_NEW_CONSOLE)


            elif operating_system == 'linux':
                if shutil.which('ptyxis'):
                    subprocess.Popen(['ptyxis', '--', 'bash', '-c', f'cd "{cwd}" && {jar_command_str}'])
                elif shutil.which('gnome-terminal'):
                    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', f'cd "{cwd}" && {jar_command_str}; exec bash'])
                elif shutil.which('konsole'):
                    subprocess.Popen(['konsole', '-e', 'bash', '-c', f'cd "{cwd}" && {jar_command_str}; exec bash'])
                elif shutil.which('xterm'):
                    subprocess.Popen(['xterm', '-e', f'cd "{cwd}" && {jar_command_str}; bash'])
                else:
                    # Fallback: ejecuta en segundo plano sin TTY
                    subprocess.Popen(jar_command, cwd=cwd, start_new_session=True)

            else:
                print("OS not supported")

        except Exception as e:
            print("Error al iniciar el servidor:", e)
class ProgressDialog(QProgressDialog):
    cancelled = pyqtSignal()

    def __init__(self, parent, titulo="Creando servidor", maximo=0):
        super().__init__(titulo, "Cancelar", 0, maximo, parent)
        self.setWindowTitle(titulo)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setAutoClose(False)
        self.setAutoReset(False)
        self.canceled.connect(self.cancelled)

    def set_texto(self, texto):
        self.setLabelText(texto)

    def set_valor(self, valor):
        self.setValue(valor)

    def finalizar(self):
        self.setValue(self.maximum())
        self.close()
        

class ServerCreatorWorker(QObject):
    # Señales
    progress = pyqtSignal(int)          # 0-100
    message = pyqtSignal(str)           # texto informativo
    finished = pyqtSignal(bool)         # True = ok, False = cancelado/error
    error = pyqtSignal(str)

    def __init__(self, nombre, version, tipo, ram_min, ram_max, seed, hardcore):
        super().__init__()
        self.nombre = nombre
        self.version = version
        self.tipo = tipo
        self.ram_min = ram_min
        self.ram_max = ram_max
        self.seed = seed
        self.hardcore = hardcore
        self._cancelado = False

    def cancelar(self):
        self._cancelado = True

    def run(self):
        try:
            self.message.emit("Descargando archivos...")
            self.progress.emit(10)

            if self._cancelado:
                self.finished.emit(False)
                return

            # --- Lógica por tipo ---
            if self.tipo == "Vanilla":
                self._setup_vanilla()
            elif self.tipo == "Forge":
                self._setup_forge()
            elif self.tipo == "Fabric":
                self._setup_fabric()
            elif self.tipo == "NeoForge":
                self._setup_neoforge()
            else:
                raise ValueError("Tipo de servidor no soportado")

            if self._cancelado:
                self.finished.emit(False)
                return

            self.progress.emit(100)
            self.message.emit("Servidor creado con éxito")
            self.finished.emit(True)

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)

    # ---------- SETUPS ----------
    def _setup_vanilla(self):
        from main import server_path, jars_path  # importación local para evitar circular
        jar_name = f"{self.version}_server_vanilla.jar"
        jar_orig = Path(jars_path) / jar_name
        if not jar_orig.exists():
            mc_server_utils.descargar_server_jar(
                mc_server_utils.obtener_jar_servidor(self.version),
                jar_orig
            )
        self.progress.emit(30)

        server_dir = Path(server_path) / self.nombre
        server_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(jar_orig, server_dir / "server_vanilla.jar")
        self._write_before_launch(server_dir)

    def _setup_forge(self):
        from main import server_path, jars_path
        forge_version = mc_server_utils.getRecommendedForgeVersion(self.version).split("-")[1]
        installer_name = f"forge-{self.version}-{forge_version}-installer.jar"
        installer_path = Path(jars_path) / installer_name
        if not installer_path.exists():
            mc_server_utils.downloadJARInstallerForge(self.version, forge_version, installer_path)
        self.progress.emit(30)

        server_dir = Path(server_path) / self.nombre
        server_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["java", "-jar", installer_path, "--installServer"], cwd=server_dir, check=True)
        self.progress.emit(70)

        shim = server_dir / f"forge-{self.version}-{forge_version}-shim.jar"
        if not shim.exists():
            raise FileNotFoundError("No se generó el shim de Forge")
        self._write_before_launch(server_dir)

    def _setup_fabric(self):
        from main import server_path, jars_path
        jar_name = f"fabric_{self.version}_server.jar"
        jar_path = Path(jars_path) / jar_name
        if not jar_path.exists():
            mc_server_utils.downloadJARFabric(self.version, jar_path)
        self.progress.emit(30)

        server_dir = Path(server_path) / self.nombre
        server_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["java", "-jar", jar_path, "--installServer"], cwd=server_dir, check=True)
        self.progress.emit(70)

        fabric_jar = server_dir / ".fabric" / "server" / f"{self.version}-server.jar"
        if not fabric_jar.exists():
            raise FileNotFoundError("No se generó el JAR de Fabric")
        self._write_before_launch(server_dir)

    def _setup_neoforge(self):
        from main import server_path, jars_path
        version_neo = self.version.split()[2]
        jar_name = f"neoforge_{version_neo}_server.jar"
        jar_path = Path(jars_path) / jar_name
        if not jar_path.exists():
            mc_server_utils.downloadJARNeoforge(version_neo, jar_path)
        self.progress.emit(30)

        server_dir = Path(server_path) / self.nombre
        server_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["java", "-jar", jar_path, "--installServer"], cwd=server_dir, check=True)
        self.progress.emit(70)

        # Buscar el JAR generado
        libs = server_dir / "libraries" / "net" / "neoforged" / "neoforge" / version_neo
        jar_server = next(libs.glob("neoforge-*-server.jar"), None)
        if not jar_server:
            jar_server = next(libs.glob("neoforge-*-universal.jar"), None)

            if not jar_server:
                raise FileNotFoundError("No se generó el JAR del servidor NeoForge")
        shutil.copy(jar_server, server_dir / f"{version_neo}.jar")
        self._write_before_launch(server_dir)

    def _write_before_launch(self, server_dir: Path):
        from main import server_path
        # Aceptar EULA
        (server_dir / "eula.txt").write_text("eula=true\n")
        # versions.txt
        (server_dir / "versions.txt").write_text(
            f"{self.version}\n{self.tipo}\n{self.ram_min}\n{self.ram_max}\n"
        )
        # server-icon.png
        icon_src = Path(fs_utils.resource_path("minecraft/ico/server-icon.png"))
        if icon_src.exists():
            shutil.copy(icon_src, server_dir / "server-icon.png")

if __name__ == "__main__":
    ico_path = Path(__file__).parent / "minecraft" / "ico" / "server_icon.ico"
    print(f"Icon path: {ico_path.resolve()}")
    # Create the application
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(fs_utils.resource_path("minecraft/ico/server_icon.ico")))
    # Create and show the application's main window
    cache = ImageCache()
    win = Window(cache)
    win.setWindowIcon(QIcon(fs_utils.resource_path("minecraft/ico/server_icon.ico")))
    win.show()
    # Run the application's main loop
    sys.exit(app.exec())