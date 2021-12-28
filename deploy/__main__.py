"""An Azure RM Python Pulumi program"""

import uuid

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

from config import create_config_file

config = pulumi.Config()
client_config = authorization.get_client_config()

# Azure Active Directory related resources
app_registration = ad.Application(
    config.get("project-name-prefix"),
    display_name=config.get("project-name-prefix"),
    owners=[client_config.object_id]
)

app_client_secret = ad.ApplicationPassword(
    config.get("project-name-prefix"),
    application_object_id=app_registration.object_id,
    display_name="Client secret",
    end_date_relative="8700h",
)

service_principal = ad.ServicePrincipal(
    config.get("project-name-prefix"),
    application_id=app_registration.application_id,
    app_role_assignment_required=False,
    owners=[client_config.object_id],
)

# CUSTOM_IMAGE = "cicddeployment"

# Create an Azure Resource Group
resource_group = resources.ResourceGroup(config.get("project-name-prefix"))


# Create an Azure resource (Storage Account)
account = storage.StorageAccount(
    config.get("project-name-prefix")[:16],
    resource_group_name=resource_group.name,
    sku=storage.SkuArgs(
        name=storage.SkuName.STANDARD_LRS,
    ),
    kind=storage.Kind.STORAGE_V2,
)

container = storage.BlobContainer(
    config.get("test-filecontainer"),
    resource_group_name=resource_group.name,
    account_name=account.name,
)

blob = storage.Blob(
    config.get("test-filename"),
    resource_group_name=resource_group.name,
    account_name=account.name,
    container_name=container.name,
    source=pulumi.FileAsset("../test/iris.csv"),
    content_type="text",
)


plan = web.AppServicePlan(
    config.get("project-name-prefix"),
    resource_group_name=resource_group.name,
    kind="Linux",
    reserved=True,
    sku=web.SkuDescriptionArgs(
        name="B1",
        tier="Basic",
    ),
)


app_insights = insights.Component(
    config.get("project-name-prefix"),
    application_type=insights.ApplicationType.WEB,
    kind="web",
    resource_group_name=resource_group.name,
)

app = web.WebApp(
    config.get("project-name-prefix"),
    resource_group_name=resource_group.name,
    server_farm_id=plan.id,
    site_config=web.SiteConfigArgs(
        app_command_line='gunicorn --bind=0.0.0.0 --timeout 600 "app:app()"',
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

app_source_control = web.WebAppSourceControl(
    config.get("project-name-prefix"),
    name=app.name,
    resource_group_name=resource_group.name,
    branch="main",
    is_git_hub_action=True,
    repo_url=config.get("repo-url"),
    git_hub_action_configuration=web.GitHubActionConfigurationArgs(
        generate_workflow_file=False,
        is_linux=True,
    ),
)

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
    config.get("project-name-prefix"),
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
    vault_name=config.get("project-name-prefix")[:16] + str(uuid.uuid4())[:8],
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

pulumi.Output.all(
    client_config.client_id,
    client_config.tenant_id,
    vault.name,
    secret.name,
    account.name,
).apply(create_config_file)
