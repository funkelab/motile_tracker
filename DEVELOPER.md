# Developer Guide

## Managing dependencies with `uv`
This repo has been set up to use `uv` for developer dependency management.
Dev dependencies are specified in the `dependency-groups` section of the `pyproject.toml`.
The `dev` group is installed by default with `uv`, so running `uv run ...` should allow
you to use all the developer tools specified in this section.

Dependency groups are different from the extra dependencies specified in
`project.optional-dependencies`, so they cannot be installed with `pip install .[dev]`
and are not packaged and distributed with the library.
