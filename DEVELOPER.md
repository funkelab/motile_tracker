# Developer Guide

## Managing dependencies with `uv`
This repo has been set up to use `uv` for developer dependency management.
Install `uv` according to [their instructions](https://docs.astral.sh/uv/getting-started/installation/).

Dev dependencies are specified in the `dependency-groups` section of the `pyproject.toml`.
The `dev` group is installed by default with `uv`, so running `uv run ...` should allow
you to use all the developer tools specified in this section.

Dependency groups are different from the extra dependencies specified in
`project.optional-dependencies`, so they cannot be installed with `pip install .[dev]`
and are not packaged and distributed with the library.

## Running tasks with `just`
For convenience, common development tasks like building docs or running test with coverage
can be run with `just`. Install `just` according to [their instructions](https://just.systems/man/en/packages.html).

Tasks are defined in the `justfile`. These tasks are just shorthand for common commands that
you would otherwise type into your shell over and over.
