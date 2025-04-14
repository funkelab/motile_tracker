from PyInstaller.utils.hooks import (collect_all, collect_submodules,
                                     collect_data_files)

datas, binaries, hiddenimports = collect_all('finn')

hiddenimports += collect_submodules("finn_builtins")
hiddenimports += collect_submodules("napari_svg")

datas += collect_data_files('finn_builtins')
datas += collect_data_files('napari_svg')

print("Loaded finn!", datas, binaries, hiddenimports)
