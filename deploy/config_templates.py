from typing import List

import pulumi
from pulumi_azure_native.web.list_web_app_publishing_credentials import ListWebAppPublishingCredentialsResult


def create_config_file(args: List[str]) -> None:
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

def create_publish_profile(publish_profile: ListWebAppPublishingCredentialsResult, app_url: str) -> str:
    # Make mypy happy
    assert publish_profile.scm_uri is not None
    assert publish_profile.publishing_password is not None

    publish_url = publish_profile.scm_uri.split("@")[-1] + ":443"
    user_name = publish_profile.publishing_user_name
    user_pwd = publish_profile.publishing_password
    destination_app_url = "https://" + app_url

    publish_profile_string = f"""<publishData>
    <publishProfile
        publishUrl="{publish_url}"
        userName="{user_name}"
        userPWD="{user_pwd}"
        destinationAppUrl="{destination_app_url}"
    >
    </publishProfile>
</publishData>"""

    return publish_profile_string