# %%
"""An Azure RM Python Pulumi program"""

import pulumi
from pulumi_azure_native import resources, storage, authorization, web, containerregistry, keyvault, insights
import pulumi_docker as docker
from azure.identity import AzureCliCredential
from msgraph.core import GraphClient
from typing import cast, List

config = pulumi.Config()

graph = GraphClient(credential=AzureCliCredential(), scopes=["https://graph.microsoft.com/.default"])

CUSTOM_IMAGE = "cicddeployment"

# Create an Azure Resource Group
resource_group = resources.ResourceGroup('resource_group')


# Create an Azure resource (Storage Account)
account = storage.StorageAccount('sa',
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(
        name=storage.SkuName.STANDARD_LRS,
    ),
    kind=storage.Kind.STORAGE_V2)

pulumi.export("Storage account name", account.name)

container = storage.BlobContainer("test",
    resource_group_name=resource_group.name,
    account_name=account.name,
)

blob = storage.Blob("iris.csv",
    resource_group_name=resource_group.name,
    account_name=account.name,
    container_name=container.name,
    source=pulumi.FileAsset("test/iris.csv"),
    content_type="text"
)

# Export the primary key of the Storage Account
primary_key = pulumi.Output.all(resource_group.name, account.name) \
    .apply(lambda args: storage.list_storage_account_keys(
        resource_group_name=args[0],
        account_name=args[1]
    )).apply(lambda accountKeys: accountKeys.keys[0].value)
pulumi.export("primary_storage_key", primary_key)


plan = web.AppServicePlan(
    "plan",
    resource_group_name=resource_group.name,
    kind="Linux",
    reserved=True,
    sku=web.SkuDescriptionArgs(
        name="B1",
        tier="Basic",
    )
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
    resource_group_name=resource_group.name
)

app = web.WebApp(
    "webapp",
    resource_group_name=resource_group.name,
    server_farm_id=plan.id,
    site_config=web.SiteConfigArgs(
        app_settings=[
            web.NameValuePairArgs(name="APPINSIGHTS_INSTRUMENTATIONKEY", value=app_insights.instrumentation_key),
            web.NameValuePairArgs(name="APPLICATIONINSIGHTS_CONNECTION_STRING",
                                  value=app_insights.instrumentation_key.apply(
                                      lambda key: "InstrumentationKey=" + key
                                  )),
            web.NameValuePairArgs(name="ApplicationInsightsAgent_EXTENSION_VERSION", value="~2")
        ]
    ),
    identity=web.ManagedServiceIdentityArgs(
        type=web.ManagedServiceIdentityType.SYSTEM_ASSIGNED
    )
)

# Get object IDs for all users that need specific accesses
owners = cast(List[str], config.get_object("storage-user-access"))
object_ids = []
for owner in owners:
    object_ids.append(graph.get(f"/users/{owner}@equinor.com").json()["id"])

object_ids.append(web_app.id)

access_policies = []
for object_id in object_ids:
    access_policies.append(keyvault.AccessPolicyEntryArgs(
        object_id=object_id,
        permissions=keyvault.PermissionsArgs(
            secrets=[
                "get",
                "list",
            ],
        ),
        tenant_id=config.get("tenant-id"),
    ))

vault = keyvault.Vault("vault",
    properties=keyvault.VaultPropertiesArgs(
        access_policies=access_policies,
        enabled_for_deployment=True,
        enabled_for_disk_encryption=True,
        enabled_for_template_deployment=True,
        sku=keyvault.SkuArgs(
            family="A",
            name=keyvault.SkuName.STANDARD,
        ),
        tenant_id=config.get("tenant-id"),
    ),
    resource_group_name=resource_group.name,
    vault_name="vault"
)

secret = keyvault.Secret("client-secret",
    properties=keyvault.SecretPropertiesArgs(
        value="secret-value",
    ),
    resource_group_name=resource_group.name,
    secret_name="client-secret",
    vault_name=vault.name
)

# Give users/applications Storage Blob Data Reader role to the storage account
if object_ids:
    for object_id in object_ids:
        role_assignment = authorization.RoleAssignment("roleAssignment",
            principal_id=object_id,
            principal_type="User",
            role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",
            scope="/subscriptions/ff01e3b6-b71f-446a-837b-0eb93efd5053/resourceGroups/resource_group53c97c7c/providers/Microsoft.Storage/storageAccounts/sa5b82a03b"
        )
else:
    print("No users specified for storage read access, skipping...")


# %%
config_file = f"""
CLIENT_ID = "{config.get('client-id')}"  # Application (client) ID of app registration
AUTHORITY = "https://login.microsoftonline.com/{config.get('tenant-id')}"
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
KEYVAULT_URI = "https://{vault.name}.vault.azure.net/"
SECRET_NAME = "{secret.name}"
ROLES = []
CHECK_PROD = "IS_PROD"


# Data files
data_files = {
    "iris": {
        "account_url": "https://{account.name}.blob.core.windows.net",
        "container": "test",
        "filename": "iris.csv",
    }
}
"""

with open("../config.py") as file:
    file.write(config_file)