"""配置读取：从环境变量加载 Jira 连接信息。"""

import os


class Config:
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token

    @classmethod
    def from_env(cls) -> "Config":
        base_url = os.environ["JIRA_BASE_URL"]
        email = os.environ["JIRA_EMAIL"]
        api_token = os.environ["JIRA_API_TOKEN"]
        if not all([base_url, email, api_token]):
            raise RuntimeError("缺少 JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN 环境变量")
        return cls(base_url, email, api_token)