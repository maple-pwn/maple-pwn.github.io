# 从 Prompt Jailbreak 到 GCG

> 最近补了一下 2023 年那篇很出圈的 LLM 越狱论文，这里做一个稍微完整一点的阅读记录。先说结论：这篇文章真正重要的地方，不是找到了某串“神秘字符串”，而是它把 jailbreak 从手搓提示词，推进成了一个可定义、可优化、可迁移、可评测的问题。

想看懂这篇论文，其实要先把四个概念分清楚：**对齐（alignment）**、**jailbreak（越狱）**、**对抗攻击（adversarial attack）**、**迁移性（transferability）**。不过今天还是速过一下。

## 前置知识


### Alignment

现在常见的聊天模型并不是“预训练完就直接上线”，而是会经过一轮或多轮对齐。站在用户视角看，对齐最直观的表现通常是：

- 正常问题，模型尽量给有帮助的回答；
- 高风险、违规、恶意请求，模型尽量拒答；
- 边界模糊的问题，模型会更偏向安全回答。

所以很多时候，我们说一个模型“对齐得不错”，其实是在说它 **学会了在一些场景下拒绝输出**。

!!! note
    这里有个很关键但经常被忽略的点：模型会拒答，不等于模型内部真的“不知道”这些内容。很多时候只是外面多包了一层行为约束。


### Jailbreak

Jailbreak 本质上就是：**想办法绕过这层拒答机制，让模型重新进入“愿意回答”的模式**。

早期很多 jailbreak 都很像提示词杂技：

- 让模型扮演某个角色；
- 把任务塞进虚构场景、游戏规则、小说创作里；
- 强制模型以某种固定开头作答；
- 或者通过多轮对话一点点把它带偏。

这些方法当然有用，但有几个明显问题：

- 很依赖人工经验；
- 对模型版本非常敏感；
- 稍微换个 system prompt 或 safety policy 就可能失效；
- 最关键的是，不太方便系统比较。

也就是说，它更像经验主义，而不像一个清楚的优化问题。


### 对抗攻击

在传统机器学习里，对抗攻击更像一个标准优化任务：

> 给定模型、输入和目标，找一个小扰动，让模型输出偏掉。

图像里这件事比较自然，因为像素是连续的，可以直接沿梯度走。

但 LLM 不一样，输入是 **离散 token**。  你没法对某个 token 做“加 0.01”这种操作，所以很多连续优化方法到了文本空间就变得别扭。

这篇论文的核心技术价值，就是在离散 token 空间里给出了一套足够实用的优化办法。


### 迁移性

如果某个攻击只对你手里那一个模型有效，那它更多像是“把这个模型调坏了”。真正可怕的是 **迁移性**：

- 在模型 A 上优化出的攻击；
- 拿去打模型 B、C、D；
- 依旧有不低成功率。

这意味着攻击利用的不是某个模型私有的 bug，而更像是多个模型共享的脆弱模式。

这篇论文最震撼的地方，就在这里。


## 论文到底在做什么

论文标题叫 **Universal and Transferable Adversarial Attacks on Aligned Language Models**。

里面有两个关键词：

- **Universal**：希望一个 suffix 对很多不同请求都有效；
- **Transferable**：希望它不仅能打穿白盒源模型，还能迁移到别的开源模型，甚至闭源黑盒模型。

论文考虑的攻击形态非常明确：

- 用户原始请求不改；
- system prompt 不改；
- 模型权重不改；
- 只在用户消息后面 **追加一个自动搜索出来的 suffix**。

也就是说，它研究的是一种很干净的 threat model：

> 攻击者只利用普通用户可控的输入文本，就试图绕过模型的安全对齐。

这个设定其实很重要，因为它不是在研究“拿到微调权限以后怎么毁掉模型”，而是在研究 **公开可交互接口本身到底稳不稳**。


## 为什么这篇论文值得看

在这篇文章之前，LLM 越狱当然已经存在，但自动化方法整体不算强。

作者自己在引言里其实说得很直白：过去不是完全没有自动 prompt attack，而是这些方法在“打穿对齐后的聊天模型”这个问题上，效果一直不稳定。

所以这篇论文最有价值的，不是“又多了一个攻击论文”，而是它第一次比较有说服力地展示了：

