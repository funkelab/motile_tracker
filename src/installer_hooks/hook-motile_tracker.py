from PyInstaller.utils.hooks import collect_all

print("✅ Hook for motile_tracker is being loaded!")

datas, binaries, hiddenimports = collect_all('motile_tracker')

# datas = collect_data_files('motile_tracker')

# hiddenimports = collect_submodules('motile_tracker')

hiddenimports += [
    'motile_tracker.launcher',
    'motile_tracker.application_menus.main_app',
    'motile_tracker.application_menus.menu_widget',
    'motile_tracker.data_views.views.tree_view.tree_widget',
    'motile_tracker.motile.backend.solve',
    'motile_tracker.example_data',
]
