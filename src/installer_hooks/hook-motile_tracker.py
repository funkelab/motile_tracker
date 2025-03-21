from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('motile_tracker')

print("✅ Loaded motile_tracker!", datas, binaries, hiddenimports)
