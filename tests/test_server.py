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
        {"key": "SCRUM-4", "fields": {"summary": "子任务 2.1", "status": {"name": "待办"}, "assignee": None, "duedate": None}}
    ]
    out = _format_issue_list(issues)
    assert "SCRUM-4" in out
    assert "子任务 2.1" in out


def test_format_issue_detail_structure():
    issue = {
        "key": "X-1",
        "fields": {"summary": "s", "issuetype": {"name": "任务"}, "status": {"name": "待办"}, "project": {"key": "X"}, "assignee": None, "duedate": None, "description": None},
    }
    out = _format_issue_detail(issue)
    assert "X-1" in out
    assert "待办" in out