1. 自动化 jailbreak 真的可以做得很强；
2. 不仅能做单 prompt 攻击，还能做 universal suffix；
3. 这个 suffix 还会迁移到别的模型上。

如果一句话概括，它的工作就是：

> 把 LLM jailbreak 从“提示词玄学”，变成了“离散优化问题”。


## 攻击目标怎么定义


### 为什么不直接逼模型输出整段目标文本

一个很自然的思路是：既然要攻击，那就让模型输出某段指定文本。

但作者认为这个目标太死，有两个问题：

1. 同一个请求本来就可能有很多种“成功回答”，没必要绑死到一个唯一字符串；
2. 如果想做通用攻击，这个目标会过于依赖具体请求，不方便复用。

所以他们没有要求模型精确吐出某个长答案，而是用了一个更巧的代理目标：

> 只要先把模型推到“肯定式开头”的状态里就够了。

也就是说，优化目标不是“整段危险回答”，而是让模型在回答开头几步不要拒答，而是进入“好，我来回答你”的模式。

这个建模非常关键。  因为一旦模型的前几个 token 走到了“配合回答”的方向，后面经常就会顺势继续生成本来不该生成的内容。


### 形式化一点的写法

假设：

- 原始用户请求是 $q$；
- 对抗 suffix 是 $s$；
- 希望模型以某个肯定式前缀 $t$ 开头；
- 模型给出的条件概率记作 $p(\cdot)$。

那论文大致在优化下面这个目标：

$$
\mathcal{L}(s;q,t)=-\sum_{i=1}^{|t|}\log p(t_i\mid q,s,t_{<i})
$$

也就是：让目标前缀 $t$ 的负对数似然尽量低。

如果只优化单个 prompt，这就已经够了。  如果要做通用攻击，那就把多个 prompt 的 loss 加在一起。

如果还要做多模型迁移，那就再把多个模型的 loss 一起加进去。

更粗暴一点地写，就是：

$$
\mathcal{L}_{uni}(s)=\sum_{m\in \mathcal{M}}\sum_{j=1}^{N}\mathcal{L}_m(s;q_j,t_j)
$$

这里的直觉也很简单：

- 对更多请求都有效的 suffix，才叫 universal；
- 在更多模型上都降 loss 的 suffix，才更可能 transferable。


## GCG：Greedy Coordinate Gradient


### 核心思路

论文提出的方法叫 **GCG**，全称 **Greedy Coordinate Gradient**。

一句话概括就是：

> 用梯度帮你挑候选 token，再用贪心搜索真正落子。

难点在于 suffix 是离散 token 序列，不能像图像攻击那样直接连续更新。  GCG 的做法是：

1. 固定当前 suffix；
2. 对 suffix 每个位置，计算“如果这里换 token，loss 大概会往哪边走”；
3. 根据 one-hot 梯度，为每个位置挑出若干个最有希望的候选 token；
4. 不直接信梯度，而是把这些候选真的喂进模型做前向计算；
5. 找到 loss 降得最多的那个替换；
6. 真的把这个位置换掉；
7. 继续迭代。

所以它不是纯梯度法，也不是纯暴力枚举，而是做了一个非常工程化的折中：

- 梯度负责缩小搜索空间；
- 前向评估负责纠正梯度近似误差；
- 贪心替换保证每步都在真实离散空间里更新。


### 它和 AutoPrompt 的差别在哪里

作者认为主要差别在于：

- **AutoPrompt**：每轮先选一个位置，再只在那个位置上评估替换；
- **GCG**：每轮对所有可改位置都算候选，再从全局范围里选当前最优替换。

表面看只是“单坐标”变成了“全坐标候选”，但效果差很多。

我自己的理解是：

- 离散优化本来就很容易卡局部最优；
- 如果每轮只盯一个位置，搜索会非常受限；
- 而 GCG 相当于每轮都在所有位置里做一次更大的局部搜索。

论文也强调，哪怕在相同 forward budget 下，这个差别都很明显。

!!! note
    这也是这篇论文很有意思的地方之一。它不是靠一个特别花哨的新理论赢的，更多是靠把“目标怎么定”“坐标怎么搜”“多 prompt 怎么合起来”这几步拼对了。


