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
from mainwindow import Ui_MainWindow
import mc_server_utils


base_path = os.path.join(os.path.expanduser("~"), "MinecraftServers")
server_path = os.path.join(base_path, "servers")
jars_path = os.path.join(base_path, "jars")

[mkdir_if_not_exists(path) for path in [server_path, jars_path]]

class Window(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)
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

        # Whitelist 
        self.main_window.configurePropertiesWidget.setVisible(False)
        self.main_window.widgetWhiteList.setVisible(self.main_window.Whitelist.isChecked())
        def on_whitelist_toggled(checked):
            if checked:
                self.reloadWhiteList()
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
            print(f"Propiedades del servidor {server}:\n{properties}")

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
        
        for entry in white_list:
            nameTag = entry.get('name', 'Unknown')
            item = QListWidgetItem()
            borrarButton = QPushButton("")
            borrarButton.setProperty("btnType", "icon")
            borrarButton.setIconSize(QSize(24, 24))
            borrarButton.setIcon(QIcon("minecraft/ico/delete.png"))
            borrarButton.setToolTip("Borrar de la lista blanca")
            borrarButton.clicked.connect(partial(self.removeUserFromWhiteList, entry))
            try:
                avatar_url = f"https://minotar.net/avatar/{nameTag}/32"
                avatar_pixmap = QPixmap()
                avatar_pixmap.loadFromData(requests.get(avatar_url).content)
                icon = QIcon(avatar_pixmap)
            except Exception as e:
                print(f"Error al cargar el avatar de {nameTag}: {e}")
                icon = QIcon("minecraft/ico/default_avatar.png")
            item.setIcon(icon)
            widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(QLabel(nameTag))
            layout.addWidget(borrarButton)
            layout.addStretch()
            widget.setLayout(layout)
            item.setSizeHint(widget.sizeHint())
            self.main_window.whiteList.addItem(item)
            self.main_window.whiteList.setItemWidget(item, widget)
            
            
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
            uriServer = f"{server_path}/{server}"
            widget = QWidget()
            layout  = QHBoxLayout()
            img = QLabel()
            nombre = QLabel(server)
            ico = QIcon(f"{uriServer}/server-icon.png")
            button = QPushButton( "START")
            folderIcon = QIcon("minecraft/ico/folder.png")
            
            folderButton = QPushButton(folderIcon, "")
            folderButton.setProperty("btnType", "icon")
            folderButton.setToolTip("Abrir carpeta del servidor")

            version = "N/A"
            
            try:
                tipo = ""
                rutaJar = ""
                ram_min = 1024
                ram_max = 2048
                with open(f"{server_path}/{server}/versions.txt", "r") as f:
                    version = f.readline().strip()
                    tipo = f.readline().strip()
                    ram_min = int(f.readline().strip())
                    ram_max = int(f.readline().strip())
                if tipo == "Vanilla":
                    
                    nombreJar = f"{version}_server_vanilla.jar"
                    rutaJar = os.path.join(jars_path, nombreJar)
                elif tipo == "Forge":
                    lista = os.listdir(f"{server_path}/{server}")
                    jar = [f for f in lista if f.endswith(".jar")]
                    rutaJar = os.path.join(server_path, server, jar[0]) if jar else ""

                button.clicked.connect(partial(self.startServer, server, ram_min, ram_max, rutaJar))
                folderButton.clicked.connect(partial(QDesktopServices.openUrl, QUrl.fromLocalFile(uriServer)))

            except :
                button.setEnabled(False)
                button.setText("Recargar la APP")
                # Usar QTimer para recargar la lista después de 10 segundos
                # Evitar crear múltiples timers: solo crear uno si no hay otro activo
                if not hasattr(self, "_reload_timer") or not self._reload_timer.isActive():
                    self._reload_timer = QTimer(self)
                    self._reload_timer.setSingleShot(True)
                    self._reload_timer.timeout.connect(self.reloadServers)
                    self._reload_timer.start(10000)
                print(f"No se encontró la carpeta versions o JAR para el servidor {server}.")
            img.setPixmap(ico.pixmap(64, 64))
        
            versionLabel = QLabel(f"Versión: {version} ({tipo})")
            layoutInfo = QVBoxLayout()
            layoutInfo.addWidget(nombre)
            layoutInfo.addWidget(versionLabel)
            
            layout.addWidget(img)
            layout.addLayout(layoutInfo)
            layout.addStretch()
            layout.addWidget(button)
            layout.addWidget(folderButton)
            widget.setLayout(layout)
        
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, server)  # Guardar el nombre del servidor
            item.setSizeHint(widget.sizeHint())

            self.main_window.listServers.addItem(item)
            self.main_window.listServers.setItemWidget(item, widget)
        self.main_window.listServers.itemClicked.connect(self.handle_item_click)

        
    def handle_item_click(self, item):
        self.main_window.configurePropertiesWidget.setVisible(True)
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


        # Lanzamos el servidor
        self.startServer(nombre, ram_min, ram_max, f"{jars_path}/{nombreJar}")

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
            if shutil.which('gnome-terminal'):
                # Not tested
                subprocess.Popen(['gnome-terminal', '--'] + jar_command, cwd=cwd)
            elif shutil.which('konsole'):
                # Not tested
                subprocess.Popen(['konsole', '-e', 'bash', '-c', f'cd "{cwd}" && {jar_command_str}; exec bash'])
            elif shutil.which('xterm'):
                # Not tested
                subprocess.Popen(['xterm', '-e', f'cd "{cwd}" && {jar_command_str}; bash'])
            elif shutil.which('ptyxis'):
                subprocess.Popen(['ptyxis', '--', 'bash', '-c', f'cd {cwd} && {jar_command_str}'])
            else:
                print("tty not supported")
        else:
            print("os not supported")




if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    # Create and show the application's main window
    win = Window()
    win.show()
    # Run the application's main loop
    sys.exit(app.exec())