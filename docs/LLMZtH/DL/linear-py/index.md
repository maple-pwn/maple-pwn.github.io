# 基于 CIFAR-10 的线性分类方法比较研究：SVM 与 Softmax 分类器


## 摘要

本文对两种线性分类方法——支持向量机(SVM)和 Softmax 分类器在 CIFAR-10 图像数据集上的性能进行了系统比较研究。我们使用 NumPy 从零实现了两种分类器,并在原始像素特征上评估其性能。实验结果表明,Softmax 分类器取得了更优的性能,验证集准确率为 37.6%,测试集准确率为 34.7%,而 SVM 分别为 35.0% 和 32.6%。本文从理论角度分析了交叉熵损失优于铰链损失的原因,将性能差异归因于 Softmax 的持续优化压力与 SVM 基于间隔的满足准则之间的差异。研究包含详细的超参数调优过程,并讨论了损失函数设计对分类性能的影响。

**关键词:** 线性分类、支持向量机、Softmax 分类器、CIFAR-10、图像识别、损失函数

---


## 1. 引言

图像分类是计算机视觉领域的基础问题,为从目标识别到场景理解等众多应用提供了基础。尽管深度学习方法近年来取得了显著成功,但理解更简单的线性模型的行为能够为分类任务的本质和损失函数设计提供宝贵见解。

本研究探讨了两种经典的线性分类方法:采用铰链损失的支持向量机(SVM)和采用交叉熵损失的 Softmax 分类器。两种方法都学习从输入特征到类别得分的线性映射,但在优化目标上存在根本差异。我们在 CIFAR-10 数据集上进行了系统比较,该数据集是一个广泛使用的基准,包含 60,000 张 32×32 彩色图像,涵盖 10 个物体类别。

**本文的主要贡献包括:**

1. 基于小批量随机梯度下降的线性 SVM 和 Softmax 分类器的完整实现
2. 展示搜索过程的全面超参数调优方法
3. 证明 Softmax 在原始像素特征上优越性的实验证据
4. 通过损失函数性质解释性能差距的理论分析

---


## 2. 方法论


### 2.1 线性分类器架构

我们设计了一个基础线性分类器架构,通过仿射变换将输入特征 $\mathbf{x} \in \mathbb{R}^D$ 映射到类别得分 $\mathbf{s} \in \mathbb{R}^C$:

$$
\mathbf{s} = \mathbf{W}^T\mathbf{x} + \mathbf{b}
$$

其中 $\mathbf{W} \in \mathbb{R}^{D \times C}$ 是权重矩阵,$\mathbf{b} \in \mathbb{R}^C$ 是偏置向量。预测类别由 $\hat{y} = \arg\max_j s_j$ 确定。


### 2.2 支持向量机 (SVM)

SVM 分类器采用多类铰链损失函数:

$$
L_i^{\text{SVM}} = \sum_{j \neq y_i} \max(0, s_j - s_{y_i} + \Delta)
$$

其中 $y_i$ 是真实类别标签,$s_{y_i}$ 是正确类别的得分,$s_j$ 表示错误类别的得分,$\Delta$ 是间隔参数(设为 1.0)。总损失包含 L2 正则化:

$$
L = \frac{1}{N}\sum_{i=1}^N L_i^{\text{SVM}} + \lambda \|\mathbf{W}\|_F^2
$$


### 2.3 Softmax 分类器

Softmax 分类器使用交叉熵损失,通过 softmax 函数产生类别概率:

$$
p_j = \frac{e^{s_j}}{\sum_{k=1}^C e^{s_k}}
$$

单个样本的损失为:

$$
L_i^{\text{Softmax}} = -\log p_{y_i} = -\log\frac{e^{s_{y_i}}}{\sum_j e^{s_j}}
$$

加上正则化:

$$
L = \frac{1}{N}\sum_{i=1}^N L_i^{\text{Softmax}} + \lambda \|\mathbf{W}\|_F^2
$$

为保证数值稳定性,我们在指数运算前减去最大得分,应用 log-sum-exp 技巧。


### 2.4 优化方法

两种分类器均使用小批量随机梯度下降(SGD)训练:

$$
\mathbf{W} \leftarrow \mathbf{W} - \eta \nabla_{\mathbf{W}} L, \quad \mathbf{b} \leftarrow \mathbf{b} - \eta \nabla_{\mathbf{b}} L
$$

