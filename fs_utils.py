import os


def mkdir_if_not_exists(path):
    exists = os.path.exists(path)
    if not exists:
        print(f"Directory {path} not found!")
        os.makedirs(path)
        print("Directory created successful!")
    return exists