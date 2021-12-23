# This file is not in use and is really just and example of how one can
# do and app registration in Azure AD with Python

import json
import subprocess
from datetime import datetime, timedelta

from azure.identity import AzureCliCredential
from msgraph.core import GraphClient
from requests.models import HTTPError

# %%
# Get tenant id
result = subprocess.run(["az", "account", "tenant", "list"], stdout=subprocess.PIPE)
tenant_id = json.loads(result.stdout.decode("utf-8"))[0]["tenantId"]

# %%
# Create app registration in Azure AD
graph = GraphClient(
    credential=AzureCliCredential(), scopes=["https://graph.microsoft.com/.default"]
)

response = graph.post(
    "/applications",
    data=json.dumps({"displayName": "NGTT-test-app"}),
    headers={"Content-Type": "application/json"},
)

if response.status_code != 201:
    raise HTTPError(response.json())

app_reg_metadata = response.json()
object_id = app_reg_metadata["id"]
app_id = app_reg_metadata["appId"]

print("App registration completed successfully")
print(f"Object ID: {object_id}")
print(f"Application ID: {app_id}")

# %%
# Add owner to the app registration
# TODO: Have this as manual input
owners = ["abcd"]

for owner in owners:
    user_id = graph.get(f"/users/{owner}@equinor.com").json()["id"]
    response = graph.post(
        f"/applications/{object_id}/owners/$ref",
        data=json.dumps(
            {
                "@odata.id": f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}"
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    if response.status_code != 201:
        if (
            response.text
            and response.json()["error"]["message"]
            == "One or more added object references already exist for the following modified properties: 'owners'."
        ):
            print(f"User {owner} is already an owner of the application, skipping...")
        else:
            raise HTTPError(response.json())
    else:
        print(f"Successfully added {owner} as owner to the app registration")

# %%
expiry_date = datetime.utcnow() + timedelta(days=360)

response = graph.post(
    f"/applications/{object_id}/addPassword",
    data=json.dumps(
        {
            "passwordCredential": {
                "displayName": "Client secret",
                "endDateTime": expiry_date.isoformat(),
            }
        }
    ),
    headers={"Content-Type": "application/json"},
)

if response.status_code != 200:
    raise HTTPError(response.json())

client_secret = response.json()["secretText"]

# %%
subprocess.run(["pulumi", "stack", "select", "dev"])
subprocess.run(["pulumi", "config", "set", "tenant-id", tenant_id])
subprocess.run(["pulumi", "config", "set", "app-id", app_id])
subprocess.run(["pulumi", "config", "set", "--secret", "client-secret", client_secret])


# %%
# Destroy app registration
response = graph.delete(f"/applications/{object_id}")
if response.status_code != 204 and response.status_code != 201:
    raise HTTPError(response.json())
# %%
