"""Install the Sitara KiCad color theme where kicad-cli (and the GUI) look for it, on Windows, Linux and macOS."""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
THEME_SRC = os.path.join(REPO, "themes", "Sitara.json")
THEME_NAME = "Sitara"


def colors_dir(version="10.0"):
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA")
        return os.path.join(base, "kicad", version, "colors") if base else None
    if sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Preferences", "kicad", version, "colors")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "kicad", version, "colors")


def install_theme(version="10.0", src=THEME_SRC, name=THEME_NAME):
    """Copy the theme into KiCad's colors folder. Returns the theme name for `--theme`, or None if it could not be installed."""
    dest = colors_dir(version)
    if not dest or not os.path.exists(src):
        return None
    os.makedirs(dest, exist_ok=True)
    shutil.copy(src, os.path.join(dest, name.lower() + ".json"))
    return name
