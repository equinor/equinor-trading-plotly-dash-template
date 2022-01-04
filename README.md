# Equinor Trading Plotly Dash template repo

This repo contains a template for hosting a Flask server with a Plotly Dash dashboard component.
It contains configuration for authentication towards Azure AD and can be deployed automatically using Pulumi infrastructure as code.
The deploy code will scaffold everything needed to run a complete service in the cloud.

## Getting started
Currently this project depends on some values that are generated when the service is deployed to Azure.
This might be improved in the future, but for the time being you actually have to setup the whole environment before running it locally.
To setup the infrastructure, complete the following steps.

1. Install [poetry](https://python-poetry.org/docs/)
1. Clone this repository
1. Run `poetry config virtualenvs.in-project true`
1. Run `poetry install` in both the top level folder and in the `deploy` folder
2. Navigate to the `deploy` folder
3. Set the Github token and owner values as described [here](https://www.pulumi.com/registry/packages/github/installation-configuration/)
4. (Optional) Rename the Pulumi project name
4. (Optional) Set the project name config variables:
    ```
    pulumi config set key-vault-name PROJECT_NAME
    pulumi config set project-name-prefix PROJECT_NAME
    ```
5. (Equinor only) Make sure that you have the Azure AD `Application Developer` role and the access to create new resources in your subscription
5. Run `pulumi up`
6. Done! The service should be hosted as an Azure Web App in Azure

## Running locally

In the `/scripts/` folder, there is a `run_dev.sh` file with some environment variables that can be configured.
You need to update the key vault name to the new key vault you have created in Azure.
When the values are updated, you can run the service locally by running `./scripts/run_dev.sh`.

By default, authentication is deactivated locally, but you can activate it by remove the `AUTH` variable.
