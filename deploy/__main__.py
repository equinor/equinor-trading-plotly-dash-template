# %%
"""An Azure RM Python Pulumi program"""

import uuid
from typing import List

import pulumi
import pulumi_azuread as ad
from pulumi_azure_native import (
    authorization,
    insights,
    keyvault,
    resources,
    storage,
    web,
)

config = pulumi.Config()
client_config = authorization.get_client_config()

app_registration = ad.Application(
    "appregistration", display_name="NGTT-test-app", owners=[client_config.object_id]
)

app_client_secret = ad.ApplicationPassword(
    "appclientsecret",
    application_object_id=app_registration.object_id,
    display_name="Client secret",
    end_date_relative="8700h",
)

# CUSTOM_IMAGE = "cicddeployment"

# Create an Azure Resource Group
resource_group = resources.ResourceGroup("plotly-dash-example")


# Create an Azure resource (Storage Account)
account = storage.StorageAccount(
    "sa",
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(
        name=storage.SkuName.STANDARD_LRS,
    ),
    kind=storage.Kind.STORAGE_V2,
)

container = storage.BlobContainer(
    "test",
    resource_group_name=resource_group.name,
    account_name=account.name,
)

blob = storage.Blob(
    "iris.csv",
    resource_group_name=resource_group.name,
    account_name=account.name,
    container_name=container.name,
    source=pulumi.FileAsset("../test/iris.csv"),
    content_type="text",
)


plan = web.AppServicePlan(
    "plan",
    resource_group_name=resource_group.name,
    kind="Linux",
    reserved=True,
    sku=web.SkuDescriptionArgs(
        name="B1",
        tier="Basic",
    ),
)

# registry = containerregistry.Registry(
#     "registry",
#     resource_group_name=resource_group.name,
#     sku=containerregistry.SkuArgs(
#         name="Basic",
#     ),
#     admin_user_enabled=True)

# credentials = containerregistry.list_registry_credentials_output(resource_group_name=resource_group.name,
#                                                                  registry_name=registry.name)
# admin_username = credentials.username
# admin_password = credentials.passwords[0]["value"]

# my_image = docker.Image(
#     CUSTOM_IMAGE,
#     image_name=registry.login_server.apply(
#         lambda login_server: f"{login_server}/{CUSTOM_IMAGE}:v1.0.0"),
#     build=docker.DockerBuild(context=f"./{CUSTOM_IMAGE}"),
#     registry=docker.ImageRegistry(
#         server=registry.login_server,
#         username=admin_username,
#         password=admin_password
#     )
# )

# web_app = web.WebApp(
#     "webapp",
#     resource_group_name=resource_group.name,
#     server_farm_id=plan.id,
#     site_config=web.SiteConfigArgs(
#         app_settings=[
#             web.NameValuePairArgs(name="WEBSITES_ENABLE_APP_SERVICE_STORAGE", value="false"),
#             web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_URL",
#                                   value=registry.login_server.apply(
#                                       lambda login_server: f"https://{login_server}")),
#             web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_USERNAME",
#                                   value=admin_username),
#             web.NameValuePairArgs(name="DOCKER_REGISTRY_SERVER_PASSWORD",
#                                   value=admin_password),
#             web.NameValuePairArgs(name="WEBSITES_PORT", value="80"),
#         ],
#         always_on=True,
#         linux_fx_version=my_image.image_name.apply(lambda image_name: f"DOCKER|{image_name}"),
#     ),
#     https_only=True,
#     identity=web.ManagedServiceIdentityArgs(
#         type=web.ManagedServiceIdentityType.SYSTEM_ASSIGNED
#     )
# )

app_insights = insights.Component(
    "appservice-ai",
    application_type=insights.ApplicationType.WEB,
    kind="web",
    resource_group_name=resource_group.name,
)

