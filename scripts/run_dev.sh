#!/bin/bash

export FLASK_ENV=development
export AUTH=skip
export KEYVAULT_URI=https://plotlyexample.vault.azure.net/

poetry run python app.py