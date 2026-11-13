"""Points app-owned file types (text, images, media, zip, ini) at HUD icons, per user.

  py file_icons.py set <folder>   use <folder>\\<kind>.ico (built by make_folder_icons.py)
  py file_icons.py restore        put the original icons back

The first "set" saves the original DefaultIcon values in backup\\fileicons-original.json.
App updates can reset these icons; the next theme switch sets them again.
"""
import ctypes
import json
import sys
import winreg
from pathlib import Path

ROOT = Path(__file__).parent
BACKUP = ROOT / "backup" / "fileicons-original.json"
EXTS = {".txt": "text", ".log": "text", ".ini": "config", ".png": "image", ".jpg": "image",
        ".mp3": "media", ".mp4": "media", ".zip": "zip"}


def progid(ext):
    n = ctypes.c_uint(512)
    buf = ctypes.create_unicode_buffer(512)
    ok = ctypes.windll.shlwapi.AssocQueryStringW(0, 20, ext, None, buf, ctypes.byref(n)) == 0  # ASSOCSTR_PROGID
    return buf.value if ok else None


def key(pid):
    return rf"Software\Classes\{pid}\DefaultIcon"


def read(pid):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key(pid)) as k:
            return winreg.QueryValueEx(k, "")[0]
    except OSError:
        return None


def main():
    saved = json.loads(BACKUP.read_text()) if BACKUP.exists() else {}
    if sys.argv[1] == "set":
        folder = Path(sys.argv[2])
        for ext, kind in EXTS.items():
            pid = progid(ext)
            if not pid or not (folder / f"{kind}.ico").exists():
                continue
            if pid not in saved:
                saved[pid] = read(pid)  # None = no per-user value before
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key(pid)) as k:
                winreg.SetValueEx(k, "", 0, winreg.REG_SZ, str(folder / f"{kind}.ico"))
        BACKUP.parent.mkdir(exist_ok=True)
        BACKUP.write_text(json.dumps(saved, indent=1))
    else:
        for pid, value in saved.items():
            if value is None:
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key(pid))
                except OSError:
                    pass
            else:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key(pid)) as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_EXPAND_SZ if "%" in value else winreg.REG_SZ, value)
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)  # SHCNE_ASSOCCHANGED


if __name__ == "__main__":
    main()
