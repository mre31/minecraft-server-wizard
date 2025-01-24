import os
import sys
from frontend.wizard_gui import ServerWizard
import tkinter as tk

def get_base_dir():
    """Uygulama ana dizinini belirler"""
    if getattr(sys, 'frozen', False):
        # Exe olarak çalışıyorsa
        return os.path.dirname(sys.executable)
    # Python script olarak çalışıyorsa
    return os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    base_dir = get_base_dir()
    app = ServerWizard(base_dir)
    
    # İkon dosyasının yolunu belirle
    icon_path = os.path.join(base_dir, "icon.ico")
    if os.path.exists(icon_path):
        app.root.iconbitmap(icon_path)
        # Taskbar ikonunu da ayarla
        app.root.wm_iconbitmap(icon_path)
    
    app.run() 