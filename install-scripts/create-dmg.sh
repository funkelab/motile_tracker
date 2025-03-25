echo "Create MotileTracker.dmg"
create-dmg \
    --volname MotileTracker \
    --volicon logo.icns \
    --eula LICENSE \
    dist/MotileTrackerInstaller.dmg \
    dist/MotileTracker.app
