from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('superqt')

hiddenimports += collect_submodules('superqt.fonticon')

print("✅ Loaded superqt!", hiddenimports)
