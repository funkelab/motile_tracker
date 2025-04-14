from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('freetype')

print("Loaded freetype!", datas, binaries, hiddenimports)
