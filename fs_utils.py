import os
import sys


def mkdir_if_not_exists(path):
    exists = os.path.exists(path)
    if not exists:
        print(f"Directory {path} not found!")
        os.makedirs(path)
        print("Directory created successful!")
    return exists
def resource_path(relative_path):
    """Obtiene la ruta correcta en desarrollo y en el ejecutable."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)