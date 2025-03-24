# Motile Tracker

[![tests](https://github.com/funkelab/motile_tracker/workflows/tests/badge.svg)](https://github.com/funkelab/motile_tracker/actions)
[![codecov](https://codecov.io/gh/funkelab/motile_tracker/branch/main/graph/badge.svg)](https://codecov.io/gh/funkelab/motile_tracker)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/motile_tracker)](https://napari-hub.org/plugins/motile_tracker)

The full documentation of the plugin can be found [here](https://funkelab.github.io/motile_tracker/).

A plugin for tracking with [motile](https://github.com/funkelab/motile) in napari.
Motile is a library that makes it easy to solve tracking problems using optimization
by framing the task as an Integer Linear Program (ILP).
See the motile [documentation](https://funkelab.github.io/motile)
for more details on the concepts and method.

----------------------------------

## Installation

This plugin depends on [motile](https://github.com/funkelab/motile), which in
turn depends on gurobi and ilpy. These dependencies must be installed with
conda before installing the plugin with pip.

    conda create -n motile-tracker python=3.10
    conda activate motile-tracker
    conda install -c conda-forge -c funkelab -c gurobi ilpy
    pip install motile-tracker

The conda environment can also be created from the provided conda_config.yml:

    conda env create -f conda_config.yml
    conda activate motile-tracker

Alternatively one can use [pixi](https://pixi.sh/).

## Running Motile Tracker

To run the application:
* activate the conda environment created in the [Installation Step](#installation)

    conda activate motile-tracker

* Run:

    python -m motile_tracker.launcher

If [pixi](https://pixi.sh/) is available, you can run motile-tracker using:

    pixi run start

## Package the application into an executable and create the installer

To create the executab run

    pixi run create-app

This command will create an application (.app) on OSX, an EXE on Windows and an
ELF executable on Linux.

On Windows in order to be able to package the application the ilpy library must be
properly installed and compiled. This will require [download](https://aka.ms/vs/17/release/vs_BuildTools.exe) and install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/). This comes with a script to set all required environment variables located typically at `"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"` so before you setup the app you need to run this bat file. For powershell run `scripts\scripts/set-vs-buildTools-env.ps1 <fullpathto vcvars64>`.

Further to create an installer for the app you will need:
* InnoSetup on Windows (`scoop install inno-setup` or `winget install "Inno Setup"`)
* create-dmg on OSX (`brew install create-dmg`)
* makeself on Linux (`apt install makeself`)

## Issues

If you encounter any problems, please
[file an issue](https://github.com/funkelab/motile_tracker/issues)
along with a detailed description.
