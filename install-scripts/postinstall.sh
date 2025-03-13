#!/bin/bash

source "$PREFIX/etc/profile.d/conda.sh" 
conda activate "$PREFIX"
"$PREFIX/bin/pip" install git+https://github.com/funkelab/motile_tracker@installer

cat > "$PREFIX/motile-tracker.sh" <<EOF
$PREFIX/bin/python -m motile_tracker.launcher
EOF