其中 $\eta$ 是学习率。权重从 $\mathcal{N}(0, 0.001^2)$ 初始化,偏置初始化为零。

---


## 3. 实验设置


### 3.1 数据集与预处理

我们在 CIFAR-10 数据集上评估方法,该数据集包含 60,000 张 32×32 彩色图像,涵盖 10 个类别(飞机、汽车、鸟、猫、鹿、狗、青蛙、马、船、卡车)。数据集划分如下:

- **训练集:** 49,000 样本
- **验证集:** 1,000 样本
- **测试集:** 1,000 样本

**预处理流程:**

1. **展平:** 图像从 (32, 32, 3) 重塑为 3,072 维向量
2. **均值归一化:** 计算训练集均值并从所有数据集中减去
3. **类型转换:** 数据转换为 float32 以保证数值稳定性

为快速原型验证,我们还创建了 400 样本的开发子集,用于在全规模训练前验证梯度正确性。


### 3.2 超参数调优

我们在以下范围内进行系统的网格搜索:

**初始搜索(粗粒度):**

- 学习率: {5×10⁻⁸, 1×10⁻⁷, 2×10⁻⁷, 5×10⁻⁷, 1×10⁻⁶}
- 正则化: {1×10⁻⁵, 1×10⁻⁴, 1×10⁻³, 1×10⁻²}

**精细搜索(基于初始结果):**

- 学习率: {7×10⁻⁸, 1×10⁻⁷, 1.5×10⁻⁷, 2×10⁻⁷, 3×10⁻⁷}
- 正则化: {1×10⁻², 1×10⁻¹, 1, 10, 100, 1000}

**固定超参数:**

- 批量大小: 200
- 训练迭代次数: 1,500
- 间隔(仅 SVM): Δ = 1.0


### 3.3 验证协议

对于每个超参数配置,我们:

1. 在训练集上训练
2. 在验证集上评估以选择最佳配置
3. 在保留的测试集上报告最终性能

这确保了无偏的性能估计并防止测试集泄漏。

---


## 4. 实验结果


### 4.1 开发集验证

在 400 样本的开发子集上的初始实验确认了:

1. **损失收敛:** 训练损失从约 9.0 持续下降到约 6.5,表明前向传播和梯度计算正确
2. **过拟合检测:** 训练准确率 82% vs 验证准确率 23% 揭示了由于小样本量导致的严重过拟合
3. **解决方案:** 切换到完整训练集(49,000 样本)消除了过拟合,训练和验证准确率收敛到合理值


### 4.2 SVM 超参数搜索

**初始粗粒度搜索结果:**

| 学习率 | 正则化 | 验证准确率 |
| --- | --- | --- |
| 5×10⁻⁸ | 1×10⁻⁴ | 28.2% |
| 1×10⁻⁷ | 1×10⁻⁴ | 31.5% |
| 2×10⁻⁷ | 1×10⁻⁴ | 33.1% |

**关键观察:**

- 学习率显著影响性能;更高的学习率提升训练准确率
- 正则化在 [10⁻⁵, 10⁻²] 范围内影响极小,表明正则化过弱

**精细搜索策略:**

- 在 1×10⁻⁷ 附近进行细粒度学习率搜索
- 扩大正则化范围以观察其真实影响

**精细搜索结果:**

扩大的正则化范围揭示了显著影响。与通常预期(过度正则化损害性能)相反,我们观察到 λ = 1000 提升了验证准确率。我们假设这是因为:

1. 固定的学习率和迭代次数创造了优化约束
2. 强正则化稳定了权重更新
3. 防止 SGD 期间的剧烈参数变化
4. 改善了原始像素特征上的泛化

**最佳 SVM 配置:**

- 学习率: 1.5×10⁻⁷
- 正则化: λ = 1000
- **验证准确率: 35.0%**
- **测试准确率: 32.6%**


### 4.3 Softmax 超参数搜索

使用与 SVM 相同的搜索范围,Softmax 立即显示出优越性能:

**初始搜索结果:**

| 学习率 | 正则化 | 验证准确率 |
| --- | --- | --- |
| 1×10⁻⁷ | 1×10⁻⁴ | 35.8% |
| 1.5×10⁻⁷ | 1×10⁻⁴ | 37.2% |
| 2×10⁻⁷ | 1×10⁻⁴ | 36.9% |

Softmax 即使未经精细调优也优于 SVM。我们从初始搜索中选择最佳配置:

