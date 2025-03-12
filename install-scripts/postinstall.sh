#!/bin/bash

source "$PREFIX/etc/profile.d/conda.sh" 
conda activate "$PREFIX"
"$PREFIX/bin/pip" install git+https://github.com/funkelab/motile_tracker@installer
