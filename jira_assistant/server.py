"""业务场景智能助手：Jira 查询 MCP Server。

将 Jira 工单查询封装为 MCP 工具，供 GienCoder / AI 助手通过 stdio 调用。
需求来源：Jira SCRUM-2「实现业务场景智能助手能力」。
"""

from typing import Optional

from mcp.server.fastmcp import FastMCP

from jira_assistant.config import Config
from jira_assistant.jira_client import JiraClient

# MCP server 名称（供 GienCoder/AI 识别）
mcp = FastMCP("jira-assistant")

_cfg: Optional[Config] = None
_client: Optional[JiraClient] = None


def _get_client() -> JiraClient:
    """惰性初始化 Jira 客户端，避免 import 时依赖环境变量。"""
    global _cfg, _client
    if _client is None:
        _cfg = Config.from_env()
        _client = JiraClient(_cfg)
    return _client


@mcp.tool()
def list_issues(project_key: str, status: Optional[str] = None) -> str:
    """列出指定项目下的工单。

    可按状态过滤（如"待办"、"正在进行"）。返回结构化文本，
    每条包含任务编号、标题、状态、经办人、截止时间。

    Args:
        project_key: 项目键，例如 SCRUM。
        status: 可选的状态名称过滤，例如 待办。
    """
    client = _get_client()
    try:
        issues = client.list_issues(project_key, status=status)
    except Exception as exc:  # 对外隐藏内部细节
        return _friendly_error(exc)

    if not issues:
        status_txt = f"（状态：{status}）" if status else ""
        return f"未查询到 {project_key} 项目{status_txt} 的工单。"
    return _format_issue_list(issues)


@mcp.tool()
def get_issue_detail(issue_key: str) -> str:
    """获取单条工单的完整详情。

    Args:
        issue_key: 工单号，例如 SCRUM-2。
    """
    if not issue_key or not issue_key.strip():
        return "工单号不能为空，请重试。"
    client = _get_client()
    try:
        issue = client.get_issue(issue_key)
    except Exception as exc:
        if _is_not_found(exc):
            return "未查询到该工单。"
        return _friendly_error(exc)
    return _format_issue_detail(issue)


def _is_not_found(exc: Exception) -> bool:
    return getattr(exc, "status", None) == 404 or "不存在" in str(exc)


def _friendly_error(exc: Exception) -> str:
    # 需求：不输出原始报错堆栈
    return "查询失败，请稍后重试。"


def _format_issue_list(issues: list) -> str:
    lines = [f"共 {len(issues)} 个工单："]
    for i in issues:
        lines.append(_issue_one_line(i))
    return "\n".join(lines)


def _issue_one_line(i: dict) -> str:
    key = i.get("key", "-")
    fields = i.get("fields", {})
    summary = fields.get("summary", "")
    status = (fields.get("status") or {}).get("name", "")
    assignee = (fields.get("assignee") or {}).get("displayName", "未分配")
    duedate = fields.get("duedate", "无") or "无"
    return f"- {key} | {summary} | 状态：{status} | 经办人：{assignee} | 截止：{duedate}"


def _format_issue_detail(issue: dict) -> str:
    key = issue.get("key", "-")
    fields = issue.get("fields", {})
    summary = fields.get("summary", "")
    itype = (fields.get("issuetype") or {}).get("name", "")
    status = (fields.get("status") or {}).get("name", "")
    project = (fields.get("project") or {}).get("key", "")
    assignee = (fields.get("assignee") or {}).get("displayName", "未分配")
    duedate = fields.get("duedate", "无") or "无"
    description = _adf_to_text(fields.get("description")) if fields.get("description") else ""
    return (
        f"工单：{key} ({itype})\n"
        f"标题：{summary}\n"
        f"项目：{project}\n"
        f"状态：{status}\n"
        f"经办人：{assignee}\n"
        f"截止日期：{duedate}\n"
        f"描述：{description}"
    )


def _adf_to_text(node) -> str:
    """将 Jira ADF（Atlassian Document Format）节点提取为纯文本。"""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    node_type = node.get("type")
    content = node.get("content") or []
    if node_type == "text":
        return node.get("text", "")
    parts = [_adf_to_text(c) for c in content]
    text = "".join(p for p in parts)
    if node_type in ("paragraph", "heading"):
        return text + "\n"
    if node_type == "codeBlock":
        return "```\n" + text + "\n```\n"
    return text


def main() -> None:
    """命令行入口：启动 stdio MCP server。"""
    mcp.run()


if __name__ == "__main__":
    main()