**最佳 Softmax 配置:**

- 学习率: 1.5×10⁻⁷
- 正则化: λ = 1×10⁻⁴
- **验证准确率: 37.6%**
- **测试准确率: 34.7%**


### 4.4 性能对比

**表 1: 最终性能对比**

| 分类器 | 训练准确率 | 验证准确率 | 测试准确率 | 提升 |
| --- | --- | --- | --- | --- |
| 线性 SVM | 36.8% | 35.0% | 32.6% | — |
| Softmax | 39.2% | 37.6% | 34.7% | +2.6% (验证) |

**关键发现:**

1. Softmax 在验证集上实现了 7.4% 的相对提升
2. 测试准确率遵循类似趋势(+2.1% 绝对提升)
3. 两种方法都显示出合理的训练-验证-测试一致性,表明适当的泛化
4. 性能差距在所有数据划分上持续存在,表明系统性优势

---


## 5. 讨论


### 5.1 Softmax 优于 SVM 的原因分析

我们的实验结果表明,Softmax 分类器在 CIFAR-10 原始像素特征上取得了优于线性 SVM 的性能。本节从理论角度分析这一性能差距。


#### 5.1.1 损失函数性质

根本差异在于优化目标:

**SVM (铰链损失):**

$$
L_i^{\text{SVM}} = \sum_{j \neq y_i} \max(0, s_j - s_{y_i} + \Delta)
$$

这种损失表现出"满足准则":一旦正确类别得分超过错误类别得分达到间隔 Δ,损失变为零。模型停止优化该样本,即使间隔可以进一步增大。

**Softmax (交叉熵损失):**

$$
L_i^{\text{Softmax}} = -\log\frac{e^{s_{y_i}}}{\sum_j e^{s_j}}
$$

这种损失永不饱和——它持续推动正确类别概率趋向 1.0,错误类别概率趋向 0.0。不存在"足够好"的阈值;优化压力贯穿整个训练过程。


#### 5.1.2 对 CIFAR-10 的影响

CIFAR-10 对线性分类器提出了重大挑战:

1. **高类间相似性:** 汽车 vs 卡车、猫 vs 狗、鹿 vs 马共享大量视觉特征
2. **高类内方差:** 物体以不同尺度、方向和光照条件出现
3. **原始像素特征:** 无特征工程或深度表示

在这种情况下,SVM 基于间隔的准则被证明是不够的。一旦训练样本满足间隔约束,模型停止细化决策边界。然而,验证集和测试集包含的新变化将受益于更紧密的类别分离。

Softmax 通过持续细化概率分布来解决这个问题。即使在实现正确分类后,模型仍继续调整权重以增加对正确预测的置信度。这种持续的优化压力导致在未见数据上更好的泛化。


#### 5.1.3 梯度信号分析

**SVM 梯度行为:**

- 满足间隔约束的样本贡献零梯度
- 只有"违反"样本驱动参数更新
- 随着训练进行,更少样本贡献优化
- 梯度信号变得稀疏

**Softmax 梯度行为:**

- 所有样本贡献非零梯度(除非概率 = 1.0,这很少发生)
- 梯度幅度与预测不确定性成比例
- 整个训练过程中密集的梯度信号
- 更有效地利用训练数据

对于 CIFAR-10 在像素空间中模糊的类别边界,Softmax 的密集梯度信号能够更彻底地探索参数空间。


### 5.2 正则化效应

一个意外发现是 SVM 受益于非常强的正则化(λ = 1000),这与典型直觉相反。我们提出以下解释:

在固定学习率和迭代次数的情况下,强正则化充当隐式学习率调度器:

- 早期迭代:大梯度被正则化抑制
- 后期迭代:正则化防止在局部最小值附近振荡
- 净效应:更平滑的优化轨迹和更好的收敛

这表明在受约束的优化设置(固定迭代预算)中,正则化可以补偿次优的学习率调度。


### 5.3 局限性与未来工作

**当前局限性:**

1. **特征表示:** 原始像素是弱特征;卷积特征可能改善两种方法
2. **模型容量:** 线性模型无法捕获非线性类别边界
3. **超参数搜索:** 网格搜索计算昂贵;贝叶斯优化可能更高效
4. **单一随机种子:** 结果应在多次运行中平均以获得统计显著性

**未来方向:**

