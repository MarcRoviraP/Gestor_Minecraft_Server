import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from mainwindow import Ui_MainWindow
import mc_server_utils
import os
import subprocess
base_path = os.path.join(os.path.expanduser("~"), "MinecraftServers")
class Window(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Main Window")
        self.main_window = Ui_MainWindow()
        self.main_window.setupUi(self)
        self.main_window.createServerBtn.clicked.connect(self.spawnDialog)
        
        self.crearBasePath()
        
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

        puertoLabel = QLabel("Puerto:")
        puertoSpin = QSpinBox()
        puertoSpin.setRange(1024, 65535)
        puertoSpin.setValue(25565)


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
        formLayout.addRow(puertoLabel, puertoSpin)

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
            puertoSpin.value(),
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


    def crearServidor(self, nombre, version, tipo, ram_min, ram_max, puerto, dialog):
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

        # Lanzamos el servidor
        subprocess.Popen(
            ["java", f"-Xms{ram_min}M", f"-Xmx{ram_max}M", "-jar", f"{base_path}/jars/{nombreJar}", "nogui"],
            cwd=os.path.join(base_path, "servers", nombre),
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )

        print(f"Creando servidor '{nombre}' con versión {version}, tipo {tipo}, RAM {ram_min}-{ram_max}MB, puerto {puerto}.")
        dialog.accept()




if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    # Create and show the application's main window
    win = Window()
    win.show()
    # Run the application's main loop
    sys.exit(app.exec())