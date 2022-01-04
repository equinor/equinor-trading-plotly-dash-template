import functools
import os
from typing import Any, Callable, Dict, List, Optional

import msal
from azure.keyvault.secrets import SecretClient
from flask import redirect, session, url_for

from src.models.AppSettings import AppSettings


class Auth:
    def __init__(self, app_settings: AppSettings, client: SecretClient):
        self.app_settings = app_settings

        self.client_credential = client.get_secret(self.app_settings.secret_name).value

    def _load_cache(self) -> msal.SerializableTokenCache:
        cache = msal.SerializableTokenCache()
        if session.get("token_cache"):
            cache.deserialize(session["token_cache"])
        return cache

    def _save_cache(self, cache: Any) -> None:
        if cache.has_state_changed:
            session["token_cache"] = cache.serialize()

    def _build_msal_app(
        self, cache: Any = None, authority: Any = None
    ) -> msal.ConfidentialClientApplication:
        return msal.ConfidentialClientApplication(
            self.app_settings.client_id,
            authority=authority or self.app_settings.authority,
            client_credential=self.client_credential,
            token_cache=cache,
        )

    def _build_auth_code_flow(
        self, authority: Any = None, scopes: Any = None
    ) -> Dict[str, Any]:
        return self._build_msal_app(authority=authority).initiate_auth_code_flow(
            scopes or [], redirect_uri=url_for("authorized", _external=True)
        )

    def _get_token_from_cache(self, scope: Any = None) -> Any:
        cache = self._load_cache()
        cca = self._build_msal_app(cache=cache)
        accounts = cca.get_accounts()
        if accounts:
            result = cca.acquire_token_silent(scope, account=accounts[0])
            self._save_cache(cache)
            return result


# TODO: Check ID token expiration?
# TODO: Check other factors?
def login_required(
    auth: Auth, roles: List[str] = None, scopes: Optional[List[str]] = []
) -> Callable:
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def secure_function(*args: Any, **kwargs: Any) -> Callable:
            if os.getenv("AUTH") == "skip":
                if os.getenv("IS_PROD"):
                    raise EnvironmentError("Auth bypass is not allowed in production.")
                print("WARNING: AUTH BYPASS IS ACTIVE. THIS SHOULD ONLY BE ACTIVE IN DEV.")
                return func(*args, **kwargs)
            token = auth._get_token_from_cache(scopes)
            if not token:
                return redirect(url_for("not_signed_in", reason="login"))
            if "roles" not in session["user"].keys() or (
                roles and not any(role in session["user"]["roles"] for role in roles)
            ):
                return redirect(url_for("access_denied", reason="login"))
            return func(*args, **kwargs)

        return secure_function

    return wrapper
