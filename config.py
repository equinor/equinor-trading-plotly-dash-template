# The absolute URL must match the redirect URI you set
# in the app's registration in the Azure portal.
ENDPOINT = (
    "https://graph.microsoft.com/v1.0/me"  # This resource requires no admin consent
)
SCOPES = ["User.ReadBasic.All"]
SESSION_TYPE = (
    "filesystem"  # Specifies the token cache should be stored in server-side session
)

DASH_URL_BASE = "/views/"

# Data files
# Add the "account_url" here manually if you want to use another storage account than the default.
data_files = {
    "iris": {
        "container": "test",
        "filename": "iris.csv",
    }
}