app = web.WebApp(
    "webapp",
    resource_group_name=resource_group.name,
    server_farm_id=plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(
                name="APPINSIGHTS_INSTRUMENTATIONKEY",
                value=app_insights.instrumentation_key,
            ),
            web.NameValuePairArgs(
                name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                value=app_insights.instrumentation_key.apply(
                    lambda key: "InstrumentationKey=" + key
                ),
            ),
            web.NameValuePairArgs(
                name="ApplicationInsightsAgent_EXTENSION_VERSION", value="~2"
            ),
        ]
    ),
    identity=web.ManagedServiceIdentityArgs(
        type=web.ManagedServiceIdentityType.SYSTEM_ASSIGNED
    ),
)

# %%

access_policies = []
access_policies.append(
    keyvault.AccessPolicyEntryArgs(
        object_id=app.identity.principal_id,
        permissions=keyvault.PermissionsArgs(secrets=["get", "list"]),
        tenant_id=client_config.tenant_id,
    )
)
access_policies.append(
    keyvault.AccessPolicyEntryArgs(
        object_id=client_config.object_id,
        permissions=keyvault.PermissionsArgs(secrets=["get", "list", "delete"]),
        tenant_id=client_config.tenant_id,
    )
)

vault = keyvault.Vault(
    "vault",
    properties=keyvault.VaultPropertiesArgs(
        access_policies=access_policies,
        enabled_for_deployment=True,
        enabled_for_disk_encryption=True,
        enabled_for_template_deployment=True,
        sku=keyvault.SkuArgs(
            family="A",
            name=keyvault.SkuName.STANDARD,
        ),
        tenant_id=client_config.tenant_id,
    ),
    resource_group_name=resource_group.name,
    vault_name="vault" + str(uuid.uuid4())[:8],
)


secret = keyvault.Secret(
    "client-secret",
    properties=keyvault.SecretPropertiesArgs(
        value=app_client_secret.value,
    ),
    resource_group_name=resource_group.name,
    secret_name="client-secret",
    vault_name=vault.name,
)


# Give users/applications Storage Blob Data Reader role to the storage account
role_assignment = authorization.RoleAssignment(
    "roleAssignmentOwner",
    principal_id=client_config.object_id,
    principal_type=authorization.PrincipalType.USER,
    role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",
    scope=pulumi.Output.concat(
        "/subscriptions/",
        client_config.subscription_id,
        "/resourceGroups/",
        resource_group.name,
        "/providers/Microsoft.Storage/storageAccounts/",
        account.name,
    ),
)
role_assignment = authorization.RoleAssignment(
    "roleAssignmentApp",
    principal_id=app.identity.principal_id,
    principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
    role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",
    scope=pulumi.Output.concat(
        "/subscriptions/",
        client_config.subscription_id,
        "/resourceGroups/",
        resource_group.name,
        "/providers/Microsoft.Storage/storageAccounts/",
        account.name,
    ),
)


def create_config_file(args: List[pulumi.Output]) -> None:
    client_id, tenant_id, vault_name, secret_name, account_name = args
    config_file = f"""from typing import List

CLIENT_ID = "{client_id}"  # Application (client) ID of app registration
AUTHORITY = "https://login.microsoftonline.com/{tenant_id}"
REDIRECT_PATH = "/getAToken"  # Used for forming an absolute URL to your redirect URI.
# The absolute URL must match the redirect URI you set
# in the app's registration in the Azure portal.
ENDPOINT = (
    "https://graph.microsoft.com/v1.0/me"  # This resource requires no admin consent
)
SCOPES = ["User.ReadBasic.All"]
SESSION_TYPE = (
    "filesystem"  # Specifies the token cache should be stored in server-side session
)
KEYVAULT_URI = "https://{vault_name}.vault.azure.net/"
SECRET_NAME = "{secret_name}"
ROLES: List[str] = []
CHECK_PROD = "IS_PROD"


# Data files
data_files = {{
    "iris": {{
        "account_url": "https://{account_name}.blob.core.windows.net",
        "container": "test",
        "filename": "iris.csv",
    }}
}}
"""
    with open("../config.py", "w") as file:
        file.write(config_file)


pulumi.Output.all(
    client_config.client_id,
    client_config.tenant_id,
    vault.name,
    secret.name,
    account.name,
).apply(create_config_file)
