from __future__ import annotations

import os

from helpers.data_source_test_helper import DataSourceTestHelper


class SnowflakeDataSourceTestHelper(DataSourceTestHelper):
    def _create_database_name(self) -> str | None:
        return os.getenv("SNOWFLAKE_DATABASE", "soda_test")

    def _create_data_source_yaml_str(self) -> str:
        """
        Called in _create_data_source_impl to initialized self.data_source_impl
        self.database_name and self.schema_name are available if appropriate for the data source type
        """
        if os.getenv("SNOWFLAKE_OAUTH_CLIENT_ID"):
            return self._create_oauth_data_source_yaml_str()
        # Unset, the user's default warehouse applies.
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
        warehouse_line = f"\n                warehouse: {warehouse}" if warehouse else ""
        return f"""
            type: snowflake
            name: {self.name}
            connection:
                account: {os.getenv("SNOWFLAKE_ACCOUNT")}
                user: {os.getenv("SNOWFLAKE_USER")}
                password: {os.getenv("SNOWFLAKE_PASSWORD")}{warehouse_line}
                database: {self.dataset_prefix[0]}
        """

    def _create_oauth_data_source_yaml_str(self) -> str:
        # The OAuth identity has no default warehouse.
        oauth_scope = os.getenv("SNOWFLAKE_OAUTH_SCOPE")
        oauth_scope_line = f"oauth_scope: '{oauth_scope}'" if oauth_scope else ""
        return f"""
            type: snowflake
            name: {self.name}
            connection:
                account: {os.getenv("SNOWFLAKE_ACCOUNT")}
                authenticator: OAUTH_CLIENT_CREDENTIALS
                oauth_client_id: '{os.getenv("SNOWFLAKE_OAUTH_CLIENT_ID")}'
                oauth_client_secret: '{_required_env("SNOWFLAKE_OAUTH_CLIENT_SECRET")}'
                oauth_token_request_url: '{_required_env("SNOWFLAKE_OAUTH_TOKEN_REQUEST_URL")}'
                {oauth_scope_line}
                warehouse: {os.getenv("SNOWFLAKE_WAREHOUSE", "SODA_TESTING_WH")}
                database: {self.dataset_prefix[0]}
        """

    def _adjust_schema_name(self, schema_name: str) -> str:
        return schema_name.upper()

    def _snapshot_passthrough_queries(self) -> dict:
        from soda_core.common.data_source_results import QueryResult

        # Snowflake lazily runs SELECT CURRENT_WAREHOUSE() to detect the active warehouse.
        # This is session-level metadata that shouldn't be part of per-test snapshots.
        warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "SODA_TESTING_WH")
        return {
            "SELECT CURRENT_WAREHOUSE()": QueryResult(rows=[(warehouse,)], columns=None),
        }


def _required_env(name: str) -> str:
    # Rendered unset, the value would be the string 'None'.
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} must be set when SNOWFLAKE_OAUTH_CLIENT_ID is")
    return value
