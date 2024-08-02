import os
import sys
from pathlib import Path
from shutil import copyfile

from modules._platform import get_cwd, get_launcher_name, get_platform, is_frozen
from modules.settings import get_library_folder


def create_shortcut(folder, name):
    platform = get_platform()
    library_folder = Path(get_library_folder())

    if platform == "Windows":
        import win32com.client
        from win32comext.shell import shell, shellcon

        targetpath = library_folder / folder / "blender.exe"
        workingdir = library_folder / folder
        desktop = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
        dist = Path(desktop) / (name + ".lnk")

        if getattr(sys, "frozen", False):
            icon = sys._MEIPASS + "/files/winblender.ico"  # noqa: SLF001
        else:
            icon = Path("./resources/icons/winblender.ico").resolve().as_posix()

        icon_location = library_folder / folder / "winblender.ico"
        copyfile(icon, icon_location.as_posix())

        _WSHELL = win32com.client.Dispatch("Wscript.Shell")
        wscript = _WSHELL.CreateShortCut(dist.as_posix())
        wscript.Targetpath = targetpath.as_posix()
        wscript.WorkingDirectory = workingdir.as_posix()
        wscript.WindowStyle = 0
        wscript.IconLocation = icon_location.as_posix()
        wscript.save()
    elif platform == "Linux":
        _exec = library_folder / folder / "blender"
        icon = library_folder / folder / "blender.svg"
        desktop = Path.home() / "Desktop"
        filename = name.replace(" ", "-")
        dist = desktop / (filename + ".desktop")

        kws = (
            "3d;cg;modeling;animation;painting;"
            "sculpting;texturing;video editing;"
            "video tracking;rendering;render engine;"
            "cycles;game engine;python;"
        )

        desktop_entry = "\n".join(
            [
                "[Desktop Entry]",
                f"Name={name}",
                "Comment=3D modeling, animation, rendering and post-production",
                f"Keywords={kws}",
                "Icon={}".format(icon.as_posix().replace(" ", r"\ ")),
                "Terminal=false",
                "Type=Application",
                "Categories=Graphics;3DGraphics;",
                "MimeType=application/x-blender;",
                "Exec={} %f".format(_exec.as_posix().replace(" ", r"\ ")),
            ]
        )
        with open(dist, "w", encoding="utf-8") as file:
            file.write(desktop_entry)

        os.chmod(dist, 0o744)


def get_shortcut_type() -> str:
    """ONLY FOR VISUAL REPRESENTATION"""
    return {
        "Windows": "Shortcut",
        "Linux": "Desktop file",
    }.get(get_platform(), "Shortcut")


def get_default_shortcut_destination():
    return {
        "Windows": Path(
            Path.home(), "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "BlenderLauncher.lnk"
        ),
        "Linux": Path(Path.home(), ".local", "share", "applications", "BLV2.desktop"),
    }.get(get_platform(), Path(Path.home(), ".local", "share", "applications", "BLV2.desktop"))


def register_windows_filetypes():
    import winreg

    assert is_frozen()
    # Register the program in the classes
    with winreg.CreateKey(
        winreg.HKEY_CLASSES_ROOT,
        r"blenderlauncherv2.blend\shell\open\command",
    ) as command_key:
        pth = f'"{Path(sys.executable)}"'
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'{pth} __launch_target "%1"')

    # add it to the OpenWithProgids list
    with winreg.CreateKey(
        winreg.HKEY_CLASSES_ROOT,
        r".blend\OpenWithProgids",
    ) as progids_key:
        winreg.SetValueEx(progids_key, "blenderlauncherv2.blend", 0, winreg.REG_SZ, "")


def unregister_windows_filetypes():
    import winreg

    assert is_frozen()
    # Unregister the program as a user-level application
    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"blenderlauncherv2.blend\shell\open\command")
    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"blenderlauncherv2.blend\shell\open")
    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"blenderlauncherv2.blend\shell")
    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r"blenderlauncherv2.blend")

    # vvv This doesn't seem to work. But I don't know what the correct command is supposed to be vvv
    winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, r".blend\OpenWithProgids\blenderlauncherv2.blend")


def generate_program_shortcut(destination: Path):
    """Generates a shortcut for this program. Also sets up filetype associations in Linux."""
    platform = get_platform()

    if sys.platform == "win32":
        import win32com.client

        # create the shortcut
        _WSHELL = win32com.client.Dispatch("Wscript.Shell")
        wscript = _WSHELL.CreateShortcut(str(destination))
        wscript.Targetpath = f'{destination.as_posix()} __launch_target "%1"'
        wscript.WorkingDirectory = get_cwd().as_posix()
        wscript.WindowStyle = 0
        wscript.save()

    elif platform == "Linux":
        import shlex

        bl_exe, _ = get_launcher_name()
        cwd = get_cwd()
        source = cwd / bl_exe

        _exec = source
        text = "\n".join(
            [
                "[Desktop Entry]",
                "Name=Blender Launcher V2",
                "GenericName=Launcher",
                f"Exec={shlex.quote(str(_exec))} __launch_target",
                "MimeType=application/x-blender;",
                "Icon=blender-icon",
                "Terminal=false",
                "Type=Application",
            ]
        )

        with destination.open("w", encoding="utf-8") as file:
            file.write(text)

        os.chmod(destination, 0o744)


# generate_program_shortcut(Path("~/.local/share/applications/BLV2.desktop").expanduser())
