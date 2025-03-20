#!/bin/bash

source "$PREFIX/etc/profile.d/conda.sh" 
conda activate "$PREFIX"
"$PREFIX/bin/pip" install motile_tracker

cat > "$PREFIX/motile-tracker.sh" <<EOF
$PREFIX/bin/python -m motile_tracker.launcher
EOF
