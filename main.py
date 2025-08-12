import platform
import sys
import os
import subprocess
import shutil
import json
import requests
import uuid
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from functools import partial

from fs_utils import mkdir_if_not_exists
from iconDownloader import IconDownloader
from mainwindow import Ui_MainWindow
import mc_server_utils


base_path = os.path.join(os.path.expanduser("~"), "MinecraftServers")
server_path = os.path.join(base_path, "servers")
jars_path = os.path.join(base_path, "jars")


[mkdir_if_not_exists(path) for path in [server_path, jars_path]]

class Window(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)
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
        
        self.main_window.modsListWidget.setVisible(False)


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

        def on_whitelist_toggled(checked):
            if checked:
                self.reloadWhiteList()
                print("Reload checked")

            self.main_window.widgetWhiteList.setVisible(checked)
        self.main_window.Whitelist.toggled.connect(on_whitelist_toggled)

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
        icon_labels = {}  # para mapear widgets y actualizarlos luego
        for entry in white_list:
            nameTag = entry.get('name', 'Unknown')
            item = QListWidgetItem()
            borrarButton = QPushButton("")
            borrarButton.setProperty("btnType", "icon")
            borrarButton.setIconSize(QSize(24, 24))
            borrarButton.setIcon(QIcon("minecraft/ico/delete.png"))
            borrarButton.setToolTip("Borrar de la lista blanca")
            borrarButton.clicked.connect(partial(self.removeUserFromWhiteList, entry))
            
            iconLabel = QLabel()
            iconLabel.setFixedSize(32, 32)
            icon_labels[nameTag] = iconLabel

            widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(iconLabel)
            layout.addWidget(QLabel(nameTag))
            layout.addWidget(borrarButton)
            layout.addStretch()
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())
            self.main_window.whiteList.addItem(item)
            self.main_window.whiteList.setItemWidget(item, widget)
            
            avatar_url = f"https://minotar.net/avatar/{nameTag}/32"
            
            if avatar_url:
                downloader = IconDownloader(avatar_url, self.icon_ready, iconLabel)
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
        ruta = os.path.join(server_path, "servers", self.lastServer, "whitelist.json")
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
            uri_server = os.path.join(server_path, server)
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(15)

            # Si el servidor está en línea
            if server in self.listaServidoresOnline:
                widget.setStyleSheet("""
                    QWidget {
                        background-color: #1f3b4d;       /* Azul petróleo oscuro */
                        margin-bottom: 3px;
                    }
                """)
            # Icono servidor
            img = QLabel()
            icon_path = os.path.join(uri_server, "server-icon.png")
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
                # Botón iniciar servidor
                start_server_button = QPushButton("START")
                start_server_button.clicked.connect(partial(self.startServer, server, ram_min, ram_max, ruta_jar))

            # Botón carpeta
            folder_button = QPushButton(QIcon("minecraft/ico/folder.png"), "")
            folder_button.setToolTip("Abrir carpeta del servidor")
            folder_button.setProperty("btnType", "icon")
            folder_button.setFixedSize(32, 32)
            folder_button.clicked.connect(partial(QDesktopServices.openUrl, QUrl.fromLocalFile(uri_server)))

            # Botón Mods si aplica
            mods_button = QPushButton("Mods")
            mods_button.setToolTip("Abrir lista de mods")
            mods_button.setFixedHeight(32)
            mods_button.clicked.connect(partial(self.showMods, server, tipo, version))

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
            layout.addWidget(start_server_button)

            # Finalizar item en QListWidget
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, server)
            self.main_window.listServers.addItem(item)
            self.main_window.listServers.setItemWidget(item, widget)

        self.main_window.listServers.itemClicked.connect(self.handle_item_click)
       
    def showMods(self, server, tipo, version):
        self.main_window.modsListWidget.clear()
        self.main_window.modsListWidget.setVisible(True)
        self.main_window.configurePropertiesWidget.setVisible(False)
    
        mods = mc_server_utils.obtener_todos_mods(tipo, version)
        if not mods:
            self.showWarningDialog("No se encontraron mods para este servidor.", "No hay mods")
            return
    
        self.thread_pool = getattr(self, 'thread_pool', QThreadPool())  # asegúrate de tener uno
        self.icon_labels = {}  # para mapear widgets y actualizarlos luego
    
        for mod in mods:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
    
            # Etiqueta del ícono
            icon_label = QLabel()
            icon_label.setFixedSize(32, 32)
    
            # Guardar la referencia por si se necesita actualizar luego
            self.icon_labels[mod['slug']] = icon_label
    
            # Texto del mod
            name_label = QLabel(mod['title'])
            version_label = QLabel(f"Versión: {mod['latest_version']}")
            name_label.setStyleSheet("font-weight: bold")
            info_layout = QVBoxLayout()
            info_layout.addWidget(name_label)
            info_layout.addWidget(version_label)
    
            # Botón de descargar
            download_button = QPushButton("Descargar")
            download_button.clicked.connect(partial(self.descargar_mod, mod['slug'], mod['latest_version'],server))

            # Montar layout
            layout.addWidget(icon_label)
            layout.addLayout(info_layout)
            layout.addStretch()
            layout.addWidget(download_button)
    
            # Insertar en QListWidget
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            self.main_window.modsListWidget.addItem(item)
            self.main_window.modsListWidget.setItemWidget(item, widget)
    
            # Lanzar descarga del ícono en segundo plano
            url = mod.get('icon_url', '')
            if url:
                downloader = IconDownloader(url, self.icon_ready, icon_label)
                self.thread_pool.start(downloader)

    def descargar_mod(self, slug, version,server):
        destino = os.path.join(server_path,server, "mods")
        mc_server_utils.descargarMod(version, destino)

        print(f"Descargando mod {slug} versión {version} a {destino}")
    def icon_ready(self, url, img_data, icon_label):
        
        try:
            if img_data:
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                icon_label.setPixmap(
                    pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
        except Exception as e:
            pass
            
        
    def handle_item_click(self, item):
        self.main_window.configurePropertiesWidget.setVisible(True)
        self.main_window.modsListWidget.setVisible(False)
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

    def crearServidor(self, nombre, version, tipo, ram_min, ram_max,seed, hardcore, dialog):
        if not nombre.strip():
            self.showWarningDialog("El nombre del servidor no puede estar vacío.", "Error al crear servidor")
            return
        
        if os.path.exists(os.path.join(server_path, nombre)):
            self.showWarningDialog(f"Ya existe un servidor con el nombre '{nombre}'. Por favor, elige otro nombre.", "Error al crear servidor")
            return
        if tipo == "Vanilla":
            self.setup_minecraft_server_vanilla(nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog)
        elif tipo == "Forge":
            self.setup_minecraft_server_forge(nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog)
            
        elif tipo == "Fabric":
            self.setup_minecraft_server_fabric(nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog)


        elif tipo == "NeoForge":
            self.setup_minecraft_server_neoforge(nombre, version, tipo, ram_min, ram_max, seed, hardcore, dialog)
            
        self.reloadServers()

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

        self.startServer(nombre, ram_min, ram_max, f"{server_path}/{nombre}/forge-{mcVersion}-{forgeVersion}-shim.jar")
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
        self.startServer(nombre, ram_min, ram_max, rutaJarFinal)

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

        shutil.copy("minecraft/ico/server-icon.png", f"{server_path}/{nombre}/")

    def startServer(self, nombre, ram_min, ram_max, rutaJar):
        jar_command = ["java", f"-Xms{ram_min}M", f"-Xmx{ram_max}M", "-jar", rutaJar, "nogui"]
        jar_command_str = " ".join(jar_command)
        cwd = os.path.join(server_path, nombre)
        operating_system = platform.system().lower()
    
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

    




if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    # Create and show the application's main window
    win = Window()
    win.show()
    # Run the application's main loop
    sys.exit(app.exec())