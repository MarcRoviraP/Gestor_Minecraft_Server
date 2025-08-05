from PyQt6.QtCore import QRunnable
import requests

class IconDownloader(QRunnable):
    def __init__(self, url, callback, widget):
        super().__init__()
        self.url = url
        self.callback = callback
        self.widget = widget

    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            img_data = response.content if response.ok else None
        except Exception as e:
            print(f"[IconDownloader] Error downloading icon: {e}")
            img_data = None

        # Verifica si el widget sigue existiendo y está visible
        if self.widget is not None:
            self.callback(self.url, img_data, self.widget)
        else:
            print("[IconDownloader] Widget destruido, no se llama al callback.")
