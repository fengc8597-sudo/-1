"""Jira 查询 MCP Server 核心逻辑单元测试（无需真实 Jira）。"""

from unittest import mock

import jira_assistant.server as server
from jira_assistant.server import _format_issue_detail, _format_issue_list


def _fake_client(**overrides):
    """构造一个返回可控结果的假 JiraClient。"""
    client = mock.MagicMock()
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


@mock.patch("jira_assistant.server._get_client")
def test_get_issue_detail_ok(mock_get):
    client = _fake_client()
    client.get_issue.return_value = {
        "key": "SCRUM-2",
        "fields": {
            "summary": "实现业务场景智能助手能力",
            "issuetype": {"name": "故事"},
            "status": {"name": "正在进行"},
            "project": {"key": "SCRUM"},
            "assignee": None,
            "duedate": "2026-09-21",
            "description": None,
        },
    }
    mock_get.return_value = client
    out = server.get_issue_detail("SCRUM-2")
    assert "SCRUM-2" in out
    assert "实现业务场景智能助手能力" in out
    assert "正在进行" in out
    assert "2026-09-21" in out


@mock.patch("jira_assistant.server._get_client")
def test_get_issue_detail_not_found(mock_get):
    client = _fake_client()
    client.get_issue.side_effect = server_jira_error(404)
    mock_get.return_value = client
    assert server.get_issue_detail("SCRUM-999") == "未查询到该工单。"


@mock.patch("jira_assistant.server._get_client")
def test_list_issues_empty(mock_get):
    client = _fake_client(list_issues=mock.MagicMock(return_value=[]))
    mock_get.return_value = client
    assert server.list_issues("SCRUM", "待办") == "未查询到 SCRUM 项目（状态：待办） 的工单。"


def server_jira_error(status):
    from jira_assistant.jira_client import JiraError

    return JiraError("err", status=status)


def test_format_issue_list_structure():
    issues = [
        {
            "key": "SCRUM-4",
            "fields": {
                "summary": "子任务 2.1",
                "status": {"name": "待办"},
                "assignee": None,
                "duedate": None,
            },
        }
    ]
    out = _format_issue_list(issues)
    assert "SCRUM-4" in out
    assert "子任务 2.1" in out


def test_format_issue_detail_structure():
    issue = {
        "key": "X-1",
        "fields": {
            "summary": "s",
            "issuetype": {"name": "任务"},
            "status": {"name": "待办"},
            "project": {"key": "X"},
            "assignee": None,
            "duedate": None,
            "description": None,
        },
    }
    out = _format_issue_detail(issue)
    assert "X-1" in out
    assert "待办" in out


# ---- JiraClient / Config 单元测试（mock HTTP，无真实凭据） ----

_CONFIG_ENV = {
    "JIRA_BASE_URL": "https://x.atlassian.net",
    "JIRA_EMAIL": "a@b.com",
    "JIRA_API_TOKEN": "tok",
}


def _config_from_env_ctx(env: dict):
    """进入带 env 的环境，返回 args 供 with 使用。"""
    return mock.patch.dict("os.environ", env, clear=True)


def test_config_from_env_ok():
    with _config_from_env_ctx({**_CONFIG_ENV, "JIRA_BASE_URL": "https://x.atlassian.net/"}):
        from jira_assistant.config import Config

        cfg = Config.from_env()
    assert cfg.base_url == "https://x.atlassian.net"
    assert cfg.email == "a@b.com"
    assert cfg.api_token == "tok"


def test_config_from_env_missing_key():
    """缺少环境变量时抛 KeyError。"""
    from jira_assistant.config import Config

    with mock.patch.dict("os.environ", {}, clear=True):
        try:
            Config.from_env()
            raised = False
        except KeyError:
            raised = True
    assert raised is True


def test_config_from_env_empty_value():
    """键存在但为空时抛 RuntimeError。"""
    from jira_assistant.config import Config

    with mock.patch.dict(
        "os.environ",
        {"JIRA_BASE_URL": "x", "JIRA_EMAIL": "", "JIRA_API_TOKEN": "tok"},
        clear=True,
    ):
        try:
            Config.from_env()
            raised = False
        except RuntimeError:
            raised = True
    assert raised is True


def test_jira_client_list_issues_status_filter():
    from jira_assistant.config import Config
    from jira_assistant.jira_client import JiraClient

    with _config_from_env_ctx(_CONFIG_ENV):
        cfg = Config.from_env()
    client = JiraClient(cfg)
    issues = [
        {"key": "A-1", "fields": {"status": {"name": "待办"}}},
        {"key": "A-2", "fields": {"status": {"name": "已完成"}}},
    ]
    with mock.patch.object(client._session, "get") as mget:
        mget.return_value = mock.Mock(status_code=200, ok=True, json=lambda: {"issues": issues})
        out = client.list_issues("A", "待办")
    assert [i["key"] for i in out] == ["A-1"]


def test_jira_client_get_issue_and_errors():
    from jira_assistant.config import Config
    from jira_assistant.jira_client import JiraClient, JiraError

    with _config_from_env_ctx(_CONFIG_ENV):
        cfg = Config.from_env()
    client = JiraClient(cfg)

    with mock.patch.object(client._session, "get") as mget:
        mget.return_value = mock.Mock(status_code=404, ok=False, json=lambda: {})
        try:
            client.get_issue("X-9")
            raised = False
        except JiraError as e:
            raised = e.status == 404
    assert raised is True

    # 401
    with mock.patch.object(client._session, "get") as mget:
        mget.return_value = mock.Mock(status_code=401, ok=False, json=lambda: {})
        try:
            client.get_issue("X-9")
            raised = False
        except JiraError as e:
            raised = e.status == 401
    assert raised is True

    # 500
    with mock.patch.object(client._session, "get") as mget:
        mget.return_value = mock.Mock(status_code=500, ok=False, json=lambda: {})
        try:
            client.get_issue("X-9")
            raised = False
        except JiraError as e:
            raised = e.status == 500
    assert raised is True

    # 成功路径
    payload = {"key": "X-1", "fields": {"summary": "s"}}
    with mock.patch.object(client._session, "get") as mget:
        mget.return_value = mock.Mock(status_code=200, ok=True, json=lambda: payload)
        out = client.get_issue("X-1")
    assert out == payload