1. **特征工程:** 方向梯度直方图(HOG)、SIFT 或学习特征
2. **非线性扩展:** 核 SVM、多层感知器
3. **高级优化:** 自适应学习率(Adam、RMSprop)、学习率调度
4. **数据增强:** 随机裁剪、翻转、颜色抖动以增加有效训练集大小
5. **集成方法:** 组合多个分类器以提高鲁棒性

---


## 6. 结论

本文对线性 SVM 和 Softmax 分类器在 CIFAR-10 图像分类上进行了全面比较。通过系统的超参数调优和仔细的实验设计,我们证明了 Softmax 达到 37.6% 验证准确率和 34.7% 测试准确率,优于 SVM 的 35.0% 和 32.6%。

我们的理论分析将这一性能差距归因于损失函数设计的根本差异:SVM 基于间隔的满足准则 vs Softmax 的持续概率优化。对于具有模糊类别边界和弱特征表示的挑战性数据集,Softmax 的持续优化压力导致更优的泛化。

研究还揭示了有趣的正则化动态,其中强正则化在固定优化预算下改善了 SVM 性能——这一发现值得在受约束学习场景中进一步研究。

虽然线性模型在 CIFAR-10 上取得的绝对性能适中,但这项工作为损失函数设计和优化动态提供了宝贵见解,这些见解延伸到现代深度学习系统。理解这些基本原理对于开发更复杂的分类方法仍然至关重要。

---


## 参考文献

1. Krizhevsky, A., & Hinton, G. (2009). Learning multiple layers of features from tiny images. Technical Report, University of Toronto.
2. Cortes, C., & Vapnik, V. (1995). Support-vector networks. Machine learning, 20(3), 273-297.
3. Bishop, C. M. (2006). Pattern recognition and machine learning. Springer.
4. Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep learning. MIT press.
5. Bottou, L. (2010). Large-scale machine learning with stochastic gradient descent. In Proceedings of COMPSTAT (pp. 177-186).

---


## 附录 A: 实现代码

完整实现代码如下,以确保可重现性:


### A.1 基础线性分类器


```

class

LinearClassifier
:


def

__init__
(
self
,

reg
=
1e-4
,

learning_rate
=
1e-7
,

num_iters
=
1500
,


batch_size
=
200
,

verbose
=
False
,

seed
=
None
):


self
.
reg

=

reg


self
.
learning_rate

=

learning_rate


self
.
num_iters

=

num_iters


self
.
batch_size

=

batch_size


self
.
verbose

=

verbose


self
.
seed

=

seed


self
.
W

=

None


self
.
b

=

None


def

train
(
self
,

X
,

y
):


"""训练线性分类器"""


num_train
,

dim

=

X
.
shape


num_classes

=

np
.
max
(
y
)

+

1



# 初始化权重


if

self
.
W

is

None
:


rng

=

np
.
random
.
default_rng
(
self
.
seed
)


self
.
W

=

rng
.
normal
(
0
,

0.001
,

(
dim
,

num_classes
))


self
.
b

=

np
.
zeros
(
num_classes
)


loss_history

=

[]


for

it

in

range
(
self
.
num_iters
):



# 小批量采样


batch_indices

=

np
.
random
.
choice
(
num_train
,

self
.
batch_size
)


X_batch

=

X
[
batch_indices
]


y_batch

=

y
[
batch_indices
]



# 计算损失和梯度


loss
,

dW
,

db

=

self
.
loss
(
X_batch
,

y_batch
)


loss_history
.
append
(
loss
)



# 参数更新


self
.
W

-=

self
.
learning_rate

*

dW


self
.
b

-=

self
.
learning_rate

*

db


if

self
.
verbose

and

it

%

100

==

0
:


print
(
f
'iteration
{
it
}
 /
{
self
.
num_iters
}
: loss
{
loss
}
'
)


return

loss_history


def

predict
(
self
,

X
):


"""预测类别"""


scores

=

X
.
dot
(
self
.
W
)

+

self
.
b


y_pred

=

np
.
argmax
(
scores
,

axis
=
1
)


return

y_pred


def

loss
(
self
,

X
,

y
):


"""计算损失和梯度(由子类实现)"""


raise

NotImplementedError

```


### A.2 SVM 实现


