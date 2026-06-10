# AI 与网络攻防

---


# 几个问题

- 你目前使用的AI是什么？Chatgpt？Deepseek？豆包？
- 你目前怎么使用的AI？直接对话？
- 你是否编写过完整提示词？还是一句话讲述？

---


# 分享路线

1. 先把 CLI 的位置讲清楚
2. 再把 Agent 主循环讲清楚
3. 然后进入 function calling、MCP、skills、harness、RAG
4. 最后把这些部件重新串回一道真实题目的求解链路

这一讲的目标很具体：

- 听懂每个概念在系统中的层次
- 看清它们为何会连在一起
- 分享结束后能自己搭一个最小 CLI Agent 原型

---


# 为什么是 CLI

- CLI 是真实环境的统一操作表面
- 目录、脚本、容器、日志、调试器、网络工具都能接进同一条执行链
- 命令、参数、输入、输出、artifact 都容易记录，复现实验成本低
- 安全研究里很多关键动作天然发生在终端里

---


# CLI 里到底能接住什么


```bash
tree -L 2 ./challenge
sed -n '1,160p' ./README.md
docker compose up -d
curl -sS http://127.0.0.1:8080/
python ./scripts/route_map.py
checksec --file=./chall
gdb -q ./chall -ex 'start' -ex 'quit'
```

- 读题目说明
- 启动服务与环境
- 调脚本做摘要
- 访问本地站点
- 接静态分析和调试工具

---


# 前置知识：模型在工程里输出什么

- 普通文本
- 结构化 JSON
- 工具调用请求
- 错误恢复请求
- 最终答案与证据摘要

把模型放进系统后，真正需要关注的是：

- 当前上下文里有什么
- 系统暴露了哪些工具
- 外部环境现在处在什么状态
- 模型这一步的输出怎样进入执行链

---


# 单轮问答与多步执行的差别

单轮问答的结构很短：

- 用户提问
- 模型回答
- 当前轮次结束

多步执行的结构完全不同：

- 先决定下一步动作
- 再进入工具调用
- 等环境返回真实结果
- 再根据观察结果修正下一步

只要任务出现“先读附件，再跑命令，再看输出，再修正判断”，系统就已经进入 Agent 工作流。

---


# Agent 的最小定义

Agent 可以理解成：

> 围绕任务闭环组织模型、工具、状态与观察结果的执行系统

最小闭环里有五个部件：

- plan：当前轮次要做什么
- act：把动作落到工具或环境
- observe：读取真实结果
- memory：保存跨轮仍然有价值的事实和 artifact
- stop：判断任务何时可交付

---


# Agent 主循环


```python
task = load_task()
state = init_state(task)

for step in range(MAX_STEPS):
    context = build_context(task, state)
    decision = model.generate(context, tools=tool_schemas)

    if decision.type == "tool_call":
        observation = executor.run(decision.name, decision.arguments)
        state = update_state(state, decision, observation)
        save_trace(step, decision, observation)
        continue

    if decision.type == "final_answer":
        export_answer(decision.content, state)
        break
```

---


# 为什么攻防任务天然需要 Agent

- Web 题常常要先读说明，再起服务，再枚举路由，再看响应，再回查源码
- 逆向题常常要先看文件类型，再查保护，再扫字符串，再找关键函数，再下断点
- 日志研判常常要先定时间窗，再筛字段，再聚类，再回看上下游行为

这些任务的难点都来自一件事：

上一轮观察结果会直接改变下一轮动作。

---


# function calling 出现之前卡在哪里

- 模型可以写出“建议你执行某条命令”
- 系统却很难稳定知道：
- 调哪个工具
- 参数是什么
- 哪些字段必填
- 错误时怎样回填

自由文本一旦进入复杂工具链，稳定性会迅速下降。

---


# function calling 的核心作用

- 用 schema 描述工具名称、参数结构和约束
- 模型生成“调用意图 + 参数”
- 外部执行器完成真实执行
- 执行结果再回填给模型

这里的分工很清楚：

- 模型负责决定调用什么
- 执行器负责决定怎样执行
- 系统根据结果继续推进下一轮

---


# function calling 最小例子


```json
{
  "name": "read_file",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {"type": "string"},
      "max_lines": {"type": "integer"}
    },
    "required": ["path"]
  }
}
```


```json
{
  "name": "run_command",
  "parameters": {
    "type": "object",
    "properties": {
      "command": {"type": "string"},
      "timeout_sec": {"type": "integer"}
    },
    "required": ["command"]
  }
}
```

---


# 一次 function calling 的执行回路


```
用户问题
  ↓
模型读取工具 schema
  ↓
生成 tool_call(name, arguments)
  ↓
执行器运行工具
  ↓
返回 tool_result
  ↓
模型继续分析并决定下一步
```

