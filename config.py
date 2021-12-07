CLIENT_ID = "9cc99e1d-b6c6-4d5e-9f4f-dd7ef592fb54"  # Application (client) ID of app registration
AUTHORITY = "https://login.microsoftonline.com/3aa4a235-b6e2-48d5-9195-7fcf05b459b0"
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
KEYVAULT_URI = "https://ngtt-dashboard-vault.vault.azure.net/"
SECRET_NAME = "ngtt-dashboard"
ROLES = []
CHECK_PROD = "IS_PROD"


# Data files
data_files = {
    "iris": {
        "account_url": "https://sa5b82a03b.blob.core.windows.net",
        "container": "test",
        "filename": "iris.csv",
    }
}
