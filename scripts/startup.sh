curl -sSL https://install.python-poetry.org | python3 -
echo "$HOME/.poetry/bin" >> $GITHUB_PATH
poetry config virtualenvs.in-project true
poetry install