#!/bin/bash

export FLASK_APP=app:app
export FLASK_ENV=development

poetry run flask run