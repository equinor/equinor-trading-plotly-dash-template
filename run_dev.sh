#!/bin/bash

export FLASK_APP=app.py
export FLASK_ENV=development

poetry run flask run