### 为什么选 token-level gradient

论文里还专门解释了一个老问题：  文本输入是离散的，那为什么还能算梯度？

原因在于 token 最终都会映射到 embedding。  虽然 token 本身是离散索引，但 one-hot 表示进入嵌入层以后，后续网络仍然是可微的，所以可以对 one-hot 指示变量求梯度，再把它当成“替换哪个 token 更有希望”的近似信号。

这种思路并不是论文首创，HotFlip、AutoPrompt 都做过。  这篇文章真正强的不是“第一次想到对 one-hot 求梯度”，而是 **把这个思路和更合适的搜索策略组合起来**。


### GCG 到底在算什么

这一段如果不展开，前面的“用梯度找 token”其实还是有点空空的。

我们把 suffix 记成长度为 $L$ 的 token 序列：

$$
s=(s_1,s_2,\dots,s_L)
$$

对其中第 $i$ 个位置，可以把当前 token 看成一个 one-hot 向量 $z_i\in\{0,1\}^{|V|}$，这里 $|V|$ 是词表大小。如果词嵌入矩阵记作 $E\in\mathbb{R}^{|V|\times d}$，那这个位置真正送进模型的 embedding 就是

$$
e_i=z_i^\top E
$$

而我们真正关心的是 loss 对 $z_i$ 的变化有多敏感，也就是

$$
g_i=\nabla_{z_i}\mathcal{L}
$$

直觉上，$g_i[v]$ 可以理解成：

- 如果把第 $i$ 个位置往词表第 $v$ 个 token 的方向推一点；
- loss 会更可能上升还是下降；
- 幅度大概有多大。

由于 one-hot 是离散的，当然不能真的做“小数更新”，但可以拿这个梯度做一阶近似，去判断 **哪个 token 最值得试**。


### 梯度是怎么变成候选 token 的

这一点其实就是 GCG 最核心的计算步骤。

假设当前位置原来的 token 是 $c$，你考虑把它换成词表里的某个候选 $v$。  根据一阶泰勒展开，loss 的变化可以近似写成：

$$
\Delta \mathcal{L}_{i,v}
\approx
g_i^\top (e_v-e_c)
$$

如果直接在 one-hot 空间里写，也可以理解成：

$$
\Delta \mathcal{L}_{i,v}\approx g_i[v]-g_i[c]
$$

所以对固定位置 $i$ 来说，越能让这个近似值变小的 token，就越值得进入候选集。

这一步的意义非常大，因为它把本来要枚举整个词表的问题，压缩成了：

- 每个位置只保留 top-k 个“最有希望让 loss 下降”的 token；
- 后面只在这些候选里做真实前向评估。

也就是说，GCG 不是在全词表上暴力搜索，而是在用梯度做一个很便宜的 **粗筛**。


### 为什么还要再做一次真实前向

如果梯度已经告诉你“哪个 token 看起来最好”，那为什么不直接换掉？

因为梯度只是局部线性近似，而 LLM 的实际 loss 面非常非线性。  尤其在离散替换里，这种近似误差会更明显。

所以 GCG 会再做一层校验：

1. 对每个位置拿到 top-k 候选；
2. 从这些候选里采样或组合出一批具体替换方案；
3. 把这些方案真的送进模型做前向；
4. 用真实 loss 选出当前最优替换。

这一步等于在说：

- 梯度负责缩小搜索空间；
- 真正拍板的还是模型自己的 forward loss。

也正因为这样，GCG 的更新是“真离散”的，不是 soft prompt 那种先在连续空间里绕一圈再投影回来。


### 为什么叫 Greedy Coordinate Gradient

这个名字其实对应三层意思：

- **Coordinate**：每次修改的是 suffix 的一个坐标，也就是一个 token 位置；
- **Gradient**：候选是靠梯度筛出来的；
- **Greedy**：每轮只接受当前最能降 loss 的那个替换。

如果把整个 suffix 看成一个离散向量，GCG 做的事就很像：

> 在所有坐标上做局部搜索，然后贪心地走向当前最优邻居。

它不像 beam search 那样保留很多并行分支，也不像强化学习那样去学一个全局策略。  它更朴素，但也更稳定，工程上很好实现。


