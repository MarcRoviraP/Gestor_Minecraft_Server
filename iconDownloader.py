# --- 2. IconDownloader que trabaja solo con bytes ---
import requests, weakref, os
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool


class IconDownloader(QRunnable):
    def __init__(self, url, cache, widget, signal_obj):
        super().__init__()
        self.url = url
        self.cache = cache
        self.widget_ref = weakref.ref(widget)
        self.signal_obj = signal_obj

    def run(self):
        path = self.cache._key_to_path(self.url)
        if os.path.exists(path):
            with open(path, "rb") as f:
                img_data = f.read()
            self._emit(img_data)
            return

        try:
            r = requests.get(self.url, timeout=10)
            if r.ok:
                img_data = r.content
                with open(path, "wb") as f:
                    f.write(img_data)
                self._emit(img_data)
            else:
                self._emit(None)
        except Exception as e:
            print(f"[IconDownloader] Error: {e}")
            self._emit(None)

    def _emit(self, img_data):
        widget = self.widget_ref()
        if widget:
            self.signal_obj.finished.emit(self.url, img_data, widget)
class IconResult(QObject):
    finished = pyqtSignal(str, bytes, object)  # url, img_data, widget