from typing import Union
from src.models.AppSettings import AppSettings
from azure.keyvault.secrets import SecretClient

def _format_roles(roles: Union[str, None]):
    if roles == None: raise ValueError("ROLES environment variable is not set.")
    if roles == "": roles_list = []
    else: roles_list = roles.split(",")
    return roles_list

def get_variables(secret_client: SecretClient):
    client_id = secret_client.get_secret("clientid")
    authority = secret_client.get_secret("authority")
    redirect_path = secret_client.get_secret("redirectpath")
    secret_name = secret_client.get_secret("secretname")
    storage_name = secret_client.get_secret("storagename")
    roles = secret_client.get_secret("roles")

    return AppSettings(
        client_id=client_id.value,
        authority=authority.value,
        redirect_path=redirect_path.value,
        secret_name=secret_name.value,
        storage_name=storage_name.value,
        roles=_format_roles(roles.value),
    )