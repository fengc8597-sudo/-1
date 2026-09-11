"""Jira REST 只读客户端。

仅提供 GET 查询（读取工单、列出项目任务），不包含任何写操作，
以满足需求中的"只能读取，不能修改、删除工单"权限约束。
"""

import base64
from typing import Optional

import requests

from jira_assistant.config import Config


class JiraError(Exception):
    def __init__(self, message: str, status: Optional[int] = None):
        super().__init__(message)
        self.status = status


class JiraClient:
    def __init__(self, config: Config):
        self._base_url = config.base_url
        self._session = requests.Session()
        token = base64.b64encode(
            f"{config.email}:{config.api_token}".encode()
        ).decode("utf-8")
        self._session.headers.update(
            {"Authorization": f"Basic {token}", "Accept": "application/json"}
        )

    def list_issues(self, project_key: str, status: Optional[str] = None) -> list:
        jql = f"project = {project_key} ORDER BY key ASC"
        issues = self._get_issues(jql)
        # JQL 对中文状态名的过滤在部分实例上不可靠，统一在本地按 status.name 精确过滤
        if status:
            issues = [i for i in issues if (i["fields"].get("status") or {}).get("name") == status]
        return issues

    def get_issue(self, issue_key: str) -> dict:
        url = f"{self._base_url}/rest/api/3/issue/{issue_key}"
        fields = "summary,issuetype,status,project,assignee,duedate,description"
        resp = self._session.get(url, params={"fields": fields}, timeout=10)
        self._raise_for_status(resp, issue_key)
        return resp.json()

    def _get_issues(self, jql: str) -> list:
        url = f"{self._base_url}/rest/api/3/search/jql"
        resp = self._session.get(
            url,
            params={
                "jql": jql,
                "fields": "summary,status,assignee,duedate",
                "maxResults": "50",
            },
            timeout=10,
        )
        self._raise_for_status(resp, jql)
        data = resp.json()
        return data.get("issues", [])

    @staticmethod
    def _raise_for_status(resp, subject: str) -> None:
        if resp.status_code == 404:
            raise JiraError(f"未查询到：{subject}", status=404)
        if resp.status_code == 401 or resp.status_code == 403:
            raise JiraError("鉴权失败，请检查 Jira 凭据", status=resp.status_code)
        if not resp.ok:
            raise JiraError(f"Jira 请求失败（HTTP {resp.status_code}）", status=resp.status_code)