### 一个更接近实现的流程图

把论文里的算法压平，大致就是下面这条链：

1. 构造当前输入：`原始请求 + 当前 suffix + 目标前缀`
2. 前向计算目标前缀的 NLL loss
3. 反向传播到 suffix 对应的 one-hot / embedding
4. 对每个位置取能让 loss 下降最快的 top-k token
5. 组合出一批候选 suffix
6. 对每个候选 suffix 做真实前向打分
7. 选择 loss 最小的那一个
8. 如果还没收敛，回到第 1 步

你会发现，真正“贵”的步骤主要是两类：

- 一次反向传播，拿梯度；
- 一堆候选的批量前向，做重打分。

所以 GCG 的性能瓶颈，本质上是 **梯度 + batched forward**。


### 教学版伪代码

下面这个代码块只用来解释工作原理，故意省略了真实攻击里涉及的模板拼接、目标构造、模型接口和实验超参数。它不是可直接运行的复现代码，但基本反映了 GCG 的计算骨架。

```python
def gcg_step(model, prompt_tokens, suffix_tokens, target_prefix, topk=32):
    """
    教学版伪代码：
    - prompt_tokens: 原始请求的 token
    - suffix_tokens: 当前正在优化的后缀
    - target_prefix: 用来定义优化目标的前缀
    """

    # 1) 定义当前 loss：希望模型更倾向于生成 target_prefix
    loss = target_nll(
        model=model,
        prompt_tokens=prompt_tokens,
        suffix_tokens=suffix_tokens,
        target_prefix=target_prefix,
    )

    # 2) 反向传播到 suffix 各位置，拿到每个位置对应的梯度
    grads = suffix_token_gradients(loss, suffix_tokens)

    # 3) 用梯度为每个位置挑 top-k 候选 token
    candidate_tokens = []
    for pos in range(len(suffix_tokens)):
        scores = first_order_scores(
            grad=grads[pos],
            current_token=suffix_tokens[pos],
            vocab_embeddings=model.token_embedding_matrix,
        )
        candidate_tokens.append(select_best_k(scores, k=topk))

    # 4) 组装一批“单位置替换”的候选 suffix
    candidate_suffixes = []
    for pos, token_list in enumerate(candidate_tokens):
        for new_tok in token_list:
            trial = suffix_tokens.copy()
            trial[pos] = new_tok
            candidate_suffixes.append(trial)

    # 5) 对所有候选做真实前向，用真实 loss 重打分
    candidate_losses = batch_target_nll(
        model=model,
        prompt_tokens=prompt_tokens,
        suffix_candidates=candidate_suffixes,
        target_prefix=target_prefix,
    )

    # 6) 贪心选出当前最优替换
    best_idx = argmin(candidate_losses)
    return candidate_suffixes[best_idx], candidate_losses[best_idx]
```

如果再把外层循环补上，就是：

```python
suffix = init_suffix()
for _ in range(num_steps):
    suffix, loss = gcg_step(model, prompt, suffix, target_prefix, topk=topk)
    if early_stop(loss):
        break
```

这个框架里最重要的三个函数其实是：

- `target_nll`：定义“什么叫更接近成功攻击”；
- `suffix_token_gradients`：把离散 token 变成可用的梯度信号；
- `batch_target_nll`：用真实 forward loss 给候选重新排序。

论文的主要贡献，本质上也是把这三部分拼得足够有效。


### 一个玩具例子

假设 suffix 长度只有 3：

$$
s=(s_1,s_2,s_3)
$$

某一轮反向传播以后，得到每个位置的 top-2 候选：

- 第 1 位：`{a,b}`
- 第 2 位：`{c,d}`
- 第 3 位：`{e,f}`

那 GCG 常见的一步更新并不是把三个位同时全改，而是先构造若干个“单点替换”的邻居：

- $(a,s_2,s_3)$
- $(b,s_2,s_3)$
- $(s_1,c,s_3)$
- $(s_1,d,s_3)$
- $(s_1,s_2,e)$
- $(s_1,s_2,f)$

然后对这 6 个候选做真实前向，选 loss 最低的那个接受。  
这就是“坐标下降 + 贪心更新”的具体含义。


