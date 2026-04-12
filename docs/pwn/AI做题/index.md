# AI做题

在 CLI 里把 AI 接进网络攻防：把 agent 的几层结构讲清楚

把大模型放进终端之后，工作重心会很快发生变化。聊天窗口里更看重语言生成，CLI 里更看重连续执行。题目目录、附件、日志、脚本、文档、容器、检索服务、会话状态，都会一起进入模型的工作链条。Anthropic 在讨论 agent 系统时，将预设路径的 workflow 与执行中动态决策的 agent 区分开来，同时给出一个很重要的判断：真正稳定的系统，往往建立在简单、可组合的结构上。这个判断放进终端环境尤其贴切，因为命令行天生就是一个由文件、命令、资源和过程构成的可组合系统。([Anthropic](https://www.anthropic.com/research/building-effective-agents?utm_source=chatgpt.com))

这篇文章沿着一条连续逻辑往前展开。我们平时常听到 function calling、MCP、skills、harness、RAG 这几个词。放进 CLI 场景里看，它们刚好位于同一条链上。function calling 负责把模型的调用意图写成结构化请求；MCP 负责把外部工具、数据和工作流接成统一协议；skills 负责把已经沉淀的做题经验封装为可复用能力；harness 负责长任务中的状态、权限、续接和产物管理；RAG 负责把外部知识在合适时机送进当前推理窗口。OpenAI 在 Responses API 的迁移说明里，已经把内置工具、多轮状态和 remote MCP 放进统一接口，这一变化本身就说明，现代 agent 系统正在从单轮问答转向持续执行。([OpenAI开发者](https://developers.openai.com/api/docs/guides/migrate-to-responses/?utm_source=chatgpt.com))


## 一、function calling：先把“调用意图”放进结构化通道

OpenAI 的 function calling 文档给出了很清楚的定义：开发者用 JSON Schema 描述函数的名字、参数和约束，模型在需要时生成一份结构化调用请求，宿主程序收到以后执行真实函数，再把结果返回给模型继续推理；在 strict mode 下，参数会更稳定地贴合 schema。沿着这个定义往下看，function calling 带来的核心变化，是系统内部多出了一条结构化通道。模型从此可以直接表达“调用哪个工具、传哪些参数、等待什么结果”。([OpenAI开发者](https://developers.openai.com/api/docs/assistants/tools/function-calling/?utm_source=chatgpt.com))

终端里的安全分析很适合从这个入口开始理解。设想一个课程实验目录，里面放着 `chall`、`libc.so.6` 和一份说明文档。模型读取目录后，第一步通常会进入信息采样阶段。这个阶段更适合让模型发起一次明确调用，例如 `run_checksec(path="./chall")`。宿主程序实际执行 `checksec`，随后把结果整理成 `canary=true, nx=true, pie=false, relro=partial` 这样的结构，再交还给模型。模型读取这些字段后，才会继续决定是否调用 `strings_summary`、`list_imports`、`summarize_decompilation`。这时可以清楚看到分工：模型负责判断顺序，程序负责真实执行，结构化返回值负责把前一步结果稳定传给后一步推理。

再看一个日志分析场景，function calling 的作用会更直观。假设终端里有一份 `auth.log`，你给模型接入一个日志过滤工具：


```

{


"name"
:

"filter_auth_logs"
,


"description"
:

"筛选指定时间段的认证失败记录"
,


"parameters"
:

{


"type"
:

"object"
,


"properties"
:

{


"path"
:

{
"type"
:

"string"
},


"start_time"
:

{
"type"
:

"string"
},


"end_time"
:

{
"type"
:

"string"
},


"keyword"
:

{
"type"
:

"string"
}


},


"required"
:

[
"path"
,

"start_time"
,

"end_time"
],


"additionalProperties"
:

false


},


"strict"
:

true

}

```

模型随后可以直接生成一份调用请求，宿主程序根据参数完成筛选，再把结果作为结构化记录返回。这样一来，时间范围、目标文件和关键词都会进入稳定的数据流。后续若要做时间线整理、异常聚类或字段解释，模型读取的是结构化结果，后续推理可以直接建立在这些字段上。对 CLI 而言，这种稳定的数据流十分关键，因为终端任务常常由多轮工具调用串起来，前一步输出的形状会直接影响后续推理质量。

这里有一个工程上很重要的认识：function calling 负责表达调用意图，真实执行仍然掌握在宿主程序手里。目录边界、参数校验、动作审计、人工确认，全部属于外层系统的职责。调用意图与执行权限位于两层不同结构中，理解这一点以后，后面的 MCP 和 harness 才容易摆正位置。


## 二、MCP：把零散接线变成统一接入层

当工具数量很少时，单独写几个 function schema 已经够用。工具一旦增多，维护成本会上升得很快。题目目录需要读取，知识库需要检索，本地脚本需要调用，容器命令需要执行，远端服务需要连接，每个 CLI 再各自设计一套接法，生态很快就会碎裂。MCP 的意义就在这里。

MCP 官方规范把服务器暴露的能力分成 resources、prompts、tools 三类。resources 提供上下文与数据，prompts 提供可参数化的工作流模板，tools 提供可执行动作。客户端通过统一协议发现、读取和调用这些能力。OpenAI 的 Apps SDK 文档也把 MCP server 放在核心位置，说明应用接入 ChatGPT 之类的 agent 环境时，MCP 已经承担起能力边界定义和接入组织的角色。([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-11-25?utm_source=chatgpt.com))

把这套结构放进终端现场，就会立刻变得具体。假设你为一个逆向题环境准备了两组外部能力。第一组围绕题目目录本身，提供 `resource://challenge/readme`、`resource://challenge/tree`、`tool://challenge/run_checksec`、`tool://challenge/list_symbols`。第二组围绕知识库，提供 `tool://kb.search` 和若干只读资源，例如 glibc 版本差异说明、调用约定速查、常见保护机制笔记。此时模型先枚举可用 resources 和 tools，再按当前任务去读取或调用。目录信息、知识信息、执行动作，会在统一协议下被组织起来。这样做带来的直接收益，是边界清晰：哪些能力只读，哪些能力可执行，哪些能力来自本地目录，哪些能力来自远端服务，都会在接入层直接呈现。([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-11-25?utm_source=chatgpt.com))

这时再回头看 function calling 与 MCP 的关系，就能看到清晰分层。function calling 描述单次调用怎样表达，MCP 组织一批外部能力怎样被发现、枚举和治理。OpenAI 将 remote MCP 直接并入 Responses API 工具体系，也说明这两层已经在现代 agent 结构里开始对齐：模型面对的对象，已经从单个孤立函数，扩展为一个动态变化的能力集合。([OpenAI开发者](https://developers.openai.com/api/docs/guides/migrate-to-responses/?utm_source=chatgpt.com))

继续用例子往前走。设想当前分析任务来自一套 Web 实验附件。模型通过 `resource://challenge/tree` 发现目录中存在 `routes/`、`middleware/` 和 `config/`。它随后调用 `tool://challenge/list_routes` 整理路由，再调用 `tool://kb.search` 搜索该框架的中间件认证链条。这个过程里，模型关注的是统一协议下的“发现能力—读取资源—发起调用—接收结果”这一整套动作，服务语言和后端实现细节可以留在接入层处理。终端里的复杂度因此被压缩到了接入层，模型侧的推理会更顺。


## 三、skills：把经验写进目录，让 agent 在运行中复现方法

进入实际做题阶段后，会遇到另一个问题：大量任务都有稳定起手流程。ELF 初勘、日志时间线整理、Web 附件目录梳理、取证样本特征提取，这些动作每次都从头组织，成本会很高。skills 正好承接这一层。

OpenAI 的技能文档和 Cookbook 将 skill 描述为一个可复用文件包，入口是 `SKILL.md`。这个目录里可以放说明、脚本和资源文件。系统先向模型暴露技能的名称、描述和路径，模型判断某个 skill 与当前任务相关时，再读取完整说明。这样做的好处很直接：经验可以复用，上下文占用仍然可控，因为系统采用的是先看元数据、再按需加载正文的路径。([OpenAI开发者](https://developers.openai.com/cookbook/examples/skills_in_api/?utm_source=chatgpt.com))

网络攻防题里最适合封装成 skill 的内容，是“稳定套路加现场判断”。举一个 ELF 题的例子。很多题目的初勘流程都包含几件事：识别文件类型，检查保护，提取字符串和导入导出符号，定位入口点附近逻辑，整理一份首轮分析记录。真正依赖现场语境的是，哪条线索值得继续深挖；更适合脚本和固定说明承接的，是那组重复性很高的起手步骤。于是一个 `pwn-elf-firstlook` skill 就会很自然地长出来：


```

pwn-elf-firstlook/
├── SKILL.md
├── scripts/
│   ├── run_checksec.sh
│   ├── strings_summary.py
│   ├── imports_exports.py
│   └── decomp_brief.py
└── references/
    ├── elf_mitigations.md
    └── calling_conventions.md

```

这里的关键文件始终是 `SKILL.md`。一份写得好的 `SKILL.md` 通常会把四件事交代清楚：什么条件下触发；进入后按什么顺序工作；每一步调用哪些脚本或资源；最终要产出什么结构化结果。比如你可以写明：当目录中存在 ELF 且出现本地 `libc.so.6` 时，优先触发本 skill；依次运行保护检查、符号摘要、入口点附近反编译摘要；最终生成 `firstlook.md`，其中要写入保护情况、可疑函数、下一步待验证假设。这样一来，经验就从个人头脑里的操作习惯，转成了 agent 在运行时可以直接调度的工作结构。([OpenAI开发者](https://developers.openai.com/cookbook/examples/skills_in_api/?utm_source=chatgpt.com))

换一个场景，skills 的作用同样明显。设想你在做一份认证日志分析题。一个 `forensics-auth-timeline` skill 可以规定：先抽取失败登录记录，再按时间排序，再聚合来源 IP 与用户名，再输出一个 `timeline.md` 和一份 `suspicious_ips.json`。模型在这个流程里需要做的，是根据现场日志样式判断哪几个字段最重要，是否继续追踪某个来源地址。脚本承担的是字段提取、排序和聚合这类确定性动作。这样分工以后，教学中的“方法”就会从一段抽象讲述，落成一个可以在终端里真实运行的能力包。


## 四、harness：让长任务具备连续性、可审计性和治理边界

有了工具、协议和 skill 之后，系统仍然可能在长任务里变得很脆。根源通常不在模型本身，而在 harness。这个词在工程里常用来指外层运行骨架：会话怎样起步，状态怎样保存，历史怎样压缩，失败怎样恢复，下一轮怎样接着上一轮推进，哪些动作可以自动完成，哪些动作需要人工点头。

Anthropic 在关于 long-running agents 的文章里专门讨论了这个问题。复杂任务会跨越多个上下文窗口，后一轮会话很难直接继承前一轮全部细节，因此系统需要专门的初始化、增量推进和 artifact 交接机制。OpenAI 2026 年关于 long-running agents 的文章，也把 shell、skills 和 compaction 放到同一条工程链上，说明长任务的可靠性依赖外层系统持续维护上下文与过程。([Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents?utm_source=chatgpt.com))

最适合理解 harness 的方式，依然是沿着一个连续任务走一遍。设想你把一组 Web 实验附件交给 agent。第一轮，agent 读取目录树，识别项目类型，写出初始计划。第二轮，它提取路由、配置项和依赖清单，发现认证逻辑落在中间件里。第三轮，它调用知识库检索相关框架的认证链条说明。第四轮，它修正先前假设，更新下一步计划。这个过程中，真正需要跨轮保留下来的内容，是计划、证据、命令记录、关键文件路径、已确认事实、待验证假设。harness 的任务，就是把这些内容沉淀成 artifact，让下一轮能直接接上。([Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents?utm_source=chatgpt.com))

artifact 可以长成很多形态。常见做法是每轮结束后都落一份 `analysis_state.json`，里面写入当前任务摘要、已确认事实、待验证假设、下轮优先动作、最近执行的命令和关键文件引用；再配一份 `notes.md` 记录人类可读的推理过程。这样一来，模型下一轮启动时可以先读取状态文件，再进入后续步骤；人类中途接手时，也能快速看清当前进度与证据链。长任务的连续性就从聊天历史里抽出来，进入显式产物层。

终端场景里，harness 还承担治理职责。只读命令、写文件动作、网络访问、工作目录范围、人工确认点，都会在这一层划边界。agent 进入 shell 以后，系统后果已经从“生成一段文本”扩展为“可能改动环境”。因此，命令白名单、目录沙箱、审计日志和人工确认机制，都会随着 harness 一起进入设计范围。这一层设计清楚以后，agent 的可用性和可控性才会同步上升。


## 五、RAG：把当前步骤真正需要的材料送进当前窗口

终端里的任务总会碰到模型外部知识这一层。课程讲义、协议标准、框架文档、历史 writeup、日志格式表、内部分析笔记，真正能推动题目继续往前走的知识，大多在模型参数外部。Lewis 等人的 RAG 论文提出的核心思路，是将参数化记忆与显式的非参数记忆结合起来：模型在生成时从外部索引检索相关片段，再基于这些片段生成结果。论文同时强调了两个工程价值，一个是知识更新能力，一个是证据来源可追溯。([arXiv](https://arxiv.org/abs/2005.11401?utm_source=chatgpt.com))

这套思路放进 CLI 以后，含义会更具体。目标是在某一轮分析中，只把当前最相关的那几段材料送进来。OpenAI 的 File Search 文档与 Responses API 相关说明也沿着这个方向展开：系统会处理和检索文件内容，把语义相关片段返回给模型，当前窗口因此能保持更高的信息密度。([OpenAI开发者](https://developers.openai.com/api/docs/assistants/tools/file-search/?utm_source=chatgpt.com))

还是用一个取证题的例子来看。终端目录里有一批系统日志，你同时准备了两份资料，一份是“Linux 认证日志字段说明”，另一份是“时间线整理方法”。前几轮工具调用已经定位到某个时间窗口内的异常失败登录。接下来，模型最需要的是与 `auth.log` 相关的字段解释、时间戳解析和失败认证记录含义。RAG 在这个节点上的作用，就是把这几段资料精准送进当前窗口，让模型能够立刻解释字段语义、确定下一步聚合维度，并把结果写进时间线。

RAG 的工程效果，经常取决于检索层的设计。切分粒度会影响召回质量，块太大时噪声会上升，块太小时关键条件会被拆散。检索策略同样重要，函数名、错误码、协议字段、特定版本号这类信息，往往需要混合检索来提升命中率。Anthropic 在 Contextual Retrieval 的文章里提出，用 contextual embeddings 与 contextual BM25 一起改进检索阶段；他们报告说，这种方法能将失败检索数量降低 49%，配合 reranking 后可降低 67%。这个结果说明，RAG 的瓶颈常常位于“片段怎样组织与召回”这一层。([Anthropic](https://www.anthropic.com/news/contextual-retrieval?utm_source=chatgpt.com))

换到做题视角，可以把它理解得很朴素：安全分析经常会遇到“这条线索像某个知识点，细节又带着版本差异或上下文偏移”的情况。此时，最有价值的材料通常是贴着现场证据的几段说明。RAG 做的事情，就是让这几段材料在合适时间进入合适位置。


## 六、把五层接起来，CLI 里的 agent 才真正开始工作

沿着前面的五层继续往前收束，一条完整链路就会出现。agent 先读取题目目录和基础资源，识别任务类型；随后根据环境和题型选择合适的 skill；skill 中定义的步骤引导它发起若干 function calls，执行本地脚本或工具；当任务需要访问统一接入的外部能力时，它通过 MCP 找到对应的 resources 与 tools；当当前推理缺少背景知识时，它通过 RAG 检索最相关的片段；整个过程中，harness 负责状态保存、权限治理、历史压缩和阶段产物管理。这样的一套系统，才会在终端里表现出真正的持续执行能力。([OpenAI开发者](https://developers.openai.com/api/docs/guides/migrate-to-responses/?utm_source=chatgpt.com))

从工程角度看，很多 AI + CLI 工作流到后面都会进入“外层系统设计”阶段，原因就在这里。稳定体验依赖的是整条结构链的配合：调用意图要结构化，工具能力要统一接入，经验要能封装复用，长任务要有状态与治理，知识要按需送达。2025 到 2026 年的官方文档越来越多地讨论 tools、MCP、skills、shell、compaction 和 long-running agents，本身就是这一趋势的直接反映。([OpenAI开发者](https://developers.openai.com/blog/skills-shell-tips/?utm_source=chatgpt.com))


## 七、放进一小时分享时，内容怎样组织会更顺

拿去做分享时，可以沿着终端里的真实困难开场：题目附件很多、命令调用很多、过程跨度很长、知识分散在外部文档里。接着进入 function calling，把结构化调用这一层讲稳；再讲 MCP，让听众看到统一协议怎样让工具和资源接入变得有序；中段讲 skills，把经验资产化这一层展开；后半段接上 harness 和 RAG，让大家看到长任务连续性与外部知识供给怎样共同支撑 agent。这样组织下来，每个名词都会落在具体位置上，听众脑中会形成一张完整结构图。([Anthropic](https://www.anthropic.com/research/building-effective-agents?utm_source=chatgpt.com))


## 参考文章

1. OpenAI, *Migrate to the Responses API*. ([OpenAI开发者](https://developers.openai.com/api/docs/guides/migrate-to-responses/?utm_source=chatgpt.com))
2. OpenAI, *Building MCP servers for ChatGPT Apps and API integrations*. ([OpenAI开发者](https://developers.openai.com/api/docs/mcp/?utm_source=chatgpt.com))
3. Model Context Protocol, *Specification* 与 *Introduction*. ([Model Context Protocol](https://modelcontextprotocol.io/specification/2025-11-25?utm_source=chatgpt.com))
4. OpenAI, *Using skills to accelerate OSS maintenance*. ([OpenAI开发者](https://developers.openai.com/blog/skills-agents-sdk/?utm_source=chatgpt.com))
5. OpenAI Cookbook, *Skills in OpenAI API*. ([OpenAI开发者](https://developers.openai.com/cookbook/examples/skills_in_api/?utm_source=chatgpt.com))
6. OpenAI, *Shell + Skills + Compaction: Tips for long-running agents that do real work*. ([OpenAI开发者](https://developers.openai.com/blog/skills-shell-tips/?utm_source=chatgpt.com))
7. Anthropic, *Building Effective Agents*. ([Anthropic](https://www.anthropic.com/research/building-effective-agents?utm_source=chatgpt.com))
8. Anthropic, *Effective harnesses for long-running agents*. ([Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents?utm_source=chatgpt.com))
9. Anthropic, *Harness design for long-running application development*. ([Anthropic](https://www.anthropic.com/engineering/harness-design-long-running-apps?utm_source=chatgpt.com))
10. Patrick Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. ([arXiv](https://arxiv.org/abs/2005.11401?utm_source=chatgpt.com))
11. Anthropic, *Introducing Contextual Retrieval*. ([Anthropic](https://www.anthropic.com/news/contextual-retrieval?utm_source=chatgpt.com))
12. OpenAI, *Assistants File Search* 与相关 Retrieval 文档入口. ([OpenAI开发者](https://developers.openai.com/api/docs/assistants/tools/file-search/?utm_source=chatgpt.com))

下一步最合适的是把这篇正文继续改成“适合讲一小时的演讲稿版”，把每一节拆成口头表达、现场 demo、命令展示和页间过渡。
