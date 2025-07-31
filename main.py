import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from mainwindow import Ui_MainWindow
import mc_server_utils

class Window(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Main Window")
        self.main_window = Ui_MainWindow()
        self.main_window.setupUi(self)
        self.main_window.createServerBtn.clicked.connect(self.spawnDialog)

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

        eulaCheck = QCheckBox("Aceptar EULA")

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
        formLayout.addRow(eulaCheck)

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
            eulaCheck.isChecked(),
            dlg
        ))
        cancelButton.clicked.connect(dlg.reject)

        dlg.exec()

    def crearServidor(self, nombre, version, tipo, ram_min, ram_max, puerto, eula_aceptado, dialog):
        if not nombre.strip():
            print("El nombre del servidor no puede estar vacío.")
            return
        if not eula_aceptado:
            print("Debes aceptar el EULA para continuar.")
            return

        mc_server_utils.descargar_server_jar(
            mc_server_utils.obtener_jar_servidor(version),
            f"{version}_server_vanilla.jar"
        )
        
        # Aquí va tu lógica de creación de servidor
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