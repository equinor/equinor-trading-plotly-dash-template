sudo apt-get update && sudo apt-get install -y ca-certificates
curl -sSL https://install.python-poetry.org | python3 -
echo "$HOME/.poetry/bin" >> $GITHUB_PATH
poetry config virtualenvs.in-project true
poetry install
poetry run waitress-serve --port 5000 --call app:app