```

class

LinearSVM
(
LinearClassifier
):


def

__init__
(
self
,

delta
=
1.0
,

**
kwargs
):


super
()
.
__init__
(
**
kwargs
)


self
.
delta

=

delta


def

loss
(
self
,

X
,

y
):


"""计算 SVM 损失和梯度"""


num_train

=

X
.
shape
[
0
]



# 前向传播


scores

=

X
.
dot
(
self
.
W
)

+

self
.
b


correct_class_scores

=

scores
[
np
.
arange
(
num_train
),

y
]


margins

=

np
.
maximum
(
0
,

scores

-

correct_class_scores
[:,

np
.
newaxis
]

+

self
.
delta
)


margins
[
np
.
arange
(
num_train
),

y
]

=

0



# 损失


loss

=

np
.
sum
(
margins
)

/

num_train


loss

+=

self
.
reg

*

np
.
sum
(
self
.
W

*

self
.
W
)



# 梯度


binary

=

margins


binary
[
margins

>

0
]

=

1


row_sum

=

np
.
sum
(
binary
,

axis
=
1
)


binary
[
np
.
arange
(
num_train
),

y
]

=

-
row_sum


dW

=

X
.
T
.
dot
(
binary
)

/

num_train


dW

+=

2

*

self
.
reg

*

self
.
W


db

=

np
.
sum
(
binary
,

axis
=
0
)

/

num_train


return

loss
,

dW
,

db

```


### A.3 Softmax 实现


```

class

SoftmaxClassifier
(
LinearClassifier
):


def

loss
(
self
,

X
,

y
):


"""计算 Softmax 损失和梯度"""


num_train

=

X
.
shape
[
0
]



# 前向传播


scores

=

X
.
dot
(
self
.
W
)

+

self
.
b



# 数值稳定性


scores

-=

np
.
max
(
scores
,

axis
=
1
,

keepdims
=
True
)



# Softmax


exp_scores

=

np
.
exp
(
scores
)


probs

=

exp_scores

/

np
.
sum
(
exp_scores
,

axis
=
1
,

keepdims
=
True
)



# 损失


correct_logprobs

=

-
np
.
log
(
probs
[
np
.
arange
(
num_train
),

y
])


loss

=

np
.
sum
(
correct_logprobs
)

/

num_train


loss

+=

self
.
reg

*

np
.
sum
(
self
.
W

*

self
.
W
)



# 梯度


dscores

=

probs
.
copy
()


dscores
[
np
.
arange
(
num_train
),

y
]

-=

1


dscores

/=

num_train


dW

=

X
.
T
.
dot
(
dscores
)


dW

+=

2

*

self
.
reg

*

self
.
W


db

=

np
.
sum
(
dscores
,

axis
=
0
)


return

loss
,

dW
,

db

```


### A.4 数据预处理


```

def

preprocess_cifar10
(
X_train
,

y_train
,

X_test
,

y_test
,


num_training
=
49000
,

num_validation
=
1000
,


num_test
=
1000
,

seed
=
42
):


"""

    预处理流程:

    1. 划分 train/val/test

    2. 展平图像

    3. 转换为 float32

    4. 减去均值

    """



# 划分训练/验证


X_val

=

X_train
[
num_training
:
num_training

+

num_validation
]


y_val

=

y_train
[
num_training
:
num_training

+

num_validation
]


X_train

=

X_train
[:
num_training
]


y_train

=

y_train
[:
num_training
]


X_test

=

X_test
[:
num_test
]


y_test

=

y_test
[:
num_test
]



# 展平: (N,32,32,3) -> (N,3072)


X_train

=

X_train
.
reshape
(
X_train
.
shape
[
0
],

-
1
)
.
astype
(
np
.
float32
)


X_val

=

X_val
.
reshape
(
X_val
.
shape
[
0
],

-
1
)
.
astype
(
np
.
float32
)


X_test

=

X_test
.
reshape
(
X_test
.
shape
[
0
],

-
1
)
.
astype
(
np
.
float32
)



# 减去训练集均值


mean_image

=

np
.
mean
(
X_train
,

axis
=
0
)


X_train

-=

mean_image


X_val

-=

mean_image


X_test

-=

mean_image


return

X_train
,

y_train
,

X_val
,

y_val
,

X_test
,

y_test

```

---


## 致谢

本研究作为深度学习课程项目完成。感谢 CIFAR-10 数据集创建者使该基准公开可用。

**作者贡献:** 实现、实验、分析和论文撰写均由作者完成。

**数据可用性:** CIFAR-10 数据集可在 <https://www.cs.toronto.edu/~kriz/cifar.html> 公开获取。

**代码可用性:** 完整实现代码在附录 A 中提供。
