import os
import shutil

def clean_screenshot_folders(base_path='.'):
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path) and item.startswith('screenshot'):
            print(f"Removing folder: {item_path}")
            shutil.rmtree(item_path)

if __name__ == "__main__":
    clean_screenshot_folders()