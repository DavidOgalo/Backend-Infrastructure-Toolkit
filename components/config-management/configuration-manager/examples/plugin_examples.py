"""
Example plugin implementations for ConfigManager extensibility.
"""

from config_manager import ConfigHookPlugin, ConfigSourcePlugin


class VaultConfigPlugin(ConfigSourcePlugin):
    """Example: Loads config from a (mocked) Vault service."""

    def load(self):
        # Simulate fetching secrets from Vault
        return {"secrets": {"api_key": "vault-key", "db_password": "vault-db-pass"}}


class SlackNotificationHook(ConfigHookPlugin):
    """Example: Sends notification on config change (mocked)."""

    def on_config_change(self, event, old_config, new_config):
        print(f"[Slack] Config changed! Event: {event}")
        # Here you would send a real Slack message


if __name__ == "__main__":
    from config_manager import ConfigManager

    # Register plugins
    config = ConfigManager()
    config.add_source_plugin(VaultConfigPlugin())
    config.add_hook_plugin(SlackNotificationHook())
    # Trigger a config change to see hook in action
    config.set("feature_flags.new_ui", True)
    # Access plugin-loaded secrets
    print(
        "Vault secrets:",
        config.get("secrets.api_key"),
        config.get("secrets.db_password"),
    )
