from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = collect_data_files('napari')
datas += collect_data_files('napari_builtins')
datas += collect_data_files('napari_svg')

hiddenimports = collect_submodules("napari") 
hiddenimports = collect_submodules("napari_svg") 

hiddenimports += [
    'napari.viewer',
    'napari.plugins',
    'napari._event_loop',
    'napari.__main__',
    'napari._qt',
    'napari._qt.qt_main_window',
    'napari_builtins',
    'napari_plugin_manager',
]
