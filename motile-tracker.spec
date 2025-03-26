# -*- mode: python ; coding: utf-8 -*-
import sys
import napari
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE


sys.setrecursionlimit(sys.getrecursionlimit() * 5)

sys.modules["FixTk"] = None

NAME = "MotileTracker"
WINDOWED = True if sys.platform == "darwin" else False
DEBUG = False
UPX = False
BLOCK_CIPHER = None


def get_icon():
    logo_file = "motile_logo.ico" if sys.platform.startswith("win") else "motile_logo.icns"
    return logo_file


def get_version():
    if sys.platform != "win32":
        return None

    from PyInstaller.utils.win32 import versioninfo as vi

    ver_str = napari.__version__
    version = ver_str.replace("+", ".").split(".")
    version = [int(x) for x in version if x.isnumeric()]
    version += [0] * (4 - len(version))
    version = tuple(version)[:4]
    return vi.VSVersionInfo(
        ffi=vi.FixedFileInfo(filevers=version, prodvers=version),
        kids=[
            vi.StringFileInfo(
                [
                    vi.StringTable(
                        "000004b0",
                        [
                            vi.StringStruct("CompanyName", NAME),
                            vi.StringStruct("FileDescription", NAME),
                            vi.StringStruct("FileVersion", ver_str),
                            vi.StringStruct("LegalCopyright", ""),
                            vi.StringStruct("OriginalFileName", NAME + ".exe"),
                            vi.StringStruct("ProductName", NAME),
                            vi.StringStruct("ProductVersion", ver_str),
                        ],
                    )
                ]
            ),
            vi.VarFileInfo([vi.VarStruct("Translation", [0, 1200])]),
        ],
    )


a = Analysis(
    ["src/motile_tracker/launcher.py"],
    hookspath=["src/installer_hooks"],
    hiddenimports=[
        "motile_tracker",
    ],
    runtime_hooks=[],
    excludes=[
        "FixTk",
        "tcl",
        "tk",
        "_tkinter",
        "tkinter",
        "Tkinter",
        "matplotlib",
    ],
    noarchive=False,
    optimize=0,
    cipher=BLOCK_CIPHER,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=BLOCK_CIPHER)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NAME,
    debug=DEBUG,
    bootloader_ignore_signals=False,
    strip=False,
    upx=UPX,
    console=(not WINDOWED),
    disable_windowed_traceback=False,
    icon=get_icon(),
    version=get_version(),
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    upx=UPX,
    upx_exclude=[],
    name=NAME,
)

if sys.platform == "darwin":
    import motile_tracker

    app = BUNDLE(
        coll,
        name=NAME + ".app",
        icon=get_icon(),
        bundle_identifier=f"com.{NAME}.{NAME}",
        info_plist={
            "CFBundleIdentifier": f"com.{NAME}.{NAME}",
            "CFBundleShortVersionString": motile_tracker.__version__,
            "NSHighResolutionCapable": "True",
        },
    )