这一层的关键在于“模型生成结构化调用意图，执行权限仍然在系统外层”。

---


# function calling 落地时最常见的摩擦

- 参数缺失：先校验 schema，再把错误字段回填给模型
- 参数格式错误：返回字段级报错
- 工具超时：返回超时标记和摘要输出
- 输出过长：摘要化，或导出 artifact 后回传路径
- 重复失败：提示模型换路线，减少无效重试

---


# MCP 在系统里解决什么问题

工具一少，手写 schema 很轻松。

工具一多，系统会立刻遇到三类问题：

- 接入方式碎片化
- 能力发现方式不统一
- 权限、审计和复用都很难整理

MCP 的作用就是把“工具接入”整理成协议层。

---


# MCP 的三个核心角色

- host：持有用户会话、模型和上层应用逻辑
- client：连接 MCP server，负责发现能力和转发调用
- server：对外暴露 tools、resources 和 prompts

放到 CLI Agent 里看：

- host 往往是本地代理程序
- client 是协议适配层
- server 连接文件系统、shell、知识库、代码仓库或题目环境

---


# MCP 的价值

- 工具、资源、提示模板都进入统一接口
- 模型可以先发现能力，再决定调用顺序
- 本地能力与外部数据源可以进入同一张能力地图
- 权限、认证、审计和可观测性更容易治理

---


# 一个贴近 CLI 的 MCP 配置


```yaml
[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/labs/web-lab"]

[mcp_servers.challenge_kb]
command = "python"
args = ["./servers/challenge_kb_server.py"]

[mcp_servers.challenge_kb.env]
KB_PATH = "/labs/kb"
KB_COLLECTION = "ctf-notes"
```

这类配置最适合拿来讲“系统怎样发现并接入能力”。

---


# skills 为什么重要

很多任务有稳定起手流程：

- Web 题初始侦察
- ELF 样本初步分析
- 日志时间线整理
- 流量关键线索提取

如果每次都从空白 prompt 开始，系统就会一轮轮重复组织同样的动作。

skills 的作用是把这类经验整理成可复用工作流单元。

---


# 一个 skill 的最小结构


```yaml
web-initial-recon/
├── SKILL.md
├── references/
│   ├── common-auth-chain.md
│   └── flask-routing-checklist.md
├── scripts/
│   ├── route_map.py
│   └── response_digest.py
└── assets/
    └── recon-report-template.md
```

- `SKILL.md`：触发条件、任务边界、执行步骤、输入输出约定、常见失败点
- `references/`：按需读取的说明材料
- `scripts/`：确定性强、重复率高的脚本
- `assets/`：模板和固定产物

---


# skill 示例：Web 初始侦察


```yaml
name: web-initial-recon
description: 针对 Web 实验题执行初始侦察

1. 读取 README、compose、依赖文件
2. 启动服务并记录端口与日志
3. 生成路由摘要
4. 访问首页、登录页、健康检查端点
5. 输出 recon-report.md
```

这一层的重点是：

- 把重复经验沉淀下来
- 让 Agent 在运行时复用方法
- 让上下文开销保持在可控范围内

---


# harness 的严格定义

在这次分享里，harness 定义为：

> 围绕某一类任务建立的执行与评测壳层，它负责题目输入、环境准备、工具暴露、运行约束、轨迹记录、结果判分与复现实验。

harness 让系统从“能跑”走向：

- 可测
- 可比
- 可复现

---


# harness 至少要包含什么

- 输入：题目描述、附件、基础 URL、标签
- 环境：工作目录、容器、依赖、本地服务
- 工具：允许的命令、MCP server、自定义函数
- 约束：最大步数、总时长、可写目录、网络范围
- 轨迹：每轮调用、输出摘要、artifact 路径
- 评测：成功条件、证据要求、导出格式、重放脚本

---


# 最小 harness 草图


```yaml
task_id: web-lab-ssti-01
input:
  prompt_file: problem.md
  attachments: [app.zip, docker-compose.yml]
environment:
  workspace: /labs/web-lab-ssti-01
tools:
  allowed_commands: [ls, sed, grep, curl, python, docker]
constraints:
  max_steps: 20
  wall_clock_minutes: 25
logging:
  trace_file: traces/run.jsonl
success:
  answer_pattern: "flag\\{[^\\n]+\\}"
```

---


# RAG 为什么会进入这条链

安全知识天然分散在很多地方：

- writeup
- 协议规范
- 源码
- 论文
- API 手册
- 日志样本

全部塞进上下文，相关片段反而更难被当前步骤抓住。

RAG 解决的是“当前轮次最需要哪几段材料”。

---


# RAG 的完整链条


```
原始资料
  ↓
切分
  ↓
建立索引
  ↓
检索候选
  ↓
重排
  ↓
拼接上下文
  ↓
返回引用
```

