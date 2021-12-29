from pulumi_azure_native.web.list_web_app_publishing_credentials import ListWebAppPublishingCredentialsResult
import pulumi_github as gh

from config_templates import create_publish_profile

def add_publish_profile_and_web_app_name(publish_profile: ListWebAppPublishingCredentialsResult, app_url: str, app_name: str, repo_url: str):
    # Make mypy happy
    assert publish_profile.scm_uri is not None
    assert publish_profile.publishing_password is not None

    gh.ActionsSecret("AZURE_WEBAPP_PUBLISH_PROFILE",
        secret_name="AZURE_WEBAPP_PUBLISH_PROFILE",
        repository=repo_url,
        plaintext_value=create_publish_profile(
            publish_profile.scm_uri,
            publish_profile.publishing_user_name,
            publish_profile.publishing_password,
            "https://" + app_url
        ),
    )

    gh.ActionsSecret("AZURE_WEBAPP_NAME",
        secret_name="AZURE_WEBAPP_NAME",
        repository=repo_url,
        plaintext_value=app_name
    )