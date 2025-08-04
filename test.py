import os
import re
import requests
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QListWidgetItem, QVBoxLayout
from functools import partial
import mc_server_utils
from iconDownloader import IconDownloader
from PyQt6.QtCore import QThreadPool
from PyQt6.QtGui import QPixmap, QIcon

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
        download_button.clicked.connect(partial(self.descargar_mod, mod['slug'], mod['latest_version']))

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
      self.thread_pool = getattr(self, 'thread_pool', QThreadPool())
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
              self.thread_pool.start(downloader)
          
  