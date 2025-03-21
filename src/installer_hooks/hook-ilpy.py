from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('ilpy.impl.solvers')

print("✅ Loaded ilpy!", datas, binaries, hiddenimports)
