from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('motile_tracker')

# datas += collect_data_files('motile_tracker.data_views.views_coordinator')
# hiddenimports += collect_submodules('motile_tracker.data_views.views_coordinator')

# datas += collect_data_files('fonticon_fa6')
# hiddenimports += collect_submodules('fonticon_fa6')

# datas += collect_data_files('superqt.fonticon')
# hiddenimports += collect_submodules('superqt.fonticon')

# datas += collect_data_files('superqt.fonticon._plugins')
# hiddenimports += collect_submodules('superqt.fonticon._plugins')

print("✅ Loaded motile_tracker!")
