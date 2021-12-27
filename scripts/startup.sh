apt-get update && apt-get install -y ca-certificates
curl --insecure -sSL https://install.python-poetry.org | python3 -
echo "$HOME/.poetry/bin" >> $GITHUB_PATH
poetry config virtualenvs.in-project true
poetry install
poetry run gunicorn --bind=0.0.0.0 --timeout 600 "app:app()"