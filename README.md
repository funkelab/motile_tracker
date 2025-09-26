# Motile Tracker

[![tests](https://github.com/funkelab/motile_tracker/workflows/tests/badge.svg)](https://github.com/funkelab/motile_tracker/actions)
[![codecov](https://codecov.io/gh/funkelab/motile_tracker/branch/main/graph/badge.svg)](https://codecov.io/gh/funkelab/motile_tracker)

The full documentation of the plugin can be found [here](https://funkelab.github.io/motile_tracker/).

An application for interactive tracking with [motile](https://github.com/funkelab/motile)
Motile is a library that makes it easy to solve tracking problems using optimization
by framing the task as an Integer Linear Program (ILP).
See the motile [documentation](https://funkelab.github.io/motile)
for more details on the concepts and method.

----------------------------------

## Installation

Users can download and install an executable application from the github release, or
install from `pypi` in the environment of their choice (e.g. `venv`, `conda`) with the command
`pip install motile-tracker`.
Currently, the motile_tracker requires python >=3.10.

Developers can clone the GitHub repository and then  use `uv` to install and run the code.
See the developer guide in `DEVELOPER.md` for more information.

## Running Motile Tracker

Start the executable application, or run `motile_tracker` from the command line.

## Package the application into an executable and create the installer

Tagging any branch will automatically trigger the deploy.yml workflow,
which pushes the tagged version to PyPi and creates a github release; draft release if the tag contains "-dev", pre-release if the tag contains "-rc' or a full release otherwise. In case of a draft or pre release, when the user updates the release notes and promotes it to a published release, github will trigger `make_bundle_app.yml` workflow which will create the Linux, Mac and Windows installer and will upload them as release artifacts to github.

## Issues

If you encounter any problems, please
[file an issue](https://github.com/funkelab/motile_tracker/issues)
along with a detailed description.
