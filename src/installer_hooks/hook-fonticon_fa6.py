from PyInstaller.utils.hooks import (collect_submodules,
                                     collect_data_files)

datas = collect_data_files('fonticon_fa6')

hiddenimports = collect_submodules('fonticon_fa6')

print("Loaded fonticon_fa6!", datas, hiddenimports)