### 官方代码应该怎么看

如果你想看“论文原理和代码实现是怎么接起来的”，官方仓库最值得看的入口不是大实验脚本，而是仓库 README 里明确提到的两个地方：

- `demo.ipynb`
  这是官方给的最小示例，用来熟悉 GCG 的基本流程。
- `experiments/`
  这是复现实验用的目录，里面包含 individual / multiple / transfer 几类实验配置和启动脚本。

按功能去读，官方实现大致可以拆成四层：

1. **模板和切片层**
   负责把 `用户请求 / suffix / 目标前缀` 拼到同一个输入里，并标清哪些 token 属于可优化区域、哪些 token 属于 target 区域。
2. **梯度层**
   对可优化 suffix 的 token 位置取梯度。
3. **候选生成层**
   根据梯度取 top-k 候选，并构造一批待评估 suffix。
4. **批量打分层**
   对候选 suffix 批量前向，选当前最优。

如果按“原理对代码”的方式看，其实就盯住这四层就够了。  
剩下很多工程细节，无非是：

- tokenizer 差异怎么处理；
- 不同模型的对话模板怎么切；
- batch 大小和显存怎么折中；
- 多行为、多模型实验怎么配置。

!!! note
    官方 README 里明确写了 `demo.ipynb` 是 “minimal implementation of GCG”，而完整的 AdvBench 复现实验代码在 `experiments/` 目录。这两个入口比直接扎进一大堆脚本里更好读。


## 从单 prompt 到 universal suffix


### 多 prompt 联合优化

如果只对一个请求优化，你当然可以搞出一个对这个请求很好用的 suffix。  但这种东西很像“单题特攻”，不太说明问题。

论文更进一步，希望同一个 suffix 能在多种行为请求上都有效。  所以他们把多个 prompt 的 loss 聚合起来，一起优化同一个 suffix。

这一步很重要，因为它把问题从：

- “某一个问题能不能被打穿”

变成了：

- “模型内部有没有一类共享脆弱模式，可以被一个统一 suffix 激活”

而实验结果说明，这种共享模式确实存在。


### 增量式加入 prompt

论文这里还有个挺实用的技巧：  不是一开始就把所有训练 prompt 全扔进去一起优化，而是 **增量式加入**。

大致思路是：

- 先让 suffix 在较少 prompt 上成功；
- 成功后再加下一个 prompt；
- 逐步把训练集合扩展大。

这有点像 curriculum learning。  作者发现这样比“一上来全量硬怼”更稳定。

这个细节很工程，但也很关键。因为 universal attack 本身就是一个更难的联合优化问题，直接全量开打容易把搜索空间搞得太乱。


### 多模型联合优化

如果还想要迁移到别的模型，那最直接的想法就是：  在多个源模型上同时优化 suffix。

论文就是这么干的。它把多个模型的 loss 聚合起来一起优化。  当多个模型使用相同 tokenizer 时，这一步尤其自然，因为梯度都在同一个 token 空间里。

这里顺手还能看出一个点：

- **离散 token 优化** 有时反而比 embedding-space 优化更方便迁移；
- 因为你最终优化出来的就是实际可输入的字符串，而不是某个没法直接输入接口的软提示向量。


## 实验设计


### AdvBench 在测什么

为了系统评估攻击，作者构建了 **AdvBench**。

它分成两类任务：

1. **Harmful Strings**
   目标是让模型精确输出某个目标字符串，比较偏“精细控制”。
2. **Harmful Behaviors**
   目标是不要求精确字符串，只要求模型对某类危险请求做出实质性配合，更像 red teaming。

论文里还提到：

- harmful strings 的长度范围大概是 3 到 44 个 token；
- 对 universal attack，他们会在一部分 behavior 上训练，再看 held-out behavior 上的 ASR；
- 黑盒迁移实验里使用了 **388 个 behavior** 去做评测。

AdvBench 本身也是这篇论文的重要副产品，因为它让后面的工作更方便横向比较。


### 成功指标怎么记

论文主指标是 **ASR（Attack Success Rate）**。

- 对 harmful strings：要求模型输出与目标字符串完全一致；
- 对 harmful behaviors：要求模型对该行为做出“合理尝试”，这里会涉及一定人工判断；
- 对 universal attack：会分别报告 train ASR 和 test ASR。

