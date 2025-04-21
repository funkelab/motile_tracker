from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all('ilpy')

gdatas, gbinaries, ghiddenimports = collect_all('ilpy.solver_backend._gurobi')
sdatas, sbinaries, shiddenimports = collect_all('ilpy.solver_backend._scip')

datas += gdatas + sdatas
binaries += gbinaries + sbinaries
hiddenimports += ghiddenimports + shiddenimports

print("Loaded ilpy!", datas, binaries, hiddenimports)
