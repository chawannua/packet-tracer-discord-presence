import os

def uninstall():
    startup = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    lnk = os.path.join(startup, "PacketTracerPresence.lnk")
    if os.path.exists(lnk):
        os.remove(lnk)
        print(f"Removed: {lnk}")
    else:
        print("Autostart shortcut was not found.")

if __name__ == "__main__":
    uninstall()