这个设计挺合理，因为：

- harmful strings 更严格，更像“精确控制能力测试”；
- harmful behaviors 更贴近真实 jailbreak 场景。


## 白盒结果


### 单模型、单任务时，GCG 明显强于旧方法

论文在 **Vicuna-7B** 和 **LLaMA-2-7B-Chat** 上做了白盒攻击，对比了 GBDA、PEZ、AutoPrompt 和 GCG。

表 1 最重要的结果可以直接记下来：

| 模型 | 任务 | AutoPrompt | GCG |
| --- | --- | --- | --- |
| Vicuna-7B | harmful strings | 25% | 88% |
| Vicuna-7B | harmful behaviors | 95% | 99% |
| LLaMA-2-7B-Chat | harmful strings | 3% | 57% |
| LLaMA-2-7B-Chat | harmful behaviors | 45% | 56% |

如果只看这个表，已经能得到两个结论：

- GCG 基本全面压过旧 baseline；
- 在更难啃的 LLaMA-2-7B-Chat 上，它的优势更明显。

尤其是 harmful strings 这一列，非常能说明问题。  
因为这是一个更严格的目标，PEZ 和 GBDA 基本直接扑街，AutoPrompt 也不太行，GCG 才第一次把“自动化离散搜索能稳定打穿对齐模型”这件事做出了像样结果。


### Universal attack 不是幻觉

论文还做了 “25 behaviors, 1 model” 的通用攻击实验，也就是：

- 用 25 个 harmful behaviors 联合优化一个 suffix；
- 然后分别看训练集和 hold-out 测试集上的成功率。

结果也很硬：

- **Vicuna-7B**：GCG 的 train/test ASR 是 **100% / 98%**
- **LLaMA-2-7B-Chat**：GCG 的 train/test ASR 是 **88% / 84%**

这个结果非常关键。  因为它说明存在的不是“某些问题能被单独凿穿”，而是 **一个统一 suffix 可以在大量未见过的相似危险请求上继续生效**。

这基本就把 “universal jailbreak” 从猜想推进成了实证结论。


## 迁移攻击：这篇论文真正震撼的部分


### 黑盒迁移结果

作者把 suffix 优化在 Vicuna、Guanaco 等开源模型上，再拿去打 GPT-3.5、GPT-4、Claude、PaLM-2 等商业模型。

表 2 的数字很值得直接记：

| 方法 | GPT-3.5 | GPT-4 | Claude-1 | Claude-2 | PaLM-2 |
| --- | --- | --- | --- | --- | --- |
| Behavior only | 1.8% | 8.0% | 0.0% | 0.0% | 0.0% |
| Behavior + “Sure, here’s” | 5.7% | 13.1% | 0.0% | 0.0% | 0.0% |
| Behavior + GCG（Vicuna） | 34.3% | 34.5% | 2.6% | 0.0% | 31.7% |
| Behavior + GCG（Vicuna & Guanacos） | 47.4% | 29.1% | 37.6% | 1.8% | 36.1% |
| Concatenate | 79.6% | 24.2% | 38.4% | 1.3% | 14.4% |
| Ensemble | 86.6% | 46.9% | 47.9% | 2.1% | 66.0% |

只看这张表，其实已经足够说明这篇论文为什么会出圈。

因为它告诉你：

- 纯人工 baseline 很弱；
- 自动搜索出的 suffix 突然能显著打动黑盒商业模型；
- 多模型联合优化后，迁移进一步上升；
- ensemble 还能继续抬成功率。


### 为什么 GPT 系列更容易中招

论文里作者自己也讨论了一个现象：  GPT-3.5 / GPT-4 上的迁移成功率偏高，而 Claude-2 明显更稳。

一个他们给出的解释是：

- Vicuna 本身基于 ChatGPT 输出蒸馏；
- 所以在某种意义上，Vicuna 和 GPT-3.5 之间并不是完全独立；
- 对抗迁移在“蒸馏关系”或“同血缘数据分布”之间，本来就可能更强。

这个解释我觉得挺合理。  所以不能简单把结论说成“GPT 比 Claude 差”，更准确的说法应该是：

