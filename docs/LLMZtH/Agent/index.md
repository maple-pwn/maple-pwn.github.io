# Agent相关知识

!!!note

    本章内容主要来自[小林coding](https://xiaolinnote.com/ai/agent/agent_info.html)

## Agent是什么

==关于模型==

模型本质上是一个问答机器，或者说是一个抽象函数，会对你的输入 $x$ 进行一系列加工后生成输出 $y$，即 $y = f(x)$ 中，$f(\cdot)$ 就是模型，所以它其实是一个只会答题的东西，你问一句它答一句，你让它先搜索再回答，它就不会了。总而言之，单模型存在以下问题：

- 知识冻结：模型的训练数据有截止日期，它没有任何途径获取实时信息
- 工具缺乏：它不可以行动，它只能告诉你怎么做，而不是去做
- 记忆断连：由于是一个单函数模型，是不包括过往文本的。每次调用之间是完全失忆的

==Agent==

Agent有核心的运作闭环：**感知->规划->行动->再感知**。有以下三个重要功能

**工具调用（Tool Use）**：直接解决单模型的所有问题。Tool Use 不是模型自己执行，而是模型输出该调用什么，怎么调用，让代码去执行，结果再反馈给模型，这里模型只是大脑

> 假设给Agent配了两个工具：`查天气`、`发邮件`，大致如下
>
> ```python
> tools = [
>     {
>         "name": "get_weather",
>         "description": "获取指定城市的当前天气",
>         "parameters": {
>             "type": "object",
>             "properties": {
>                 "city": {"type": "string", "description": "城市名称"}
>             },
>             "required": ["city"]
>         }
>     },
>     {
>         "name": "send_email",
>         "description": "发送邮件给指定收件人",
>         "parameters": {
>             "type": "object",
>             "properties": {
>                 "to": {"type": "string"},
>                 "subject": {"type": "string"},
>                 "body": {"type": "string"}
>             },
>             "required": ["to", "subject", "body"]
>         }
>     }
> ]
> ```
> 
> 这段代码是交付给模型的说明书，让模型按照标准生成内容，输入到代码中

**记忆机制**：Agent 系统通常会设计短期记忆和长期记忆两层。

- 短期记忆就是当前任务执行过程中的中间状态，比如第一步搜索到了什么，第二步计算结果是多少，这些都存在上下文里，保证 Agent 不会做到一半忘了前面发生了什么。
- 长期记忆则是跨任务的，比如用户的偏好、历史操作记录，通常用向量数据库来存储，需要的时候做语义检索拿回来

**多步推理和自我纠错**：Agent 区别于简单自动化脚本的关键。Agent 在执行过程中如果某一步失败，它不会直接崩掉，而是能感知到失败，分析原因，换一种方式重试。比如用关键词 A 搜索没找到有用信息，它会自动换关键词 B 再搜一次；调用某个 API 报错了，它会看报错信息然后调整参数重新调用。

==MCP：模型上下文协议 & A2A：Agent 间通信协议==

在没有 MCP 之前，每个 Agent 框架接每个工具都要写一套适配代码，假设有 M 个 Agent 框架和 N 个工具，就需要 M x N 套适配逻辑，工程成本非常高

MCP 的架构分三层：

- 最外层是 Host：用户直接交互的 AI 应用，例如 Claude CLI、Codex
- 中间是 Client：负责和 MCP Server 建立连接、管理通信
- 最里层是 Server：真正暴露工具能力的服务



A2A 的核心设计是 Agent Card，每个 Agent 都有一张结构化的描述信息，里面写明它能够完成的任务、当前状态、所需输入等信息。其他 Agent 读取这张 Card，就可以判断如何与其协作、如何拆分任务并进行调用

---

## Agent的基本架构

Agent的基本架构有四个核心组件：LLM、工具、记忆、规划模块

- **LLM**是系统的决策层，负责理解任务和做决策
- **工具** 让Agent能够和外界世界交互
- **记忆** 让Agent在任务执行过程中保持状态
- **规划模块** 将复杂目标拆解为可执行的步骤

LLM和工具部分已经介绍过/不用介绍，这边再详细记录一下记忆部分

==记忆系统==

- 最基础的是短期记忆，也就是当前任务过程中放在 context window 里的上下文。它保存每一步的中间状态，比如搜索结果、工具返回值和当前判断，让 Agent 能接着前面的内容继续执行，但容量有限，任务结束后通常就清掉了。
- 再往上是长期记忆，通常用 embedding 加向量数据库实现。重要信息先编码存起来，后面遇到相关任务时，再通过语义检索取回放进上下文里。长期记忆主要分三类：
    - 语义记忆存稳定事实
    - 情景记忆存具体经历
    - 程序性记忆存处理流程。

==规划模块==

规划模块的底层依赖的是LLM的推理能力，有一些方法提升模型的技术手段

- 最基础的方法是CoT(思维链)，让模型把思考的过程写出来；
- 还有一种方法是ToT(思维树)，在每个推理节点上展开多个可能的分支，评估每个分支的质量，选出最好的那条再往前

有了推理能力打底，实际运行中有这些主流模式：

- 先规划后执行：Plan-and-Excute模式，先让LLM输出一个完整的步骤列表，然后按顺序逐步执行
- 边规划边执行：ReAct模式，每走一步就根据当前结果重新思考下一步该做什么

下面是一个伪代码

```python
def agent_run(user_goal: str):
    plan = llm.plan(user_goal)
    
    memory = []
    
    for step in plan:
        action = llm.decide(
            step = step,
            history = memory,
            long_term = vector_db.search(step)	# 从长期记忆里找到相关历史
        )
        
        if action.type == "tool_call":
            result = tools.execute(action.tool_name, action.args)
            memory.append({"step": step, "result": result})
            
        elif action.type == "final_answer":
            return action.content
```

## Workflow、Agent、Tools的概念和区别

- Tools是最小能力单元，是封装好的可调用函数，只负责执行，没有任何决策能力
- Agent是一个完整的决策系统，内部用LLM作为中枢，自行判断何时调用Tools、要不要继续、什么时候继续，是一个主动的对象
- Workflow是更上层的编排框架，把Agent、LLM、Tools组织成一条确定性流程

> Tools的例子
>
> ```python
> tools = [
>     {
>         "name": "web_search",
>         "description": "在互联网上搜索信息，适合查询实时数据或不确定的知识",
>         "parameters": {
>             "type": "object",
>             "properties": {
>                 "query": {"type": "string", "description": "搜索关键词，越具体越好"}
>             },
>             "required": ["query"]
>         }
>     },
>     {
>         "name": "send_email",
>         "description": "向指定邮箱发送一封邮件",
>         "parameters": {
>             "type": "object",
>             "properties": {
>                 "to":      {"type": "string", "description": "收件人邮箱地址"},
>                 "subject": {"type": "string", "description": "邮件主题"},
>                 "body":    {"type": "string", "description": "邮件正文内容"}
>             },
>             "required": ["to", "subject", "body"]
>         }
>     }
> ]
> 
> def execute_web_search(query: str) -> str:
>     # 这里才是真正发出 HTTP 请求去搜索的代码
>     ...
> 
> def execute_send_email(to: str, subject: str, body: str) -> str:
>     # 这里才是真正调用邮件 API 发送邮件的代码
>     ...
> ```

> Agent的例子
>
> ```python
> import anthropic
> 
> client = anthropic.Anthropic()
> 
> def run_agent(user_goal: str):
>     # 把用户目标放进对话历史，Agent 的所有思考和行动都在这个 messages 里积累
>     messages = [{"role": "user", "content": user_goal}]
> 
>     # 注意：开发者根本不知道这个循环会跑几次，完全由 LLM 自己决定
>     while True:
>         # 每一轮，LLM 看到当前的完整对话历史，自己判断下一步该做什么
>         response = client.messages.create(
>             model="claude-opus-4-6",
>             max_tokens=1024,
>             tools=tools,      # 把「工具说明书」传给 LLM，让它知道自己有哪些能力
>             messages=messages
>         )
> 
>         # LLM 告诉我们「任务完成了」，把最终答案返回出去，循环结束
>         if response.stop_reason == "end_turn":
>             return response.content[0].text
> 
>         # LLM 认为还需要调工具，我们就真正去执行它指定的工具
>         # 注意：LLM 只是「告诉我们调哪个工具、传什么参数」，真正执行的是我们的代码
>         tool_use = next(b for b in response.content if b.type == "tool_use")
>         tool_result = execute_tool(tool_use.name, tool_use.input)
> 
>         # 把工具的执行结果塞回对话历史，LLM 下一轮能看到这个结果，再接着决策
>         messages.append({"role": "assistant", "content": response.content})
>         messages.append({
>             "role": "user",
>             "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": tool_result}]
>         })
>         # 回到循环顶部，LLM 再看一遍现在的状态，做下一步决策
> ```

> Workflow的例子
>
> ```python
> def run_customer_service_workflow(user_query: str) -> str:
>     # ---- 第一步：意图识别 ----
>     # 这里把 LLM 当成一个分类器来用，它只负责判断这个问题属于哪个类别
>     # 「下一步去哪」这个决策是下面的 if/elif 来做的，不是 LLM 自己决定的
>     intent = classify_intent_with_llm(user_query)  # 返回 "product" / "refund" / "other"
> 
>     # ---- 第二步：根据意图走不同分支 ----
>     # 注意：这个分支判断是开发者写的 Python 代码，不是 LLM 的决策
>     if intent == "product":
>         # 产品问题：去知识库检索，再生成回答
>         docs = search_knowledge_base(user_query)    # 直接调 Tool，固定的检索步骤
>         answer = generate_answer_with_llm(user_query, docs)  # LLM 作为节点生成回答
>         return answer
> 
>     elif intent == "refund":
>         # 退款问题：查订单系统，再走审核流程
>         order_info = query_order_system(user_query)  # 调 Tool 查订单
>         if order_info["eligible"]:
>             process_refund(order_info["order_id"])   # 调 Tool 处理退款
>             return "退款已受理，预计 3 个工作日到账"
>         else:
>             return "很抱歉，该订单不满足退款条件"
> 
>     else:
>         # 其他问题：转人工
>         escalate_to_human_agent(user_query)
>         return "已为您转接人工客服，请稍候"
> ```
> 
> LLM在这里面出现了两次，一次是做意图分类，一次是生成回答，只是一个节点罢了，**接下来去哪** 这件事由if/elif决定
> 

==完整编排方式==

纯Agent过于自由，容易失控；纯Workflow过于死板，没法列举所有情况

所以常见的是 **Agentic Workflow**：用Workflow固定主流程的骨架，在需要灵活判断的节点嵌入Agent，其余固定节点直接用LLM或Tools

A社总结了一些常见的Workflow编排模式，如下：

- Prompt Chaining(提示链)：把一个大任务拆成多个小步骤，前一步的输出作为后一步的输入
- Routing(路由)：先用LLM做分类判断，然后根据分类结果把请求分发到不同的处理分支
- Parallelization（并行化）：把可以同时进行的子任务并行执行，最后汇总结果
- Orchestrator-Workers（编排者-工人）：一个中央编排者负责分配任务，多个Worker各自完成子任务
- Evaluator-Optimizer（评估者-优化者）：一个LLM负责生成输出，另一个LLM负责评估这个输出的质量，反复迭代

## 其他Agent设计范式

回顾一下Agent和Workflow的区别

```python
# Workflow 风格：流程固定，每步都是确定的，LLM 只是工具
def workflow_answer_question(user_query: str):
    # 第一步：固定做向量检索
    docs = vector_db.search(user_query, top_k=5)
    # 第二步：固定做 rerank（重排序，筛选最相关的结果）
    reranked = reranker.rank(user_query, docs)
    # 第三步：固定喂给 LLM 生成答案
    answer = llm.generate(user_query, context=reranked)
    return answer

# Agent 风格：流程不固定，LLM 自己在运行时动态决定每一步
def agent_answer_question(user_query: str):
    while True:
        # LLM 自己决定：要搜索？要计算？还是直接回答？
        action = llm.decide(user_query, history=memory)
        if action.type == "search":
            result = vector_db.search(action.query)
            memory.append(result)
        elif action.type == "calculate":
            result = calculator.run(action.expr)
            memory.append(result)
        elif action.type == "final_answer":
            return action.content
```

==Agent三种设计范式==

- ReAct（Reasoning+Acting）：把推理和行动交替进行，其每一轮循环由三个步骤组成
    - 形成完整的Thought -> Action -> Observation 循环
    - Thought：LLM把当前的情况分析一遍，把推理过程写出来
    - Action：LLM根据思考的结论决定调用哪个工具、传什么参数
    - Observation：工具结果反馈给LLM，它读取结果继续Thought
    - 容易忘记最初的目标，或者反复在工具之间打转
- Plan-and-Execute：针对ReAct的短板，由LLM做规划，输出一个完整的步骤列表，然后由另一角色逐步执行
    - 现在已经存在动态重规划，也就是每执行完一步都会把结果反馈给规划器，规划期判断当前执行结果和预期一致与否，是否继续沿用后续计划
    - 可以在保持全局视野的情况下不会过于死板，但是会增加延迟和成本
- Reflection（反思）：在前两个范式上加上一层质量保障。它的做法是在 Agent 完成一步或者完成整个任务之后，再让一个评估者来判断结果如何
    - Reflection有一个变体为Reflexion，它在反馈结果优劣之余，还会加入本次失败的原因和改进建议，并作为下次输入。但是token消耗和延迟会增加

## Agent推理模式？ReAct具体实现方式？

- CoT是让LLM先把推理过程写出来再给答案
- ReAct是在CoT基础上加入了行动，让LLM交替输出思考和工具调用，每次行动后根据结果继续思考

RaAct模式中是通过prompt格式来约束LLM的输出结构，这个循环是由代码驱动。LLM每次只做一件事：根据当前的历史，输出下一步的Thought加上Action。代码负责检测输出，判断是否有Final Answer

> 典型的ReAct提示词如下：
>
> ```text
> 你是一个 AI 助手，可以使用以下工具：
> - search(query): 搜索互联网获取最新信息
> - calculator(expr): 计算数学表达式
> 
> 回答时请严格按照以下格式：
> Thought: 你的思考过程（分析当前情况，决定下一步）
> Action: 工具名称
> Action Input: 工具的输入参数
> Observation: （此行由系统填入工具返回的结果，你不用写）
> ... 以上可以重复多轮 ...
> Final Answer: 当你确定可以回答时，在这里给出最终答案
> 
> 问题：2024 年苹果公司的市值是多少？和谷歌相比谁更高？
> ```
>
> 代码如下：
>
> ```python
> def react_agent(question: str, tools: dict, max_steps: int = 10):
>     # 把 ReAct 格式约束和问题拼在一起，作为初始 prompt
>     prompt = build_react_prompt(question, tools)
>     # 用来存每一轮的对话历史，每次调 LLM 都把完整历史带上
>     history = []
> 
>     for _ in range(max_steps):
>         # 调 LLM，让它输出下一步的 Thought + Action
>         # 注意：每次调用都把完整历史拼进去，LLM 才知道之前做了什么
>         response = llm.generate(prompt + "\n".join(history))
> 
>         if "Final Answer:" in response:
>             # LLM 输出了 Final Answer，说明它判断任务完成了
>             return response.split("Final Answer:")[-1].strip()
> 
>         # 从 LLM 输出里解析出 Action 名称和 Action Input
>         # 例如：Action: search，Action Input: 苹果公司市值 -> ("search", "苹果公司市值")
>         action, action_input = parse_action(response)
> 
>         # 执行对应的工具，拿到真实结果
>         if action in tools:
>             observation = tools[action](action_input)
>         else:
>             # 如果 LLM 填了一个不存在的工具名，给它一个错误反馈
>             observation = f"工具 {action} 不存在，请选择可用工具"
> 
>         # 把这一轮的 LLM 输出（含 Thought+Action）和 Observation 都追加进历史
>         # 下次调 LLM 时这些内容会成为它的「记忆」
>         history.append(response)
>         history.append(f"Observation: {observation}")
> 
>     return "超过最大步数，任务未完成"
> ```

这是古早版本的ReAct的实现，从GPT4以后，原生支持Function Calling/Tool Use，可以直接输出结构化的json工具调用，不必解析文本格式。

==ReAct存在的问题==

1. 循环漂移：容易在多次的循环迭代中忘记自己要做什么，原始目标被遗忘
2. 错误传播：如果中间有一步出现问题，则后面会将错误传递下去

## 复杂任务如何拆分？

需要考虑 `拆分粒度`、`并行优化`、`依赖分析` 这三个部分

- **静态拆分**：提前把步骤写死
- **动态拆分**：让LLM自己根据目标规划步骤

一个好的拆分结果应该满足这些条件：

- 完备性：所有步骤加在一起可以覆盖原始任务的全部要求
- 独立性：每个步骤的职责边界清晰
- 可验证性：每个步骤执行完以后，是否有一个简单标准判断它做对了没有

## Agent 的记忆机制

记忆机制分为四层：

- 感知记忆：当前输入的原始内容
- 短期记忆：context windows里的对话历史
- 长期记忆：存在外部数据库、预计检索召回
- 实体记忆：结构化提取的关键事实

设计时考虑三个问题：`存什么`、`怎么存`、`什么时候取出来用`

==长期记忆==

长期记忆细分为三类：

- 情节记忆：存储具体事件经历。例如“上周二用户问我xxx怎么做，最后用xxx解决了”
- 语义记忆：多次经历中提炼出来的通用知识和规律。例如“在做xxx的时候，可以xxx解决”
- 程序记忆：存的是怎么做某件事的操作流程，是一套可以直接复用的操作SOP

==存什么==

- 用户偏好和习惯：语言风格、技术栈偏好、工作习惯
- 任务执行中产生的关键结论和决策
- 外部知识

==怎么存==

- 需要语义检索的内容，比如文档知识、对话摘要这类非结构化的文本，适合存进 **向量数据库**，用embedding编码后通过相似度检索
- 结构化的用户偏好和状态字段，比如语言偏好、项目配置这些可以精准查询的内容，适合用关系数据库或Key-Value存储
- 整段文档或知识库适合存进向量数据库，配合RAG流程做召回

==什么时候取出来用==

- 主动检索：任务开始前，用当前任务的描述去检索相关记忆，把结果注入system prompt作为背景知识
- 被动触发：判断当前步骤需要某类特定知识的时候，主动发起检索

## Agent的长期记忆系统怎么做？

核心工具是向量数据库（Vector Database）加上向量化（Embedding）

- Embedding：把一段文字转化成一组数字的过程。语义相近的文字，转化出来的数字向量在空间中靠的很近
- 向量数据库：存这些数字向量的数据库。核心能力是 *相似度检索*

> 下面的例子：
>
> ```python
> from openai import OpenAI
> import chromadb
> 
> client = OpenAI()
> # ChromaDB 是一个轻量的向量数据库，适合本地开发使用
> db = chromadb.Client()
> # 创建一个「集合」，类似于关系数据库里的表，用来存 Agent 的长期记忆
> collection = db.get_or_create_collection("agent_memory")
> 
> def save_to_long_term(content: str, metadata: dict):
>     # 第一步：把文字内容转成 embedding 向量
>     # text-embedding-3-small 是 OpenAI 的 embedding 模型，把文字变成数字向量
>     embedding = client.embeddings.create(
>         input=content,
>         model="text-embedding-3-small"
>     ).data[0].embedding  # 得到一个几百维的浮点数列表
> 
>     # 第二步：把向量、原文、元信息一起存进向量数据库
>     # 第二步：把向量、原文、元信息一起存进向量数据库
>     # metadata 非常关键，它是记忆的「标签」，后续检索时可以按标签过滤
>     # 比如只查「coding 类型」的记忆，或者只查「最近 7 天」的记忆
>     collection.add(
>         embeddings=[embedding],   # 这是「索引」，用于相似度检索
>         documents=[content],      # 这是原文，检索命中后返回给 LLM 直接使用
>         metadatas=[metadata],     # 附加信息，比如存入时间、任务类型、重要程度、记忆类型
>         ids=[f"mem_{hash(content)}"]
>     )
> 
> def retrieve_memory(query: str, top_k: int = 3) -> list[str]:
>     # 第一步：把当前查询也转成 embedding 向量
>     # 和存储时用的是同一个 embedding 模型，这样「语义距离」才有可比性
>     query_embedding = client.embeddings.create(
>         input=query,
>         model="text-embedding-3-small"
>     ).data[0].embedding
> 
>     # 第二步：在向量数据库里找「向量距离最近」的几条记录
>     # 向量距离近 = 语义相近 = 内容最相关
>     results = collection.query(
>         query_embeddings=[query_embedding],
>         n_results=top_k  # 只取前 top_k 条，避免检索出太多噪音
>     )
>     # 返回的是原文文本列表，LLM 可以直接读取这些记忆内容
>     return results["documents"][0]
> ```

> 长期记忆的一些伪代码：
>
> ```python
> def run_agent_with_memory(user_request: str, long_term_memory, short_term_memory):
>     # 第一步：任务开始前，用任务描述检索长期记忆，拿出相关历史
>     # 这一步让 Agent「想起」和当前任务相关的历史经验和用户偏好
>     relevant_memories = long_term_memory.retrieve(user_request, top_k=3)
> 
>     # 第二步：把检索到的长期记忆注入 system prompt
>     # LLM 会把这些信息当作背景知识，影响它这次任务的处理方式
>     system_prompt = f"""你是一个智能助手。
> 以下是用户的相关历史信息，请在处理任务时参考：
> {chr(10).join(relevant_memories)}"""
> 
>     short_term_memory.add("system", system_prompt)
>     short_term_memory.add("user", user_request)
> 
>     # 第三步：整个任务执行过程中，靠短期记忆维持状态
>     # 每一步的中间结果都追加进 messages，LLM 始终知道做到哪里了
>     result = execute_task_with_short_term_memory(short_term_memory)
> 
>     # 第四步：任务完成后，把重要结论写入长期记忆
>     # 这次任务产生的新知识就沉淀下来，下次可以用
>     if result.is_important:
>         long_term_memory.save(
>             content=result.summary,
>             metadata={"task_type": "coding", "timestamp": now()}
>         )
> 
>     return result
> ```

## Agent记忆压缩的常见方法

- 摘要压缩
- 滑动窗口
- 重要性过滤：打分筛选，只留重要内容
- 结构化抽取：把关键信息抽成结构化数据存起来

一般滑动窗口丢弃之前先做一次摘要

==摘要压缩==

这个由LLM自行判断摘要什么。一些高级做法是 **层级摘要**，最近10轮保留原文，10到50轮的历史压缩成中期摘要，50之前的进一步压缩成更精炼的长期摘要

==重要性过滤==

重要性过滤不考虑时间性，而是根据内容的实际价值来决定去留

一种激进的重要性过滤思路：**观察屏蔽**：在构造Prompt的时候选择性隐藏某些历史条目，例如当前任务是写代码，Agent就把之前关于需求讨论的对话标记为与当前内容无关

==主动压缩==

之前都是被动的触发，但Agent也可以在获取到 2000token的原始搜索结果后压缩为 200 token，在上下文增长的角度压缩，而不是最后再压缩，比较适合工具调用频繁的Agent

### Prompt Caching

LLM每次处理请求的时候，都需要把输入的所有 token 过一遍模型来做计算，这个过程叫做 prefill，是延迟和成本的主要来源之一，

Prompt Caching 的思路是：如果prompt的前缀部分在多次请求之间是一样的，就把这部分的计算结果缓存起来，下次请求如果前缀匹配，就复用换从，不重新计算

## LLM的规划能力提升

- CoT：让LLM把推理步骤写出来，线性地一步步推导到答案
- ToT：让它同时探索多条推理路径，选择最优的继续深入
- GoT：图结构推理，推理节点可复用和合并

## 设计多Agent 的协作和动态切换机制

协作一般靠两件事情：消息传递和共享状态

- 消息传递：Agent完成自己的工作后把结果发出去，下一个Agent取用
- 共享状态是所有Agent共同读写一个状态对象，记录任务进展和中间结果

动态切换靠 Orchestrator来做

- 静态路由：提前写好规则，任务类型A就找Agent X
- LLM动态决策：根据当前情况实时判断该把任务交给谁

> ```python
> def dynamic_route(task_context: str, available_agents: list[str]) -> str:
>     """让 LLM 根据当前上下文决定下一步调用哪个 Agent"""
>     prompt = f"""当前任务状态：
> {task_context}
> 
> 可用的 Agent：
> {chr(10).join(f'- {agent}' for agent in available_agents)}
> 
> 请根据当前进展，判断下一步应该交给哪个 Agent 来执行。
> 只返回 Agent 名称，不需要解释。"""
> 
>     response = client.chat.completions.create(
>         model="gpt-4",
>         messages=[{"role": "user", "content": prompt}]
>     )
>     selected = response.choices[0].message.content.strip()
>     return selected  # 返回选中的 Agent 名称
> ```
