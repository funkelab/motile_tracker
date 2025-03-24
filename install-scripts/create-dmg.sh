echo "Create MotileTracker.dmg"
create-dmg \
    --volname MotileTracker \
    --volicon logo.icns \
    --eula LICENSE \
    dist/MotileTracker.dmg \
    dist/MotileTracker.app