- 不同闭源模型确实表现不同；
- 但这些差异里掺杂了血缘关系、前置过滤、接口策略、采样参数等多个因素。


### Claude-2 为什么低很多

论文里 Claude-2 的 ASR 很低，最高也就 **2.1%**。

作者并没有把这件事解释成“Claude-2 理论上解决了问题”，而是相对克制地提出了几个可能性：

- 它可能确实更 robust；
- 也可能有更前置的内容过滤器；
- 聊天界面和 API 的行为还不完全一致；
- 人工轻微改写用户请求后，原本失败的攻击有时又能成功。

也就是说，Claude-2 更像是“工程防护做得更厚”，而不是“从根上免疫了 suffix attack”。


## 一个特别有意思的现象：迁移过拟合

论文还有个我很喜欢的观察：**优化太久，迁移反而会变差。**

也就是：

- 源模型上的 loss 继续下降；
- 白盒攻击看起来越来越成功；
- 但迁移到黑盒模型上的 ASR 反而下降。

作者把它叫做 **transfer overfitting**。

这和经典对抗样本有点像：  
你越贴着源模型去抠，越可能只学到源模型私有的脆弱性，而不是多个模型共享的那部分非鲁棒特征。

所以这篇论文真正追求的，不是“单模型上把 loss 打到最低”，而是 **找到跨模型共享的攻击方向**。

我觉得这点非常关键，因为它说明 jailbreak 攻击已经不只是 prompt engineering，而开始有一点 adversarial ML 那种味道了。


## 论文里几个很值得记住的技术判断


### 1. 只优化第一个 token 不够

论文明确说过，如果你只逼模型先输出一个 “Sure” 之类的起始 token，很容易出现一种假成功：

- 模型确实没拒答；
- 但它可能只是被带去别的无关方向；
- 并没有真正开始配合原始危险请求。

所以他们才会选择“肯定式前缀 + 重述原请求”的目标，而不是只盯第一个 token。


### 2. 文本攻击和图像攻击不完全一样

在图像里，大家通常强调“人眼几乎看不出来的微小扰动”。

但文本里没有这种天然定义，因为 token 一换，人类几乎一定能看出来变了。

这篇论文反而指出：  
在 aligned LLM 这个问题里，这件事没那么尴尬。

因为 threat model 本来就是：

> 任何用户可输入的附加文本，只要能让模型越过安全边界，都算攻击成功。

也就是说，在这个任务里，不需要维持“语义等价扰动”那套严格约束。  
这反而让问题定义更干净。


### 3. 多模型优化有助于 prompt 变得更“有结构”

论文讨论部分还提到一个挺有意思的观察：

- 单模型 prompt 有时看起来非常像乱码；
- 多 prompt、多模型联合优化出来的 suffix，反而更容易出现某种可解释结构。

作者给出的例子里，优化出来的攻击串里会出现一些和目标有关的自然语言残片，比如要求模型重述第一句、先以某种语气开头之类。

这不意味着攻击提示词就是“有意义的人类语言”，但至少说明：

- 模型并不是完全被无语义噪声骗了；
- 它更像是被推到了某种可重复触发的内部响应模式。


## 我自己的理解


### 这篇论文最大的贡献不是“攻击更强”，而是“问题建模更清楚”

如果只从结果看，它当然是在说“我比之前更能越狱”。

但从研究角度看，我觉得它最大的贡献其实是把问题拆清楚了：

1. **目标怎么定**：不逼整段答案，只逼“肯定式开头”；
2. **离散空间怎么搜**：梯度筛候选，真实前向选替换；
3. **怎么做 universal**：多 prompt 聚合；
4. **怎么做 transfer**：多模型聚合；
5. **怎么测**：AdvBench + ASR。

这五步拼起来，后面很多自动化 jailbreak 工作基本都绕不开它。


### 它打掉的是“表层拒答”，不是“内部能力”

这篇论文反复提醒我们一件事：

> 如果模型能力本体还在，只是后训练阶段学会了“别说”，那它就始终可能被某种输入重新拉回去。

也就是说，很多 alignment 更像是行为层修补，而不是能力层删除。

这也是为什么作者最后会把问题引向更大的方向：

