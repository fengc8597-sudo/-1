# SDD — 业务场景智能助手（SCRUM-2）

## 1. 需求来源
- Jira 工单：SCRUM-2「实现业务场景智能助手能力」（故事，进行中）
- 需求描述：见 SCRUM-2 最新评论（业务背景 / 功能需求 / 非功能需求 / 验收标准）

## 2. 目标
为内部业务系统接入 AI 智能助手，面向业务人员提供**自然语言交互**去查询 Jira 工单信息（工单详情、项目任务列表、任务状态），降低操作门槛。

## 3. 关键需求要点
### 功能需求
1. 支持自然语言提问，例如「查询 SCRUM 项目下所有未完成工单」「汇总本周任务」。
2. 智能助手可调用 Jira 接口读取工单：获取工单详情、查询项目任务列表、查看任务状态。
3. 回答简洁、结构化，区分任务编号、标题、处理人、截止时间。
4. 权限控制：只读当前项目数据，不能修改、删除工单。
5. 异常处理：工单不存在时返回友好提示，不输出原始报错堆栈。

### 非功能需求
- 单次问答响应 ≤ 3 秒。
- 支持对话上下文记忆、多轮追问。
- 不输出敏感内部数据。

### 验收标准
1. 提问「列出 SCRUM 项目所有待办任务」→ 正确返回 SCRUM-1、SCRUM-2 信息。
2. 提问「查看 SCRUM-2 工单详情」→ 返回完整任务标题、截止日期、状态。
3. 输入不存在的工单号 → 返回提示「未查询到该工单」。

## 4. 技术方案：MCP Server（Python）
将 Jira 查询封装为 MCP 工具，供 GienCoder / AI 助手通过 MCP 协议（stdio）调用。

- 协议：MCP (Model Context Protocol)
- 语言/运行时：Python 3，官方 `mcp` SDK（FastMCP）
- 配置（环境变量）：`JIRA_BASE_URL`、`JIRA_EMAIL`、`JIRA_API_TOKEN`
- 认证：Bearer / Basic，Jira REST API v3

## 5. MCP 工具清单
| 工具 | 作用 | 对应验收 |
|------|------|----------|
| `list_issues(project_key, status)` | 列出项目工单（可按状态过滤），返回 编号/标题/状态/经办人/截止时间 | 验收 1 |
| `get_issue_detail(issue_key)` | 获取单条工单完整详情；不存在返回「未查询到该工单」 | 验收 2、3 |

## 6. 只读与安全约束
- 客户端仅用 GET 方法访问 Jira，绝不调用创建/更新/删除接口。
- 错误信息脱敏：异常时不外泄 token、堆栈、内部路径。

## 7. 目录结构
```
jira_assistant/
  __init__.py
  server.py        # FastMCP server 入口与工具定义
  jira_client.py   # Jira REST 只读客户端
  config.py        # 环境变量读取
requirements.txt
pyproject.toml