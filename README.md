# Equinor Trading Plotly Dash template repo

This repo contains a template for hosting a Flask server with a Plotly Dash dashboard component.
It contains configuration for authentication towards Azure AD and can be deployed automatically using Pulumi infrastructure as code.
The deploy code will scaffold everything needed to run a complete service in the cloud, requiring minimal knowledge of Azure.

## Getting started
Currently this project depends on some values that are generated when the service is deployed to Azure.
This might be improved in the future, but for the time being you actually have to setup the whole environment before running it locally.
To setup the infrastructure, complete the following steps.

1. Install [poetry](https://python-poetry.org/docs/)
1. Install [pulumi](https://www.pulumi.com/docs/get-started/install/)
1. Clone this repository or create a new repo based on the template
1. Run `poetry config virtualenvs.in-project true`
1. Run `poetry install` in both the top level folder AND in the `deploy` folder
2. Navigate to the `deploy` folder
4. (Optional) Rename the Pulumi project name in the Pulumi config files (probably have to do that for the config prefix too)
4. Generate a personal access token in Github. Select the `workflow` scope when generating the Github token
5. Set the access token, when requested for stack name write `dev`: 
    ```
    pulumi config set github:token XXXXXXXXXXXXXX --secret
    ```
5. (Optional) If your repo is placed in an organization, set the Github owner to the organization name:
    ```
    pulumi config set github:owner ORG_NAME
    ```
7.  Set a unique key vault name:
    ```
    pulumi config set key-vault-name PROJECT_NAME
    ```
4. (Optional) Set the project name config variables:
    ```
    pulumi config set project-name-prefix PROJECT_NAME
    ```
5. (Equinor only) Make sure that you have the Azure AD `Application Developer` role and the access to create new resources in your subscription
5. Run `pulumi up`
6. Done! The service should be hosted as an Azure Web App in Azure

Note that the authentication provider will block access to the service until an AD admin as given an admin grant to the application.

## Running locally

In the `/scripts/` folder, there is a `run_dev.sh` file with some environment variables that can be configured.
You need to update the key vault name to the new key vault you have created in Azure.
When the values are updated, you can run the service locally by running `./scripts/run_dev.sh`.

By default, authentication is deactivated locally, but you can activate it by removing the `AUTH` variable.
