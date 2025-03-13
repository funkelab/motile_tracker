set PATH=%PATH%;C:\ProgramData\scoop\shims

"%PREFIX%\Scripts\pip.exe" install "git+https://github.com/funkelab/motile_tracker@installer"

echo "Create start script"

(
    echo cd "%PREFIX%"
    echo .\python -m motile_tracker.launcher
)> "%PREFIX%\motile_tracker.bat"
