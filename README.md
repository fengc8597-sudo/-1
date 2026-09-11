# Jira 智能助手（MCP Server）

[![CI](https://github.com/fengc8597-sudo/-1/workflows/CI/badge.svg)](https://github.com/fengc8597-sudo/-1/actions)

业务场景智能助手，将 **Jira 工单查询**封装为 MCP 工具，供 GienCoder / AI 助手通过 stdio 调用。
需求来源：Jira SCRUM-2「实现业务场景智能助手能力」。

## 功能
- 列出指定项目下的工单（可按状态过滤），返回 编号 / 标题 / 状态 / 经办人 / 截止时间。
- 获取单条工单完整详情；工单不存在时返回「未查询到该工单」。
- 仅只读访问 Jira，不能修改、删除工单。

## 工具
| 工具 | 说明 |
|------|------|
| `list_issues(project_key, status)` | 列出项目工单，可按状态过滤 |
| `get_issue_detail(issue_key)` | 获取单条工单详情 |

## 配置（环境变量）
| 变量 | 说明 |
|------|------|
| `JIRA_BASE_URL` | Jira 地址，如 `https://xxx.atlassian.net` |
| `JIRA_EMAIL` | Jira 账号邮箱 |
| `JIRA_API_TOKEN` | Jira API Token |

## 运行
```bash
pip install -r requirements.txt
JIRA_BASE_URL=... JIRA_EMAIL=... JIRA_API_TOKEN=... python -m jira_assistant.server
```

默认通过 stdio 承载 MCP 协议，供支持 MCP 的客户端（如 GienCoder）连接。