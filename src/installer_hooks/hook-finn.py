from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('finn')

print("Loaded finn!", datas, binaries, hiddenimports)
