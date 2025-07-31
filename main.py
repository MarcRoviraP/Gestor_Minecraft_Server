import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from mainwindow import Ui_MainWindow
import mc_server_utils
import os
import subprocess
import shutil


base_path = os.path.join(os.path.expanduser("~"), "MinecraftServers")
class Window(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Main Window")
        self.main_window = Ui_MainWindow()
        self.main_window.setupUi(self)
        #Abrir dialogo de crear servidor
        self.main_window.createServerBtn.clicked.connect(self.spawnDialog)
        
        # Recargar servidores al iniciar
        self.reloadServers()
        
        
        #Crear directorio base si no existe
        self.crearBasePath()

    def reloadServers(self):
        servidores = os.listdir(base_path + "/servers")
        for server in servidores:
            uriServer = f"{base_path}/servers/{server}"
            widget = QWidget()
            layout  = QHBoxLayout()
            img = QLabel()
            nombre = QLabel(server)
            ico = QIcon(f"{uriServer}/server-icon.png")
            button = QPushButton( "START")
            
            
            try:
                
                version = os.listdir(uriServer + '/versions')[0]
                nombreJar = f"{version}_server_vanilla.jar"
                rutaJar = os.path.join(base_path, "jars", nombreJar)
            

                button.clicked.connect(lambda _, s=server: self.startServer(s, 1024, 2048, rutaJar))

            except :
                button.setEnabled(False)
                button.setText("Recargar la APP")
                print(f"No se encontró el JAR para el servidor {server}.")
            img.setPixmap(ico.pixmap(64, 64))
        
            versionLabel = QLabel(f"Versión: {version}")
            layoutInfo = QVBoxLayout()
            layoutInfo.addWidget(nombre)
            layoutInfo.addWidget(versionLabel)
            
            layout.addWidget(img)
            layout.addLayout(layoutInfo)
            layout.addStretch()
            layout.addWidget(button)
            widget.setLayout(layout)
        
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())

            self.main_window.listServers.addItem(item)
            self.main_window.listServers.setItemWidget(item, widget)
        self.main_window.listServers.setCurrentRow(0)
        
    def crearBasePath(self):
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            os.makedirs(os.path.join(base_path, "jars"))
            os.makedirs(os.path.join(base_path, "servers"))
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
        minRamSpin.setValue(1024)

        maxRamLabel = QLabel("RAM máxima (MB):")
        maxRamSpin = QSpinBox()
        maxRamSpin.setRange(512, 64000)
        maxRamSpin.setValue(2048)

        # --- Botones ---
        createButton = QPushButton("Crear")
        cancelButton = QPushButton("Cancelar")

        # --- Layouts ---
        formLayout = QFormLayout()
        formLayout.addRow(nombreLabel, nombreEdit)
        formLayout.addRow(versionLabel, versionCombo)
        formLayout.addRow(tipoLabel, tipoCombo)
        formLayout.addRow(minRamLabel, minRamSpin)
        formLayout.addRow(maxRamLabel, maxRamSpin)

        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(createButton)
        buttonLayout.addWidget(cancelButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addLayout(buttonLayout)
        dlg.setLayout(mainLayout)

        # --- Conexiones ---
        createButton.clicked.connect(lambda: self.crearServidor(
            nombreEdit.text(),
            versionCombo.currentText(),
            tipoCombo.currentText(),
            minRamSpin.value(),
            maxRamSpin.value(),
            dlg
        ))
        cancelButton.clicked.connect(dlg.reject)

        
        dlg.exec()

    def aceptar_eula(self,base_path, nombre):

        server_path = os.path.join(base_path, "servers", nombre)
        eula_path = os.path.join(base_path, "servers", nombre, "eula.txt")
    
        os.makedirs(server_path, exist_ok=True)

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


    def crearServidor(self, nombre, version, tipo, ram_min, ram_max, dialog):
        if not nombre.strip():
            print("El nombre del servidor no puede estar vacío.")
            return
     

        nombreJar = f"{version}_server_vanilla.jar"

        if not os.path.exists(f"{base_path}/jars/{nombreJar}"):
            mc_server_utils.descargar_server_jar(
                mc_server_utils.obtener_jar_servidor(version),
                f"{base_path}/jars/{nombreJar}"
            )

        # Aquí aceptamos la EULA automáticamente
        self.aceptar_eula(base_path, nombre)

        shutil.copy("minecraft/ico/server-icon.png", f"{base_path}/servers/{nombre}/")
        # Lanzamos el servidor
        self.startServer(nombre, ram_min, ram_max, f"{base_path}/jars/{nombreJar}")

        print(f"Creando servidor '{nombre}' con versión {version}, tipo {tipo}, RAM {ram_min}-{ram_max}MB.")
        # Recargar la lista de servidores
        self.main_window.listServers.clear()
        self.reloadServers()
        dialog.accept()

    def startServer(self, nombre, ram_min, ram_max, rutaJar):
        subprocess.Popen(
            ["java", f"-Xms{ram_min}M", f"-Xmx{ram_max}M", "-jar", rutaJar, "nogui"],
            cwd=os.path.join(base_path, "servers", nombre),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )




if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    # Create and show the application's main window
    win = Window()
    win.show()
    # Run the application's main loop
    sys.exit(app.exec())