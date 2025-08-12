import os
import hashlib
import requests
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QObject, pyqtSignal
from tempfile import gettempdir

class ImageCache(QObject):
    image_loaded = pyqtSignal(str, QPixmap)  # Señal: clave, pixmap

    def __init__(self, cache_dir=None):
        super().__init__()
        self.memory_cache = {}
        self.cache_dir = cache_dir or os.path.join(gettempdir(), "pyqt_image_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def _key_to_path(self, key: str):
        """Convierte una clave (url o nombre) en una ruta segura para disco"""
        filename = hashlib.md5(key.encode()).hexdigest() + ".png"
        return os.path.join(self.cache_dir, filename)

    def get(self, key: str):
        # 1️⃣ Buscar en memoria
        if key in self.memory_cache:
            return self.memory_cache[key]

        # 2️⃣ Buscar en disco
        path = self._key_to_path(key)
        if os.path.exists(path):
            pixmap = QPixmap(path)
            self.memory_cache[key] = pixmap
            return pixmap

        return None

    def set_from_url(self, key: str, url: str):
        """Descarga y guarda imagen en caché"""
        path = self._key_to_path(key)
        if os.path.exists(path):
            pixmap = QPixmap(path)
        else:
            resp = requests.get(url, stream=True)
            if resp.status_code == 200:
                with open(path, "wb") as f:
                    f.write(resp.content)
                pixmap = QPixmap(path)
            else:
                pixmap = None

        if pixmap:
            self.memory_cache[key] = pixmap
            self.image_loaded.emit(key, pixmap)

    def clear(self):
        """Borra caché en memoria y disco"""
        self.memory_cache.clear()
        for f in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, f))
