# Equinor Trading template repo

This is a template containing all the essentials you need when creating a new repo for a project. The main components are the following:

- `docs` - This is folder contains the setup needed to build the docstring documentation.
- `src` - Main folder for code modules.
- `test` - Folder containing tests.
- `.github/workflows/lint-and-format.yml` - Github Actions workflow for lint checking and automated testing.
- `pre-commit-config.yaml` - Pre-commit configuration for automatically running lint checking and automated testing before committing.
- `pyproject.toml`, `poetry.lock` - Project and package definition.
- `setup.cfg` - Configuration of linting tools.


## Getting started

1. Install [poetry](https://python-poetry.org/docs/)
1. Clone repository
1. Run `poetry config virtualenvs.in-project true` followed by `poetry install` from the project root folder. A .venv folder should now be created and placed in the root of the project. 
1. Run `poetry shell` to create a new poetry shell, followed `jupyter notebook` to open [jupyter notebook](https://jupyter.org/) in this environment. 
1. Install pre-commit hook by running `poetry run pre-commit install`

## How to build the docs
Build `.rst` files

```
poetry run sphinx-apidoc -o docs/source src
```

Build HTML files from `.rst` files

```
poetry run sphinx-build -b html docs/source docs/build
```

The docs can now be accessed under docs/build. 

## Run tests

`poetry run python -m pytest`
