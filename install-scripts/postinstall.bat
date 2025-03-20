"%PREFIX%\Scripts\pip.exe" install motile_tracker

echo "Create start script"

(
    echo cd "%PREFIX%"
    echo .\python -m motile_tracker.launcher
)> "%PREFIX%\motile_tracker.bat"