- 单纯补拒答模式够不够；
- 输入过滤够不够；
- 对抗训练会不会有用；
- 更前置的预训练约束能不能减少这类能力暴露。


### Claude-2 的低 ASR 不该被过度解读

这篇论文很容易被读成：

- GPT 被打得挺惨；
- Claude-2 很稳；
- 所以 Claude-2 已经解决了这个问题。

我觉得这个结论太快了。

更稳妥的理解应该是：

- 在作者的自动化 suffix attack 设定下，Claude-2 确实更难打；
- 但它未必从机制上“证明安全”；
- 其中可能混入了额外检测器、接口过滤、采样设置和数据血缘差异。

论文自己其实也没有做那种过度结论。


### 论文的局限也挺明显

我觉得至少有这几个边界：

- 它研究的是 **suffix attack**，不等于覆盖所有 jailbreak 形态；
- harmful behavior 的成功判定含有一定人工判断；
- 商业模型的接口层还有很多不可见因素，实验可重复性天然有限；
- 高迁移率与模型血缘关系可能有关；
- 它证明了“现有对齐不稳”，但没有给出真正通用的解决方案。

所以这篇论文更像一记重锤，而不是完整答案。


## 对防御有什么启发

这篇论文虽然是攻击论文，但对防御的启发反而很大。

我自己读下来，至少有几条：

### 1. 单纯拒答模板不够

如果安全策略只是“看到某类请求就拒答”，那它本质上仍然是一个可以被优化绕过的输出行为。


### 2. 前置检测器也不够稳

论文讨论 Claude 时提到，聊天界面里可能存在更前置的内容过滤。  
但作者也指出，这种 detector 在视觉领域早就被证明很难构成根本防御。

直觉上也好理解：

- 你加了一个检测器；
- 攻击者就把任务改成“同时绕过检测器和模型”。


### 3. 对抗训练可能有帮助，但代价未知

作者在结论里提到，最自然的后续方向其实就是 **adversarial training**：

- 用 GCG 这类方法持续攻击模型；
- 再把正确拒答行为反喂回训练。

但这条路有两个老问题：

- 训练成本高；
- 鲁棒性和正常能力之间可能存在 trade-off。

视觉里这事已经打了很多年，LLM 里大概率也不会轻松。


### 4. 更根本的问题可能在预训练阶段

如果模型在预训练时已经强烈吸收了危险知识和相应文本模式，后面对齐更多是在“补行为”，那它天然就更容易被重新激活。

这也是作者最终把问题推到更前面去的原因：  
也许需要的不只是后训练补丁，而是更前置、更结构性的安全设计。


## 总结

如果一句话概括这篇论文，我会写成：

> 它把 LLM jailbreak 从经验主义的提示词技巧，推进成了一个可系统优化、可跨模型迁移的对抗攻击问题。

再展开一点，我觉得它最值得记住的是四件事：

1. **自动化越狱是能做强的**，而且不只是白盒玩具；
2. **universal suffix 确实存在**，不是个别 prompt 特攻；
3. **迁移性是真问题**，说明很多模型共享同类脆弱性；
4. **现有对齐更像行为修补**，离真正鲁棒还有距离。

所以如果现在还把“模型会拒答”直接等同于“模型安全”，那基本属于想多了。

> 这篇论文未必把理论讲透了，但它很像一个分水岭。后面的自动化 jailbreak、红队 benchmark 和 defense 讨论，很多都得沿着它给出的框架继续往下走。


## 参考

参考文献

- [Universal and Transferable Adversarial Attacks on Aligned Language Models](https://arxiv.org/abs/2307.15043)
- [论文 HTML 版（arXiv experimental HTML）](https://arxiv.org/html/2307.15043v2)
- [llm-attacks 项目主页](https://llm-attacks.org/)
- [llm-attacks 代码仓库](https://github.com/llm-attacks/llm-attacks)
- [Jailbroken: How Does LLM Safety Training Fail?](https://arxiv.org/abs/2307.02483)
- [Are Aligned Neural Networks Adversarially Aligned?](https://arxiv.org/abs/2306.15447)
- [AutoPrompt: Eliciting Knowledge from Language Models with Automatically Generated Prompts](https://arxiv.org/abs/2010.15980)