它负责补充外部知识，外部动作仍然交给工具层处理。

---


# 在攻防任务里，RAG 最适合补什么

- 历届题解和题型经验
- glibc 版本笔记
- 常见 Web 漏洞利用条件
- 工具使用手册
- 协议说明与日志字段说明

更适合写成 skill 的内容：

- 稳定、重复、流程明确的动作套路

更适合作为工具暴露的内容：

- 需要和外部系统实时交互的能力

---


# 现在把所有部件串起来


```
用户任务
  ↓
CLI 工作台
  ↓
Agent 主循环
  ├─ 用 skill 选起手流程
  ├─ 用 function calling 发起结构化调用
  ├─ 用 MCP 接 shell / 文件系统 / 知识库
  ├─ 用 RAG 补充局部知识
  └─ 在 harness 约束下持续运行
  ↓
答案 + 证据 + 可复放结果
```

---


# 端到端案例：一题 Web 实验题怎样推进

1. 用户提交题目说明、附件和基础 URL
2. harness 准备工作目录和容器环境
3. Agent 读取说明与目录树
4. `web-initial-recon` skill 进入当前上下文
5. 模型通过 function calling 调 `read_file`、`run_command`
6. MCP 接入文件系统、shell 与本地知识库
7. RAG 检索框架笔记和历史题解片段
8. Agent 更新计划并继续验证
9. harness 记录轨迹并校验成功条件
10. 系统导出答案、证据和 artifact

---


# 一小时分享怎样安排

| 环节 | 时间 |
| --- | --- |
| 开场与问题背景 | 5 分钟 |
| 前置知识 | 6 分钟 |
| Agent 基础 | 8 分钟 |
| CLI | 5 分钟 |
| function calling | 8 分钟 |
| MCP | 7 分钟 |
| skills | 5 分钟 |
| harness | 5 分钟 |
| RAG | 5 分钟 |
| 端到端案例 | 4 分钟 |
| 收束与提问 | 2 分钟 |

---


# 哪些地方适合现场演示

- CLI 一节：直接展示 `tree`、`sed`、`curl`
- function calling 一节：展示 schema、tool\_call、tool\_result
- MCP 一节：展示配置片段和能力发现
- 端到端案例：展示 artifact 输出目录和最终结果

更适合画图的地方：

- 整体架构关系
- MCP 角色关系
- RAG 检索流

---


# 初学者最适合先搭什么

先搭一个最小系统：

- 一个模型调用入口
- 一个 `read_file`
- 一个 `run_command`
- 一份状态文件
- 一条 10 到 20 步的主循环
- 一个 artifact 目录

只要它已经能读题目说明、扫目录、跑几条只读命令、输出简短报告，它就已经开始具备解题能力。

---


# 什么时候引入 MCP、skills、RAG、harness

- 工具来源开始多样化时，引入 MCP
- 某类任务的起手流程已经稳定时，把 prompt 升级成 skill
- 知识规模超过上下文容量、版本差异开始影响判断时，引入 RAG
- 开始重复跑题、做模型比较、做团队复核时，补齐 harness

系统扩展的顺序最好始终围绕一件事：

当前真实任务已经推进到了哪一步。

---


# 常见误解澄清

- Agent 不等于 prompt 拼接，它还包含状态、工具、观察和终止条件
- MCP 不等于插件，它讨论的是统一协议和能力治理
- RAG 不等于外挂知识库，它包含检索、重排、引用和时效控制
- harness 不等于测试脚本，它还负责运行约束、轨迹记录和结果导出

---


# 最小可行原型路线图

| 阶段 | 目标 |
| --- | --- |
| 第 1 周 | 跑通最小 Agent 主循环 |
| 第 2 周 | 写出第一个 skill |
| 第 3 周 | 接入 MCP 与本地知识库 |
| 第 4 周 | 补齐 harness 和结果导出 |
| 第 5 周 | 建立 RAG 索引并跑小规模题集 |

这条路线的重点不在“大而全”，而在每一周都保持系统可运行。

---


# 最后想留下的画面

终端里摆着题目目录、脚本、日志、容器与知识库。

Agent 在受控约束下持续：

- 读取现场
- 调用工具
- 记录证据
- 修正路线
- 导出答案与过程

这时我们讨论的焦点，已经转向“怎样把模型放进一套真正能做事的系统里”。

---


# 参考资料

- ReAct: Synergizing Reasoning and Acting in Language Models
- OpenAI Function Calling Guide
- Model Context Protocol Introduction / Specification
- OpenAI Academy Skills
- SWE-bench Harness Reference
- Inspect AI / Inspect Cyber
- Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- Anthropic Contextual Retrieval

分享结束后如果要继续深挖，优先从官方协议、官方文档和原始论文往下读。
