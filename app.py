import logging
import os
import traceback
from typing import Any, List, Text, Union

import requests
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from opencensus.ext.azure.log_exporter import AzureLogHandler
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.wrappers import Response

import config
from src.utils.auth import Auth, login_required
from src.utils.DataLoader import DataLoader
from src.utils.environment import get_variables
from views.DashApp import DashApp
from views.IrisExample import IrisExample

credential = DefaultAzureCredential(
    exclude_visual_studio_code_credential=True,
    exclude_shared_token_cache_credential=True,
)
secret_client = SecretClient(
    vault_url=os.environ["KEYVAULT_URI"], credential=credential
)

if os.getenv("IS_PROD"):
    logger = logging.getLogger(__name__)
    logger.addHandler(
        AzureLogHandler(
            connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        )
    )

app_settings = get_variables(secret_client)

data_loader = DataLoader(credential)

app = Flask(__name__, template_folder="html_templates", static_folder="assets")
app.config.from_object(
    config
)  # This is needed by flask session to access the "SESSION_TYPE" config value
Session(app)

for _, value in config.data_files.items():
    if "account_url" not in value:
        value[
            "account_url"
        ] = f"https://{app_settings.storage_name}.blob.core.windows.net"

# Extend this list with more dash apps
dash_apps: List[DashApp] = [
    IrisExample(
        config.DASH_URL_BASE + "iris-example/",
        {
            "name": "Iris Example",
        },
        data_loader,
        {
            "iris": config.data_files["iris"],
        },
    ),
]

auth = Auth(app_settings, secret_client)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # type: ignore

for dash_app in dash_apps:
    dash_app.initialize(app)
    for view_func in dash_app.app.server.view_functions:
        dash_app.app.server.view_functions[view_func] = login_required(
            auth, app_settings.roles, config.SCOPES
        )(dash_app.app.server.view_functions[view_func])


@app.route("/")
@login_required(auth, app_settings.roles, config.SCOPES)
def index() -> Text:
    if "flow" not in session:
        session["flow"] = auth._build_auth_code_flow(scopes=config.SCOPES)
        session["user"] = session.get("id_token_claims")
    name = ""
    if session is not None and "user" in session and session["user"] is not None:
        name = session["user"]["name"].split(" ")[0]
    return render_template(
        "index.html",
        auth_url=session["flow"]["auth_uri"],
        name=name,
    )


@app.route("/test")
@login_required(auth, app_settings.roles, config.SCOPES)
def test() -> Any:
    token = auth._get_token_from_cache(config.SCOPES)
    graph_data = requests.get(
        "http://localhost:5001/api",
        headers={"Authorization": "Bearer " + token["access_token"]},
    ).json()
    return graph_data


@app.route("/menu")
@login_required(auth, app_settings.roles, config.SCOPES)
def menu() -> Text:
    return render_template(
        "menu.html",
        name=session["user"]["name"],
        dash_apps=dash_apps,
    )


@app.route("/not_signed_in")
def not_signed_in() -> Text:
    session["flow"] = auth._build_auth_code_flow(scopes=config.SCOPES)
    return render_template("not_signed_in.html", auth_url=session["flow"]["auth_uri"])


@app.route("/access_denied")
def access_denied() -> Text:
    return render_template("access_denied.html")


@app.route(app_settings.redirect_path)
def authorized() -> Union[Text, Any]:
    try:
        cache = auth._load_cache()
        result = auth._build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args
        )
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        auth._save_cache(cache)
    except:  # noqa: E722
        return render_template(
            "auth_error.html",
            result={
                "error": "Exception",
                "error_description": traceback.format_exc(),
            },
        )
    return redirect(url_for("index"))


@app.route("/logout")
def logout() -> Response:
    session.clear()
    return redirect(
        app_settings.authority
        + "/oauth2/v2.0/logout"
        + "?post_logout_redirect_uri="
        + url_for("index", _external=True)
    )


@app.route("/graphcall")
@login_required(auth, app_settings.roles, config.SCOPES)
def graphcall() -> Text:
    token = auth._get_token_from_cache(config.SCOPES)
    graph_data = requests.get(
        config.ENDPOINT,
        headers={"Authorization": "Bearer " + token["access_token"]},
    ).json()
    return render_template("display.html", result=graph_data)


app.jinja_env.globals.update(_build_auth_code_flow=auth._build_auth_code_flow)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
