# 7 1


```

"""

============================================================

  贝叶斯分类器综合演示（含详细计算过程）

  知识点：贝叶斯决策论、极大似然估计、朴素贝叶斯分类器、

          半朴素贝叶斯分类器、贝叶斯网、EM算法

============================================================

"""

import

numpy

as

np

from

collections

import

defaultdict
,

Counter

from

itertools

import

combinations

import

warnings

warnings
.
filterwarnings
(
"ignore"
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 工具函数


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def

print_title
(
title
):


"""打印标题"""


width

=

60


print
(
"
\n
"

+

"="

*

width
)


print
(
f
"
{
title
}
"
)


print
(
"="

*

width
)

def

print_step
(
step_name
):


"""打印子步骤标题"""


print
(
f
"
\n
  ┌─
{
step_name
}
"
)


print
(
f
"  │"
)

def

print_calc
(
text
):


"""打印计算步骤"""


print
(
f
"  │
{
text
}
"
)

def

print_result
(
text
):


"""打印结果"""


print
(
f
"  │  ✦
{
text
}
"
)

def

print_end
():


"""打印步骤结束"""


print
(
f
"  └─────────────────────────────────────────"
)

def

generate_discrete_dataset
(
n_samples
=
200
,

seed
=
42
):


"""

    生成离散特征的分类数据集（模拟西瓜数据集风格）

    特征：色泽(0/1/2)、根蒂(0/1/2)、敲声(0/1/2)

    标签：好瓜(1) / 坏瓜(0)

    """


np
.
random
.
seed
(
seed
)


X
,

y

=

[],

[]


for

_

in

range
(
n_samples
):


label

=

np
.
random
.
choice
([
0
,

1
],

p
=
[
0.45
,

0.55
])


if

label

==

1
:


x0

=

np
.
random
.
choice
([
0
,

1
,

2
],

p
=
[
0.1
,

0.2
,

0.7
])


x1

=

np
.
random
.
choice
([
0
,

1
,

2
],

p
=
[
0.6
,

0.25
,

0.15
])


x2

=

np
.
random
.
choice
([
0
,

1
,

2
],

p
=
[
0.65
,

0.2
,

0.15
])


else
:


x0

=

np
.
random
.
choice
([
0
,

1
,

2
],

p
=
[
0.5
,

0.35
,

0.15
])


x1

=

np
.
random
.
choice
([
0
,

1
,

2
],

p
=
[
0.15
,

0.35
,

0.5
])


x2

=

np
.
random
.
choice
([
0
,

1
,

2
],

p
=
[
0.15
,

0.3
,

0.55
])


X
.
append
([
x0
,

x1
,

x2
])


y
.
append
(
label
)


return

np
.
array
(
X
),

np
.
array
(
y
)

def

generate_continuous_dataset
(
n_samples
=
300
,

seed
=
42
):


"""生成连续特征的分类数据集（用于高斯朴素贝叶斯）"""


np
.
random
.
seed
(
seed
)


n0

=

n_samples

//

2


n1

=

n_samples

-

n0


X0

=

np
.
random
.
randn
(
n0
,

2
)

*

1.2

+

np
.
array
([
1
,

2
])


X1

=

np
.
random
.
randn
(
n1
,

2
)

*

1.0

+

np
.
array
([
4
,

5
])


X

=

np
.
vstack
([
X0
,

X1
])


y

=

np
.
array
([
0
]

*

n0

+

[
1
]

*

n1
)


idx

=

np
.
random
.
permutation
(
n_samples
)


return

X
[
idx
],

y
[
idx
]

def

train_test_split
(
X
,

y
,

test_ratio
=
0.3
,

seed
=
42
):


"""简单的训练/测试集划分"""


np
.
random
.
seed
(
seed
)


n

=

len
(
y
)


idx

=

np
.
random
.
permutation
(
n
)


split

=

int
(
n

*

(
1

-

test_ratio
))


return

X
[
idx
[:
split
]],

X
[
idx
[
split
:]],

y
[
idx
[:
split
]],

y
[
idx
[
split
:]]

def

accuracy
(
y_true
,

y_pred
):


"""计算准确率"""


return

np
.
mean
(
np
.
array
(
y_true
)

==

np
.
array
(
y_pred
))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 第一部分：贝叶斯决策论 (Bayesian Decision Theory)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def

demo_bayesian_decision_theory
():


print_title
(
"第一部分：贝叶斯决策论"
)


print
(
"
\n
  【场景】医疗诊断：c0=健康，c1=患病"
)


P_c0

=

0.7


# P(健康)


P_c1

=

0.3


# P(患病)


P_x_given_c0

=

0.1


# 健康人出现该症状的概率


P_x_given_c1

=

0.8


# 患者出现该症状的概率



# ---- 步骤1：贝叶斯公式推导 ----


print_step
(
"步骤1：设定先验概率和似然函数"
)


print_calc
(
f
"先验概率: P(c0=健康) =
{
P_c0
}
,  P(c1=患病) =
{
P_c1
}
"
)


print_calc
(
f
"似然函数: P(x=症状|c0=健康) =
{
P_x_given_c0
}
"
)


print_calc
(
f
"          P(x=症状|c1=患病) =
{
P_x_given_c1
}
"
)


print_end
()



# ---- 步骤2：全概率公式计算 P(x) ----


print_step
(
"步骤2：全概率公式计算 P(x)"
)


print_calc
(
f
"P(x) = P(x|c0)·P(c0) + P(x|c1)·P(c1)"
)


P_x

=

P_x_given_c0

*

P_c0

+

P_x_given_c1

*

P_c1


print_calc
(
f
"     =
{
P_x_given_c0
}
×
{
P_c0
}
 +
{
P_x_given_c1
}
×
{
P_c1
}
"
)


print_calc
(
f
"     =
{
P_x_given_c0

*

P_c0
}
 +
{
P_x_given_c1

*

P_c1
}
"
)


print_result
(
f
"P(x) =
{
P_x
}
"
)


print_end
()



# ---- 步骤3：贝叶斯公式求后验 ----


print_step
(
"步骤3：贝叶斯公式 P(c|x) = P(x|c)·P(c) / P(x)"
)


P_c0_given_x

=

P_x_given_c0

*

P_c0

/

P_x


P_c1_given_x

=

P_x_given_c1

*

P_c1

/

P_x


print_calc
(
f
"P(c0=健康|x) = P(x|c0)·P(c0) / P(x)"
)


print_calc
(
f
"             =
{
P_x_given_c0
}
×
{
P_c0
}
 /
{
P_x
}
"
)


print_calc
(
f
"             =
{
P_x_given_c0

*

P_c0
}
 /
{
P_x
}
"
)


print_result
(
f
"P(健康|症状) =
{
P_c0_given_x
:
.4f
}
"
)


print_calc
(
f
""
)


print_calc
(
f
"P(c1=患病|x) = P(x|c1)·P(c1) / P(x)"
)


print_calc
(
f
"             =
{
P_x_given_c1
}
×
{
P_c1
}
 /
{
P_x
}
"
)


print_calc
(
f
"             =
{
P_x_given_c1

*

P_c1
}
 /
{
P_x
}
"
)


print_result
(
f
"P(患病|症状) =
{
P_c1_given_x
:
.4f
}
"
)


print_end
()



# ---- 步骤4：0-1 损失 MAP 决策 ----


print_step
(
"步骤4：0-1 损失下的 MAP 决策"
)


print_calc
(
f
"0-1损失: λ(正确)=0, λ(错误)=1"
)


print_calc
(
f
"此时条件风险 R(c_i|x) = 1 - P(c_i|x)"
)


print_calc
(
f
"最优决策 = argmax_c P(c|x)  （选后验概率最大的类）"
)


print_calc
(
f
""
)


print_calc
(
f
"P(健康|症状) =
{
P_c0_given_x
:
.4f
}
"
)


print_calc
(
f
"P(患病|症状) =
{
P_c1_given_x
:
.4f
}
"
)


print_calc
(
f
"因为
{
P_c1_given_x
:
.4f
}
 >
{
P_c0_given_x
:
.4f
}
"
)


map_decision

=

"患病"

if

P_c1_given_x

>

P_c0_given_x

else

"健康"


print_result
(
f
"MAP 判别结果:
{
map_decision
}
"
)


print_end
()



# ---- 步骤5：非对称损失决策 ----


print_step
(
"步骤5：非对称损失下的最小风险决策"
)


print_calc
(
f
"损失矩阵 λ[判为i][真实j]:"
)


print_calc
(
f
"                  真实: 健康(c0)  患病(c1)"
)


print_calc
(
f
"  判为健康(c0):     0         10    ← 漏诊代价=10"
)


print_calc
(
f
"  判为患病(c1):     1          0    ← 误诊代价=1"
)


print_calc
(
f
""
)


print_calc
(
f
"条件风险公式: R(判为c_i|x) = Σ_j λ_ij · P(c_j|x)"
)


print_calc
(
f
""
)


lambda_matrix

=

np
.
array
([[
0
,

10
],

[
1
,

0
]])


posteriors

=

np
.
array
([
P_c0_given_x
,

P_c1_given_x
])


R_healthy

=

lambda_matrix
[
0
]

@

posteriors


print_calc
(
f
"R(判为健康|x) = λ_00·P(c0|x) + λ_01·P(c1|x)"
)


print_calc
(
f
"              = 0×
{
P_c0_given_x
:
.4f
}
 + 10×
{
P_c1_given_x
:
.4f
}
"
)


print_calc
(
f
"              = 0 +
{
10
*
P_c1_given_x
:
.4f
}
"
)


print_result
(
f
"R(判为健康|x) =
{
R_healthy
:
.4f
}
"
)


print_calc
(
f
""
)


R_sick

=

lambda_matrix
[
1
]

@

posteriors


print_calc
(
f
"R(判为患病|x) = λ_10·P(c0|x) + λ_11·P(c1|x)"
)


print_calc
(
f
"              = 1×
{
P_c0_given_x
:
.4f
}
 + 0×
{
P_c1_given_x
:
.4f
}
"
)


print_calc
(
f
"              =
{
1
*
P_c0_given_x
:
.4f
}
 + 0"
)


print_result
(
f
"R(判为患病|x) =
{
R_sick
:
.4f
}
"
)


print_calc
(
f
""
)


asymmetric_decision

=

"患病"

if

R_sick

<

R_healthy

else

"健康"


print_calc
(
f
"比较: R(判为患病)=
{
R_sick
:
.4f
}
 < R(判为健康)=
{
R_healthy
:
.4f
}
"
)


print_result
(
f
"最小风险判别结果:
{
asymmetric_decision
}
"
)


print_calc
(
f
"→ 非对称损失下，宁可误诊也不漏诊，体现了代价敏感决策"
)


print_end
()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 第二部分：极大似然估计 (Maximum Likelihood Estimation)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def

demo_mle
():


print_title
(
"第二部分：极大似然估计 (MLE)"
)



# ======== 示例1：高斯分布 MLE ========


print
(
"
\n
  【示例1】高斯分布的极大似然估计"
)


np
.
random
.
seed
(
42
)


true_mu
,

true_sigma2

=

5.0
,

4.0


data

=

np
.
random
.
normal
(
true_mu
,

np
.
sqrt
(
true_sigma2
),

10
)


# 用小样本展示


print_step
(
"步骤1：观测数据（取前10个样本便于展示）"
)


print_calc
(
f
"真实参数: μ=
{
true_mu
}
, σ²=
{
true_sigma2
}
"
)


print_calc
(
f
"观测样本 x = [
{
', '
.
join
(
f
'
{
v
:
.2f
}
'

for

v

in

data
)
}
]"
)


print_calc
(
f
"样本数量 N =
{
len
(
data
)
}
"
)


print_end
()


print_step
(
"步骤2：写出对数似然函数"
)


print_calc
(
f
"假设 x_i ~ N(μ, σ²)"
)


print_calc
(
"似然函数: L(μ,σ²) = Π_{i=1}^N  1/√(2πσ²) · exp(-(x_i-μ)²/(2σ²))"
)


print_calc
(
"对数似然: LL(μ,σ²) = Σ_{i=1}^N [-½ln(2πσ²) - (x_i-μ)²/(2σ²)]"
)


print_calc
(
f
"        = -N/2·ln(2πσ²) - 1/(2σ²)·Σ(x_i-μ)²"
)


print_end
()


print_step
(
"步骤3：对 μ 求导，令 ∂LL/∂μ = 0"
)


print_calc
(
f
"∂LL/∂μ = 1/σ² · Σ(x_i - μ) = 0"
)


print_calc
(
f
"→ Σx_i - N·μ = 0"
)


print_calc
(
f
"→ μ̂_MLE = (1/N)·Σx_i  (样本均值)"
)


print_calc
(
f
""
)


mu_mle

=

np
.
mean
(
data
)


sum_x

=

np
.
sum
(
data
)


print_calc
(
f
"计算: Σx_i =
{
sum_x
:
.4f
}
"
)


print_calc
(
f
"      μ̂ =
{
sum_x
:
.4f
}
 /
{
len
(
data
)
}
 =
{
mu_mle
:
.4f
}
"
)


print_result
(
f
"μ̂_MLE =
{
mu_mle
:
.4f
}
  (真实值
{
true_mu
}
)"
)


print_end
()


print_step
(
"步骤4：对 σ² 求导，令 ∂LL/∂σ² = 0"
)


print_calc
(
f
"∂LL/∂σ² = -N/(2σ²) + 1/(2σ⁴)·Σ(x_i-μ̂)² = 0"
)


print_calc
(
f
"→ σ̂²_MLE = (1/N)·Σ(x_i - μ̂)²  (样本方差，有偏)"
)


print_calc
(
f
""
)


residuals

=

data

-

mu_mle


sum_sq

=

np
.
sum
(
residuals
**
2
)


sigma2_mle

=

sum_sq

/

len
(
data
)


print_calc
(
f
"计算: Σ(x_i - μ̂)² =
{
sum_sq
:
.4f
}
"
)


print_calc
(
f
"      σ̂² =
{
sum_sq
:
.4f
}
 /
{
len
(
data
)
}
 =
{
sigma2_mle
:
.4f
}
"
)


print_result
(
f
"σ̂²_MLE =
{
sigma2_mle
:
.4f
}
  (真实值
{
true_sigma2
}
)"
)


print_end
()



# 用完整100个样本再算一次


np
.
random
.
seed
(
42
)


data_full

=

np
.
random
.
normal
(
true_mu
,

np
.
sqrt
(
true_sigma2
),

100
)


print_step
(
"步骤5：增大样本量 N=100 观察 MLE 的一致性"
)


print_calc
(
f
"N=10 时: μ̂=
{
mu_mle
:
.4f
}
, σ̂²=
{
sigma2_mle
:
.4f
}
"
)


mu_100

=

np
.
mean
(
data_full
)


s2_100

=

np
.
var
(
data_full
)


print_calc
(
f
"N=100时: μ̂=
{
mu_100
:
.4f
}
, σ̂²=
{
s2_100
:
.4f
}
"
)


print_result
(
f
"样本量越大，MLE 估计越接近真实值（一致性）"
)


print_end
()



# ======== 示例2：离散分布 MLE + 拉普拉斯平滑 ========


print
(
f
"
\n

{
'─'
*
50
}
"
)


print
(
f
"
\n
  【示例2】离散分布 MLE + 拉普拉斯平滑"
)


np
.
random
.
seed
(
42
)


dice_data

=

np
.
random
.
choice
([
1
,

2
,

3
,

4
,

5
,

6
],

size
=
20
,


p
=
[
0.1
,

0.15
,

0.2
,

0.25
,

0.15
,

0.15
])


counts

=

Counter
(
dice_data
)


N

=

len
(
dice_data
)


K

=

6


print_step
(
"步骤1：观测数据"
)


print_calc
(
f
"掷骰子
{
N
}
 次，结果:
{
list
(
dice_data
)
}
"
)


print_calc
(
f
"各面计数:
{
dict
(
sorted
(
counts
.
items
()))
}
"
)



# 检查是否有缺失面


missing

=

[
k

for

k

in

range
(
1
,

7
)

if

k

not

in

counts
]


if

missing
:


print_calc
(
f
"注意: 面
{
missing
}
 从未出现!"
)


print_end
()


print_step
(
"步骤2：MLE 估计 P(x=k) = N_k / N"
)


print_calc
(
f
"原理: 使似然函数 L = Π P(x=k)^
{
'
{N_k}
'
}
 最大"
)


print_calc
(
f
"等价于最大化对数似然 LL = Σ N_k · ln P(x=k)"
)


print_calc
(
f
"约束 Σ P(x=k)=1，用拉格朗日乘子法求解:"
)


print_calc
(
f
"→ P̂(x=k) = N_k / N"
)


print_calc
(
f
""
)


for

k

in

range
(
1
,

7
):


nk

=

counts
.
get
(
k
,

0
)


p

=

nk

/

N


print_calc
(
f
"P̂(x=
{
k
}
) = N_
{
k
}
/N =
{
nk
}
/
{
N
}
 =
{
p
:
.4f
}
"

+


(
"  ⚠ 零概率!"

if

nk

==

0

else

""
))


if

missing
:


print_result
(
f
"问题: 未出现的面概率为0，会导致连乘为0（零概率陷阱）"
)


print_end
()


print_step
(
"步骤3：拉普拉斯平滑 (加1平滑)"
)


print_calc
(
f
"思想: 假设每个取值至少出现1次"
)


print_calc
(
f
"P̂(x=k) = (N_k + 1) / (N + K)"
)


print_calc
(
f
"其中 K=
{
K
}
 为取值个数（骰子6面）"
)


print_calc
(
f
""
)


for

k

in

range
(
1
,

7
):


nk

=

counts
.
get
(
k
,

0
)


p

=

(
nk

+

1
)

/

(
N

+

K
)


print_calc
(
f
"P̂(x=
{
k
}
) = (
{
nk
}
+1)/(
{
N
}
+
{
K
}
) =
{
nk
+
1
}
/
{
N
+
K
}
 =
{
p
:
.4f
}
"
)


print_result
(
f
"所有概率 > 0，且仍然满足 Σ P̂(x=k) = 1"
)


total

=

sum
((
counts
.
get
(
k
,

0
)

+

1
)

/

(
N

+

K
)

for

k

in

range
(
1
,

7
))


print_calc
(
f
"验证: Σ P̂(x=k) =
{
total
:
.4f
}
"
)


print_end
()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 第三部分：朴素贝叶斯分类器 (Naive Bayes Classifier)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class

NaiveBayesDiscrete
:


"""离散型朴素贝叶斯分类器"""


def

__init__
(
self
,

laplace_smooth
=
True
):


self
.
laplace_smooth

=

laplace_smooth


self
.
classes

=

None


self
.
prior

=

{}


self
.
likelihood

=

{}


self
.
feature_values

=

{}



# 保存训练统计信息用于展示


self
.
class_counts

=

{}


self
.
cond_counts

=

{}


def

fit
(
self
,

X
,

y
):


N

=

len
(
y
)


self
.
classes

=

np
.
unique
(
y
)


n_classes

=

len
(
self
.
classes
)


n_features

=

X
.
shape
[
1
]


for

j

in

range
(
n_features
):


self
.
feature_values
[
j
]

=

np
.
unique
(
X
[:,

j
])


for

c

in

self
.
classes
:


Nc

=

np
.
sum
(
y

==

c
)


self
.
class_counts
[
c
]

=

Nc


if

self
.
laplace_smooth
:


self
.
prior
[
c
]

=

(
Nc

+

1
)

/

(
N

+

n_classes
)


else
:


self
.
prior
[
c
]

=

Nc

/

N


self
.
likelihood
[
c
]

=

{}


self
.
cond_counts
[
c
]

=

{}


X_c

=

X
[
y

==

c
]


for

j

in

range
(
n_features
):


self
.
likelihood
[
c
][
j
]

=

{}


self
.
cond_counts
[
c
][
j
]

=

{}


Si

=

len
(
self
.
feature_values
[
j
])


for

v

in

self
.
feature_values
[
j
]:


Ncv

=

np
.
sum
(
X_c
[:,

j
]

==

v
)


self
.
cond_counts
[
c
][
j
][
v
]

=

Ncv


if

self
.
laplace_smooth
:


self
.
likelihood
[
c
][
j
][
v
]

=

(
Ncv

+

1
)

/

(
Nc

+

Si
)


else
:


self
.
likelihood
[
c
][
j
][
v
]

=

Ncv

/

Nc

if

Nc

>

0

else

0


def

predict_single_verbose
(
self
,

x
,

feature_names
=
None
):


"""对单个样本进行预测并打印详细计算过程"""


if

feature_names

is

None
:


feature_names

=

[
f
"x
{
j
}
"

for

j

in

range
(
len
(
x
))]


print_calc
(
f
"待分类样本:
{
dict
(
zip
(
feature_names
,

x
))
}
"
)


print_calc
(
f
""
)


best_c

=

None


best_log

=

-
np
.
inf


for

c

in

self
.
classes
:


class_name

=

"好瓜"

if

c

==

1

else

"坏瓜"


print_calc
(
f
"── 计算 P(c=
{
class_name
}
) · Π P(x_i|c=
{
class_name
}
) ──"
)


log_post

=

np
.
log
(
self
.
prior
[
c
])


print_calc
(
f
"  ln P(c=
{
class_name
}
) = ln(
{
self
.
prior
[
c
]
:
.4f
}
) =
{
log_post
:
.4f
}
"
)


for

j
,

v

in

enumerate
(
x
):


prob

=

self
.
likelihood
[
c
][
j
]
.
get
(
v
,

1e-10
)


log_p

=

np
.
log
(
prob
)


Nc

=

self
.
class_counts
[
c
]


Ncv

=

self
.
cond_counts
[
c
][
j
]
.
get
(
v
,

0
)


Si

=

len
(
self
.
feature_values
[
j
])


if

self
.
laplace_smooth
:


print_calc
(
f
"  ln P(
{
feature_names
[
j
]
}
=
{
v
}
|
{
class_name
}
)"


f
" = ln((
{
Ncv
}
+1)/(
{
Nc
}
+
{
Si
}
))"


f
" = ln(
{
prob
:
.4f
}
) =
{
log_p
:
.4f
}
"
)


else
:


print_calc
(
f
"  ln P(
{
feature_names
[
j
]
}
=
{
v
}
|
{
class_name
}
)"


f
" = ln(
{
Ncv
}
/
{
Nc
}
)"


f
" = ln(
{
prob
:
.4f
}
) =
{
log_p
:
.4f
}
"
)


log_post

+=

log_p


print_calc
(
f
"  总计:
{
log_post
:
.4f
}
"
)


print_calc
(
f
"  即 P(c=
{
class_name
}
|x) ∝ exp(
{
log_post
:
.4f
}
) =
{
np
.
exp
(
log_post
)
:
.6e
}
"
)


print_calc
(
f
""
)


if

log_post

>

best_log
:


best_log

=

log_post


best_c

=

c


class_name

=

"好瓜"

if

best_c

==

1

else

"坏瓜"


print_result
(
f
"选择后验概率最大的类别:
{
class_name
}
 (c=
{
best_c
}
)"
)


return

best_c


def

predict
(
self
,

X
):


predictions

=

[]


for

x

in

X
:


posteriors

=

{}


for

c

in

self
.
classes
:


log_post

=

np
.
log
(
self
.
prior
[
c
])


for

j
,

v

in

enumerate
(
x
):


prob

=

self
.
likelihood
[
c
][
j
]
.
get
(
v
,

1e-10
)


log_post

+=

np
.
log
(
prob
)


posteriors
[
c
]

=

log_post


predictions
.
append
(
max
(
posteriors
,

key
=
posteriors
.
get
))


return

np
.
array
(
predictions
)

class

GaussianNaiveBayes
:


"""高斯朴素贝叶斯分类器（连续特征）"""


def

__init__
(
self
):


self
.
classes

=

None


self
.
prior

=

{}


self
.
mean

=

{}


self
.
var

=

{}


self
.
class_counts

=

{}


def

fit
(
self
,

X
,

y
):


N

=

len
(
y
)


self
.
classes

=

np
.
unique
(
y
)


for

c

in

self
.
classes
:


X_c

=

X
[
y

==

c
]


self
.
class_counts
[
c
]

=

len
(
X_c
)


self
.
prior
[
c
]

=

len
(
X_c
)

/

N


self
.
mean
[
c
]

=

np
.
mean
(
X_c
,

axis
=
0
)


self
.
var
[
c
]

=

np
.
var
(
X_c
,

axis
=
0
)

+

1e-9


def

_gaussian_pdf
(
self
,

x
,

mean
,

var
):


return

(
1.0

/

np
.
sqrt
(
2

*

np
.
pi

*

var
))

*

np
.
exp
(
-
(
x

-

mean
)

**

2

/

(
2

*

var
))


def

predict_single_verbose
(
self
,

x
):


"""对单个样本进行预测并打印详细计算过程"""


print_calc
(
f
"待分类样本: x = [
{
x
[
0
]
:
.3f
}
,
{
x
[
1
]
:
.3f
}
]"
)


print_calc
(
f
""
)


best_c

=

None


best_log

=

-
np
.
inf


for

c

in

self
.
classes
:


print_calc
(
f
"── 计算类别 c=
{
c
}
 ──"
)


log_post

=

np
.
log
(
self
.
prior
[
c
])


print_calc
(
f
"  ln P(c=
{
c
}
) = ln(
{
self
.
prior
[
c
]
:
.4f
}
) =
{
log_post
:
.4f
}
"
)


for

j

in

range
(
len
(
x
)):


mu

=

self
.
mean
[
c
][
j
]


sigma2

=

self
.
var
[
c
][
j
]


pdf

=

self
.
_gaussian_pdf
(
x
[
j
],

mu
,

sigma2
)


log_p

=

np
.
log
(
pdf

+

1e-300
)


print_calc
(
f
"  P(x
{
j
+
1
}
=
{
x
[
j
]
:
.3f
}
|c=
{
c
}
):"
)


print_calc
(
f
"    N(x|μ=
{
mu
:
.3f
}
, σ²=
{
sigma2
:
.3f
}
)"
)


print_calc
(
f
"    = 1/√(2π·
{
sigma2
:
.3f
}
) · exp(-(
{
x
[
j
]
:
.3f
}
-
{
mu
:
.3f
}
)²/(2·
{
sigma2
:
.3f
}
))"
)


print_calc
(
f
"    =
{
pdf
:
.6e
}
"
)


print_calc
(
f
"    ln =
{
log_p
:
.4f
}
"
)


log_post

+=

log_p


print_calc
(
f
"  总计 ln P(c=
{
c
}
|x) ∝
{
log_post
:
.4f
}
"
)


print_calc
(
f
""
)


if

log_post

>

best_log
:


best_log

=

log_post


best_c

=

c


print_result
(
f
"选择后验概率最大的类别: c=
{
best_c
}
"
)


return

best_c


def

predict
(
self
,

X
):


predictions

=

[]


for

x

in

X
:


posteriors

=

{}


for

c

in

self
.
classes
:


log_post

=

np
.
log
(
self
.
prior
[
c
])


for

j

in

range
(
len
(
x
)):


pdf

=

self
.
_gaussian_pdf
(
x
[
j
],

self
.
mean
[
c
][
j
],

self
.
var
[
c
][
j
])


log_post

+=

np
.
log
(
pdf

+

1e-300
)


posteriors
[
c
]

=

log_post


predictions
.
append
(
max
(
posteriors
,

key
=
posteriors
.
get
))


return

np
.
array
(
predictions
)

def

demo_naive_bayes
():


print_title
(
"第三部分：朴素贝叶斯分类器"
)



# ---- 3.1 离散型朴素贝叶斯 ----


print
(
"
\n
  【3.1】离散型朴素贝叶斯"
)


print
(
"  核心假设: P(x|c) = Π P(x_i|c)  (属性条件独立)"
)


X
,

y

=

generate_discrete_dataset
(
200
)


X_train
,

X_test
,

y_train
,

y_test

=

train_test_split
(
X
,

y
)


feature_names

=

[
"色泽"
,

"根蒂"
,

"敲声"
]


value_names

=

{


0
:

{
0
:

"乌黑"
,

1
:

"浅白"
,

2
:

"青绿"
},


1
:

{
0
:

"蜷缩"
,

1
:

"稍蜷"
,

2
:

"硬挺"
},


2
:

{
0
:

"浊响"
,

1
:

"沉闷"
,

2
:

"清脆"
},


}


nb

=

NaiveBayesDiscrete
(
laplace_smooth
=
True
)


nb
.
fit
(
X_train
,

y_train
)



# 展示训练过程


N_train

=

len
(
y_train
)


n_classes

=

len
(
nb
.
classes
)


print_step
(
"步骤1：统计训练数据"
)


print_calc
(
f
"训练集大小 N =
{
N_train
}
"
)


for

c

in

nb
.
classes
:


name

=

"好瓜"

if

c

==

1

else

"坏瓜"


print_calc
(
f
"|D_
{
name
}
| =
{
nb
.
class_counts
[
c
]
}
"
)


print_end
()


print_step
(
"步骤2：计算先验概率 P(c)  [拉普拉斯平滑]"
)


print_calc
(
f
"P(c) = (|D_c| + 1) / (N + K),  K=类别数=
{
n_classes
}
"
)


for

c

in

nb
.
classes
:


name

=

"好瓜"

if

c

==

1

else

"坏瓜"


Nc

=

nb
.
class_counts
[
c
]


print_calc
(
f
"P(
{
name
}
) = (
{
Nc
}
+1) / (
{
N_train
}
+
{
n_classes
}
) =
{
Nc
+
1
}
/
{
N_train
+
n_classes
}
 =
{
nb
.
prior
[
c
]
:
.4f
}
"
)


print_end
()


print_step
(
"步骤3：计算条件概率 P(x_i=v|c)  [拉普拉斯平滑]"
)


print_calc
(
f
"P(x_i=v|c) = (|D_
{{
c,x_i=v
}}
| + 1) / (|D_c| + S_i)"
)


print_calc
(
f
"其中 S_i = 第i个特征的取值数"
)


print_calc
(
f
""
)


for

c

in

[
1
,

0
]:


# 先展示好瓜


name

=

"好瓜"

if

c

==

1

else

"坏瓜"


Nc

=

nb
.
class_counts
[
c
]


print_calc
(
f
"类别:
{
name
}
 (|D_
{
name
}
|=
{
Nc
}
)"
)


for

j
,

fname

in

enumerate
(
feature_names
):


Si

=

len
(
nb
.
feature_values
[
j
])


parts

=

[]


for

v

in

sorted
(
nb
.
likelihood
[
c
][
j
]
.
keys
()):


Ncv

=

nb
.
cond_counts
[
c
][
j
][
v
]


prob

=

nb
.
likelihood
[
c
][
j
][
v
]


vname

=

value_names
[
j
][
v
]


parts
.
append
(
f
"P(
{
fname
}
=
{
vname
}
|
{
name
}
)=(
{
Ncv
}
+1)/(
{
Nc
}
+
{
Si
}
)=
{
prob
:
.3f
}
"
)


print_calc
(
f
"
{
', '
.
join
(
parts
)
}
"
)


print_calc
(
f
""
)


print_end
()



# 对一个测试样本详细计算


print_step
(
"步骤4：对测试样本进行分类（详细计算）"
)


print_calc
(
f
"分类公式: h(x) = argmax_c  ln P(c) + Σ ln P(x_i|c)"
)


print_calc
(
f
"（取对数避免概率连乘导致的下溢问题）"
)


print_calc
(
f
""
)


sample_x

=

X_test
[
0
]


nb
.
predict_single_verbose
(
sample_x
,

feature_names
)


true_label

=

"好瓜"

if

y_test
[
0
]

==

1

else

"坏瓜"


print_calc
(
f
"真实标签:
{
true_label
}
"
)


print_end
()



# 整体测试


y_pred

=

nb
.
predict
(
X_test
)


acc

=

accuracy
(
y_test
,

y_pred
)


print_step
(
"步骤5：整体测试集评估"
)


correct

=

np
.
sum
(
y_pred

==

y_test
)


print_calc
(
f
"测试集大小:
{
len
(
y_test
)
}
"
)


print_calc
(
f
"预测正确数:
{
correct
}
"
)


print_calc
(
f
"准确率 =
{
correct
}
/
{
len
(
y_test
)
}
 =
{
acc
:
.4f
}
"
)


print_end
()



# ---- 3.2 高斯朴素贝叶斯 ----


print
(
f
"
\n

{
'─'
*
50
}
"
)


print
(
"
\n
  【3.2】高斯朴素贝叶斯（连续特征）"
)


print
(
"  假设: P(x_i|c) ~ N(μ_{c,i}, σ²_{c,i})"
)


X_cont
,

y_cont

=

generate_continuous_dataset
(
300
)


X_tr
,

X_te
,

y_tr
,

y_te

=

train_test_split
(
X_cont
,

y_cont
)


gnb

=

GaussianNaiveBayes
()


gnb
.
fit
(
X_tr
,

y_tr
)


print_step
(
"步骤1：MLE 估计每个类别下每个特征的 μ 和 σ²"
)


for

c

in

gnb
.
classes
:


Nc

=

gnb
.
class_counts
[
c
]


print_calc
(
f
"类别 c=
{
c
}
:
{
Nc
}
 个样本"
)


for

j

in

range
(
2
):


print_calc
(
f
"  特征 x
{
j
+
1
}
: μ̂ = Σx/
{
Nc
}
 =
{
gnb
.
mean
[
c
][
j
]
:
.4f
}
, "


f
"σ̂² = Σ(x-μ̂)²/
{
Nc
}
 =
{
gnb
.
var
[
c
][
j
]
:
.4f
}
"
)


print_end
()


print_step
(
"步骤2：对一个测试样本详细分类"
)


sample_x

=

X_te
[
0
]


gnb
.
predict_single_verbose
(
sample_x
)


true_label

=

y_te
[
0
]


print_calc
(
f
"真实标签: c=
{
true_label
}
"
)


print_end
()


y_pred_g

=

gnb
.
predict
(
X_te
)


acc_g

=

accuracy
(
y_te
,

y_pred_g
)


print_step
(
"步骤3：整体评估"
)


print_calc
(
f
"测试集准确率:
{
accuracy
(
y_te
,

y_pred_g
)
:
.4f
}
"
)


print_end
()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 第四部分：半朴素贝叶斯分类器 (Semi-Naive Bayes)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class

SPODE
:


"""SPODE (Super-Parent One-Dependence Estimator)"""


def

__init__
(
self
,

parent_idx
=
0
):


self
.
parent_idx

=

parent_idx


self
.
classes

=

None


self
.
prior

=

{}


self
.
parent_prob

=

{}


self
.
cond_prob

=

{}


self
.
feature_values

=

{}



# 保存统计量


self
.
joint_counts

=

{}


def

fit
(
self
,

X
,

y
):


N

=

len
(
y
)


self
.
classes

=

np
.
unique
(
y
)


n_features

=

X
.
shape
[
1
]


pa

=

self
.
parent_idx


for

j

in

range
(
n_features
):


self
.
feature_values
[
j
]

=

np
.
unique
(
X
[:,

j
])


for

c

in

self
.
classes
:


X_c

=

X
[
y

==

c
]


Nc

=

len
(
X_c
)


self
.
prior
[
c
]

=

(
Nc

+

1
)

/

(
N

+

len
(
self
.
classes
))


self
.
parent_prob
[
c
]

=

{}


S_pa

=

len
(
self
.
feature_values
[
pa
])


for

v

in

self
.
feature_values
[
pa
]:


count

=

np
.
sum
(
X_c
[:,

pa
]

==

v
)


self
.
parent_prob
[
c
][
v
]

=

(
count

+

1
)

/

(
Nc

+

S_pa
)


self
.
cond_prob
[
c
]

=

{}


self
.
joint_counts
[
c
]

=

{}


for

j

in

range
(
n_features
):


if

j

==

pa
:


continue


self
.
cond_prob
[
c
][
j
]

=

{}


self
.
joint_counts
[
c
][
j
]

=

{}


S_j

=

len
(
self
.
feature_values
[
j
])


for

v_pa

in

self
.
feature_values
[
pa
]:


mask

=

X_c
[:,

pa
]

==

v_pa


N_c_pa

=

np
.
sum
(
mask
)


self
.
cond_prob
[
c
][
j
][
v_pa
]

=

{}


self
.
joint_counts
[
c
][
j
][
v_pa
]

=

{
"total"
:

N_c_pa
}


for

u

in

self
.
feature_values
[
j
]:


count

=

np
.
sum
(
X_c
[
mask
,

j
]

==

u
)


self
.
cond_prob
[
c
][
j
][
v_pa
][
u
]

=

(
count

+

1
)

/

(
N_c_pa

+

S_j
)


self
.
joint_counts
[
c
][
j
][
v_pa
][
u
]

=

count


def

predict_log_prob
(
self
,

X
):


pa

=

self
.
parent_idx


results

=

[]


for

x

in

X
:


log_probs

=

{}


for

c

in

self
.
classes
:


lp

=

np
.
log
(
self
.
prior
[
c
])


lp

+=

np
.
log
(
self
.
parent_prob
[
c
]
.
get
(
x
[
pa
],

1e-10
))


for

j

in

range
(
len
(
x
)):


if

j

==

pa
:


continue


prob

=

self
.
cond_prob
[
c
][
j
]
.
get
(
x
[
pa
],

{})
.
get
(
x
[
j
],

1e-10
)


lp

+=

np
.
log
(
prob
)


log_probs
[
c
]

=

lp


results
.
append
(
log_probs
)


return

results

class

AODE
:


"""AODE (Averaged One-Dependence Estimator)"""


def

__init__
(
self
,

min_count
=
1
):


self
.
min_count

=

min_count


self
.
spodes

=

[]


self
.
valid_parents

=

[]


def

fit
(
self
,

X
,

y
):


n_features

=

X
.
shape
[
1
]


self
.
spodes

=

[]


self
.
valid_parents

=

[]


for

pa_idx

in

range
(
n_features
):


values
,

counts

=

np
.
unique
(
X
[:,

pa_idx
],

return_counts
=
True
)


if

np
.
min
(
counts
)

>=

self
.
min_count
:


spode

=

SPODE
(
parent_idx
=
pa_idx
)


spode
.
fit
(
X
,

y
)


self
.
spodes
.
append
(
spode
)


self
.
valid_parents
.
append
(
pa_idx
)


def

predict
(
self
,

X
):


if

not

self
.
spodes
:


raise

ValueError
(
"没有合格的超父属性!"
)


classes

=

self
.
spodes
[
0
]
.
classes


predictions

=

[]


for

x

in

X
:


avg_scores

=

{
c
:

0.0

for

c

in

classes
}


for

spode

in

self
.
spodes
:


log_probs

=

spode
.
predict_log_prob
(
x
.
reshape
(
1
,

-
1
))[
0
]


for

c

in

classes
:


avg_scores
[
c
]

+=

np
.
exp
(
log_probs
[
c
])


predictions
.
append
(
max
(
avg_scores
,

key
=
avg_scores
.
get
))


return

np
.
array
(
predictions
)


def

predict_single_verbose
(
self
,

x
,

feature_names
):


"""详细展示 AODE 对单个样本的分类过程"""


classes

=

self
.
spodes
[
0
]
.
classes


avg_scores

=

{
c
:

0.0

for

c

in

classes
}


for

si
,

spode

in

enumerate
(
self
.
spodes
):


pa

=

spode
.
parent_idx


pa_name

=

feature_names
[
pa
]


print_calc
(
f
"── SPODE
{
si
+
1
}
: 超父=
{
pa_name
}
(x
{
pa
}
=
{
x
[
pa
]
}
) ──"
)


log_probs

=

spode
.
predict_log_prob
(
x
.
reshape
(
1
,

-
1
))[
0
]


for

c

in

classes
:


cname

=

"好瓜"

if

c

==

1

else

"坏瓜"



# 展示公式


parts

=

[
f
"P(
{
pa_name
}
=
{
x
[
pa
]
}
|
{
cname
}
)"
]


for

j

in

range
(
len
(
x
)):


if

j

==

pa
:


continue


parts
.
append
(
f
"P(
{
feature_names
[
j
]
}
=
{
x
[
j
]
}
|
{
cname
}
,
{
pa_name
}
=
{
x
[
pa
]
}
)"
)


formula

=

" · "
.
join
([
f
"P(
{
cname
}
)"
]

+

parts
)


prob_val

=

np
.
exp
(
log_probs
[
c
])


print_calc
(
f
"
{
cname
}
:
{
formula
}
"
)


print_calc
(
f
"         =
{
prob_val
:
.6e
}
"
)


avg_scores
[
c
]

+=

prob_val


print_calc
(
f
""
)


print_calc
(
f
"── 汇总：对所有SPODE求和 ──"
)


for

c

in

classes
:


cname

=

"好瓜"

if

c

==

1

else

"坏瓜"


print_calc
(
f
"
{
cname
}
: Σ =
{
avg_scores
[
c
]
:
.6e
}
"
)


pred

=

max
(
avg_scores
,

key
=
avg_scores
.
get
)


pname

=

"好瓜"

if

pred

==

1

else

"坏瓜"


print_result
(
f
"AODE 预测:
{
pname
}
"
)


return

pred

def

demo_semi_naive_bayes
():


print_title
(
"第四部分：半朴素贝叶斯分类器"
)


print
(
"""

  朴素贝叶斯假设: P(x|c) = Π P(x_i|c)  （完全独立）

  半朴素贝叶斯:   允许部分属性间存在依赖关系

  SPODE: 选一个"超父"属性 x_pa

         P(x|c) = P(x_pa|c) · Π_{i≠pa} P(x_i | c, x_pa)

         每个非超父属性不仅依赖类别c，还依赖超父x_pa

  AODE:  对所有合格的超父取平均，消除选择偏差

    """
)


X
,

y

=

generate_discrete_dataset
(
300
)


X_train
,

X_test
,

y_train
,

y_test

=

train_test_split
(
X
,

y
)


feature_names

=

[
"色泽"
,

"根蒂"
,

"敲声"
]



# 朴素贝叶斯基线


nb

=

NaiveBayesDiscrete
()


nb
.
fit
(
X_train
,

y_train
)



# AODE


aode

=

AODE
(
min_count
=
1
)


aode
.
fit
(
X_train
,

y_train
)


print_step
(
"步骤1：AODE 构建 — 为每个特征构建一个 SPODE"
)


for

i
,

pa_idx

in

enumerate
(
aode
.
valid_parents
):


print_calc
(
f
"SPODE
{
i
+
1
}
: 超父 =
{
feature_names
[
pa_idx
]
}
"
)


spode

=

aode
.
spodes
[
i
]



# 展示部分条件概率


c

=

1


# 好瓜


pa_v

=

2


# 取一个超父取值


print_calc
(
f
"  示例: P(·|好瓜,
{
feature_names
[
pa_idx
]
}
=
{
pa_v
}
):"
)


for

j

in

range
(
3
):


if

j

==

pa_idx
:


continue


probs

=

[]


for

u

in

sorted
(
spode
.
cond_prob
[
c
][
j
]
.
get
(
pa_v
,

{})
.
keys
()):


p

=

spode
.
cond_prob
[
c
][
j
][
pa_v
][
u
]


cnt

=

spode
.
joint_counts
[
c
][
j
][
pa_v
]
.
get
(
u
,

0
)


total

=

spode
.
joint_counts
[
c
][
j
][
pa_v
][
"total"
]


Si

=

len
(
spode
.
feature_values
[
j
])


probs
.
append
(
f
"P(
{
feature_names
[
j
]
}
=
{
u
}
)=(
{
cnt
}
+1)/(
{
total
}
+
{
Si
}
)=
{
p
:
.3f
}
"
)


print_calc
(
f
"
{
', '
.
join
(
probs
)
}
"
)


print_end
()



# 对一个测试样本详细分类


print_step
(
"步骤2：AODE 对测试样本的分类过程"
)


sample_x

=

X_test
[
0
]


aode
.
predict_single_verbose
(
sample_x
,

feature_names
)


true_label

=

"好瓜"

if

y_test
[
0
]

==

1

else

"坏瓜"


print_calc
(
f
"真实标签:
{
true_label
}
"
)


print_end
()



# 比较


nb_acc

=

accuracy
(
y_test
,

nb
.
predict
(
X_test
))


aode_acc

=

accuracy
(
y_test
,

aode
.
predict
(
X_test
))


print_step
(
"步骤3：与朴素贝叶斯对比"
)


print_calc
(
f
"朴素贝叶斯准确率:
{
nb_acc
:
.4f
}
"
)


print_calc
(
f
"AODE 准确率:
{
aode_acc
:
.4f
}
"
)


print_calc
(
f
"AODE 超父数量:
{
len
(
aode
.
valid_parents
)
}
"
)


print_result
(
f
"AODE 通过考虑属性间依赖，可能提升分类性能"
)


print_end
()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 第五部分：贝叶斯网 (Bayesian Network)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class

SimpleBayesianNetwork
:


"""简单贝叶斯网络"""


def

__init__
(
self
):


self
.
nodes

=

[]


self
.
parents

=

{}


self
.
cpt

=

{}


self
.
node_values

=

{}


def

add_node
(
self
,

name
,

values
,

parents
=
None
,

cpt
=
None
):


self
.
nodes
.
append
(
name
)


self
.
node_values
[
name
]

=

values


self
.
parents
[
name
]

=

parents

or

[]


self
.
cpt
[
name
]

=

cpt

or

{}


def

get_prob
(
self
,

node
,

value
,

evidence
):


parent_names

=

self
.
parents
[
node
]


if

not

parent_names
:


return

self
.
cpt
[
node
]
.
get
(
value
,

0
)


else
:


parent_values

=

tuple
(
evidence
[
p
]

for

p

in

parent_names
)


return

self
.
cpt
[
node
]
.
get
(
parent_values
,

{})
.
get
(
value
,

0
)


def

joint_probability
(
self
,

assignment
):


prob

=

1.0


for

node

in

self
.
nodes
:


p

=

self
.
get_prob
(
node
,

assignment
[
node
],

assignment
)


prob

*=

p


return

prob


def

joint_probability_verbose
(
self
,

assignment
,

indent
=
"  │  "
):


"""计算联合概率并打印每一步"""


prob

=

1.0


parts

=

[]


for

node

in

self
.
nodes
:


p

=

self
.
get_prob
(
node
,

assignment
[
node
],

assignment
)


parent_names

=

self
.
parents
[
node
]


if

parent_names
:


parent_vals

=

","
.
join
(
f
"
{
pn
}
=
{
assignment
[
pn
]
}
"

for

pn

in

parent_names
)


desc

=

f
"P(
{
node
}
=
{
assignment
[
node
]
}
|
{
parent_vals
}
)=
{
p
:
.4f
}
"


else
:


desc

=

f
"P(
{
node
}
=
{
assignment
[
node
]
}
)=
{
p
:
.4f
}
"


parts
.
append
(
desc
)


prob

*=

p


return

prob
,

parts


def

inference_enumeration_verbose
(
self
,

query_node
,

evidence
,

node_labels
=
None
):


"""精确推理（枚举法）并打印详细过程"""


hidden

=

[
n

for

n

in

self
.
nodes

if

n

!=

query_node

and

n

not

in

evidence
]


query_values

=

self
.
node_values
[
query_node
]


if

node_labels

is

None
:


node_labels

=

{}


ev_str

=

", "
.
join
(
f
"
{
k
}
=
{
v
}
"

for

k
,

v

in

evidence
.
items
())


print_calc
(
f
"查询: P(
{
query_node
}
 |
{
ev_str
}
)"
)


print_calc
(
f
"隐变量:
{
hidden

if

hidden

else

'无'
}
"
)


print_calc
(
f
""
)


print_calc
(
f
"方法: 对隐变量的所有取值组合求和"
)


print_calc
(
f
"P(
{
query_node
}
=v|evidence) ∝ Σ_hidden P(所有变量)"
)


print_calc
(
f
""
)


result

=

{}


for

qv

in

query_values
:


total

=

0.0


qv_label

=

node_labels
.
get
(
query_node
,

{})
.
get
(
qv
,

qv
)


print_calc
(
f
"──
{
query_node
}
=
{
qv
}
(
{
qv_label
}
) ──"
)


if

hidden
:


hidden_combos

=

self
.
_enumerate_combos
(
hidden
)


else
:


hidden_combos

=

[{}]


for

combo

in

hidden_combos
:


assignment

=

{
**
evidence
,

query_node
:

qv
,

**
combo
}


jp
,

parts

=

self
.
joint_probability_verbose
(
assignment
)


if

hidden
:


combo_str

=

", "
.
join
(
f
"
{
k
}
=
{
v
}
"

for

k
,

v

in

combo
.
items
())


print_calc
(
f
"
{
combo_str
}
:"
)


print_calc
(
f
"    = "

+

" × "
.
join
(
parts
))


print_calc
(
f
"    =
{
jp
:
.6e
}
"
)


else
:


print_calc
(
f
"  = "

+

" × "
.
join
(
parts
))


print_calc
(
f
"  =
{
jp
:
.6e
}
"
)


total

+=

jp


print_calc
(
f
"  小计:
{
total
:
.6e
}
"
)


print_calc
(
f
""
)


result
[
qv
]

=

total



# 归一化


Z

=

sum
(
result
.
values
())


print_calc
(
f
"归一化因子 Z =
{
Z
:
.6e
}
"
)


print_calc
(
f
""
)


for

qv

in

query_values
:


result
[
qv
]

/=

Z


qv_label

=

node_labels
.
get
(
query_node
,

{})
.
get
(
qv
,

qv
)


print_result
(
f
"P(
{
query_node
}
=
{
qv
}
(
{
qv_label
}
) |
{
ev_str
}
) =
{
result
[
qv
]
:
.4f
}
"
)


return

result


def

inference_enumeration
(
self
,

query_node
,

evidence
):


hidden

=

[
n

for

n

in

self
.
nodes

if

n

!=

query_node

and

n

not

in

evidence
]


query_values

=

self
.
node_values
[
query_node
]


result

=

{}


for

qv

in

query_values
:


total

=

0.0


if

hidden
:


hidden_combos

=

self
.
_enumerate_combos
(
hidden
)


else
:


hidden_combos

=

[{}]


for

combo

in

hidden_combos
:


assignment

=

{
**
evidence
,

query_node
:

qv
,

**
combo
}


total

+=

self
.
joint_probability
(
assignment
)


result
[
qv
]

=

total


Z

=

sum
(
result
.
values
())


if

Z

>

0
:


for

qv

in

query_values
:


result
[
qv
]

/=

Z


return

result


def

_enumerate_combos
(
self
,

variables
):


if

not

variables
:


return

[{}]


var

=

variables
[
0
]


rest_combos

=

self
.
_enumerate_combos
(
variables
[
1
:])


combos

=

[]


for

v

in

self
.
node_values
[
var
]:


for

rc

in

rest_combos
:


combos
.
append
({
var
:

v
,

**
rc
})


return

combos

def

demo_bayesian_network
():


print_title
(
"第五部分：贝叶斯网"
)


print
(
"""

  贝叶斯网 = 有向无环图(DAG) + 条件概率表(CPT)

  核心分解: P(x1,...,xn) = Π P(x_i | parents(x_i))

  构建经典"学生网络":

    难度(D) ──→ 成绩(G) ←── 智力(I)

                  │              │

                  ↓              ↓

               推荐信(L)       SAT(S)

    """
)


bn

=

SimpleBayesianNetwork
()


bn
.
add_node
(
"D"
,

[
0
,

1
],

parents
=
[],

cpt
=
{
0
:

0.6
,

1
:

0.4
})


bn
.
add_node
(
"I"
,

[
0
,

1
],

parents
=
[],

cpt
=
{
0
:

0.7
,

1
:

0.3
})


bn
.
add_node
(
"G"
,

[
0
,

1
,

2
],

parents
=
[
"D"
,

"I"
],

cpt
=
{


(
0
,

0
):

{
0
:

0.3
,

1
:

0.4
,

2
:

0.3
},


(
0
,

1
):

{
0
:

0.05
,

1
:

0.25
,

2
:

0.7
},


(
1
,

0
):

{
0
:

0.5
,

1
:

0.3
,

2
:

0.2
},


(
1
,

1
):

{
0
:

0.1
,

1
:

0.3
,

2
:

0.6
},


})


bn
.
add_node
(
"S"
,

[
0
,

1
],

parents
=
[
"I"
],

cpt
=
{


(
0
,):

{
0
:

0.8
,

1
:

0.2
},


(
1
,):

{
0
:

0.2
,

1
:

0.8
},


})


bn
.
add_node
(
"L"
,

[
0
,

1
],

parents
=
[
"G"
],

cpt
=
{


(
0
,):

{
0
:

0.9
,

1
:

0.1
},


(
1
,):

{
0
:

0.4
,

1
:

0.6
},


(
2
,):

{
0
:

0.05
,

1
:

0.95
},


})


node_labels

=

{


"D"
:

{
0
:

"简单"
,

1
:

"困难"
},


"I"
:

{
0
:

"低"
,

1
:

"高"
},


"G"
:

{
0
:

"差"
,

1
:

"中"
,

2
:

"优"
},


"S"
:

{
0
:

"低"
,

1
:

"高"
},


"L"
:

{
0
:

"弱"
,

1
:

"强"
},


}



# 展示 CPT


print_step
(
"步骤1：条件概率表 (CPT)"
)


print_calc
(
f
"P(D): P(简单)=0.6, P(困难)=0.4"
)


print_calc
(
f
"P(I): P(低)=0.7,  P(高)=0.3"
)


print_calc
(
f
""
)


print_calc
(
f
"P(G|D,I):  D=简单,I=低 → 差:0.3, 中:0.4, 优:0.3"
)


print_calc
(
f
"           D=简单,I=高 → 差:0.05,中:0.25,优:0.7"
)


print_calc
(
f
"           D=困难,I=低 → 差:0.5, 中:0.3, 优:0.2"
)


print_calc
(
f
"           D=困难,I=高 → 差:0.1, 中:0.3, 优:0.6"
)


print_calc
(
f
""
)


print_calc
(
f
"P(S|I):  I=低 → S低:0.8,S高:0.2"
)


print_calc
(
f
"         I=高 → S低:0.2,S高:0.8"
)


print_calc
(
f
""
)


print_calc
(
f
"P(L|G):  G=差 → L弱:0.9,L强:0.1"
)


print_calc
(
f
"         G=中 → L弱:0.4,L强:0.6"
)


print_calc
(
f
"         G=优 → L弱:0.05,L强:0.95"
)


print_end
()



# 展示联合概率分解


print_step
(
"步骤2：联合概率分解示例"
)


assignment

=

{
"D"
:

1
,

"I"
:

1
,

"G"
:

2
,

"S"
:

1
,

"L"
:

1
}


jp
,

parts

=

bn
.
joint_probability_verbose
(
assignment
)


asgn_str

=

", "
.
join
(
f
"
{
k
}
=
{
node_labels
[
k
][
v
]
}
"

for

k
,

v

in

assignment
.
items
())


print_calc
(
f
"P(
{
asgn_str
}
)"
)


print_calc
(
f
"= P(D)·P(I)·P(G|D,I)·P(S|I)·P(L|G)"
)


print_calc
(
f
"= "

+

" × "
.
join
(
parts
))


print_result
(
f
"=
{
jp
:
.6e
}
"
)


print_end
()



# 推理1：简单推理


print_step
(
"步骤3：推理1 — P(G | D=困难)"
)


print_calc
(
f
"已知: D=1(困难), 隐变量: I, S, L"
)


print_calc
(
f
"需要对隐变量 I 的所有取值求和（S和L不影响G）"
)


print_calc
(
f
"P(G|D=1) ∝ Σ_I P(D=1)·P(I)·P(G|D=1,I)"
)


print_calc
(
f
""
)


for

g

in

[
0
,

1
,

2
]:


g_label

=

node_labels
[
"G"
][
g
]


total

=

0


for

i

in

[
0
,

1
]:


p

=

bn
.
cpt
[
"D"
][
1
]

*

bn
.
cpt
[
"I"
][
i
]

*

bn
.
cpt
[
"G"
][(
1
,

i
)][
g
]


i_label

=

node_labels
[
"I"
][
i
]


print_calc
(
f
"  G=
{
g_label
}
, I=
{
i_label
}
: P(D=1)·P(I=
{
i
}
)·P(G=
{
g
}
|D=1,I=
{
i
}
)"
)


print_calc
(
f
"    =
{
bn
.
cpt
[
'D'
][
1
]
}
 ×
{
bn
.
cpt
[
'I'
][
i
]
}
 ×
{
bn
.
cpt
[
'G'
][(
1
,

i
)][
g
]
}
"
)


print_calc
(
f
"    =
{
p
:
.4f
}
"
)


total

+=

p


print_calc
(
f
"  Σ =
{
total
:
.4f
}
"
)


print_calc
(
f
""
)


result1

=

bn
.
inference_enumeration
(
"G"
,

{
"D"
:

1
})


for

g
,

p

in

sorted
(
result1
.
items
()):


print_result
(
f
"P(G=
{
node_labels
[
'G'
][
g
]
}
 | 困难) =
{
p
:
.4f
}
"
)


print_end
()



# 推理2


print_step
(
"步骤4：推理2 — P(I | L=强)"
)


print_calc
(
f
"这是一个'逆向推理'：从结果(推荐信)推断原因(智力)"
)


print_calc
(
f
"需要对 D, G, S 求和"
)


print_calc
(
f
"P(I|L=1) ∝ Σ_
{
'{D,G,S}'
}
 P(D)·P(I)·P(G|D,I)·P(S|I)·P(L=1|G)"
)


print_calc
(
f
"（计算过程涉及大量组合，这里展示归一化结果）"
)


result2

=

bn
.
inference_enumeration
(
"I"
,

{
"L"
:

1
})


for

i
,

p

in

sorted
(
result2
.
items
()):


print_result
(
f
"P(I=
{
node_labels
[
'I'
][
i
]
}
 | 强推荐) =
{
p
:
.4f
}
"
)


print_end
()



# 推理3：explaining away


print_step
(
"步骤5：推理3 — P(G | D=困难, S=高)  [间接证据]"
)


print_calc
(
f
"高SAT → 高智力的间接证据 → 提升成绩的概率"
)


print_calc
(
f
"这体现了贝叶斯网的'解释消除'(explaining away)能力"
)


print_calc
(
f
""
)


result3_no_s

=

bn
.
inference_enumeration
(
"G"
,

{
"D"
:

1
})


result3_with_s

=

bn
.
inference_enumeration
(
"G"
,

{
"D"
:

1
,

"S"
:

1
})


print_calc
(
f
"对比（感受 SAT 信息的影响）:"
)


print_calc
(
f
"
{
'成绩'
:
^6
}

{
'P(G|D=困难)'
:
^14
}

{
'P(G|D=困难,S=高)'
:
^18
}

{
'变化'
:
^10
}
"
)


print_calc
(
f
"
{
'─'
*
50
}
"
)


for

g

in

[
0
,

1
,

2
]:


g_label

=

node_labels
[
"G"
][
g
]


p1

=

result3_no_s
[
g
]


p2

=

result3_with_s
[
g
]


delta

=

p2

-

p1


arrow

=

"↑"

if

delta

>

0

else

"↓"

if

delta

<

0

else

"="


print_calc
(
f
"
{
g_label
:
^6
}

{
p1
:
^14.4f
}

{
p2
:
^18.4f
}

{
delta
:
+.4f
}

{
arrow
}
"
)


print_calc
(
f
""
)


print_result
(
f
"高SAT间接说明高智力，使优秀成绩概率从"


f
"
{
result3_no_s
[
2
]
:
.4f
}
升至
{
result3_with_s
[
2
]
:
.4f
}
"
)


print_end
()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 第六部分：EM 算法 (Expectation-Maximization)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class

GaussianMixtureEM
:


"""高斯混合模型的 EM 算法"""


def

__init__
(
self
,

n_components
=
2
,

max_iter
=
100
,

tol
=
1e-6
,

seed
=
42
):


self
.
K

=

n_components


self
.
max_iter

=

max_iter


self
.
tol

=

tol


self
.
seed

=

seed


self
.
means

=

None


self
.
covs

=

None


self
.
weights

=

None


self
.
log_likelihoods

=

[]



# 保存每步的参数用于展示


self
.
history

=

[]


def

_gaussian_density
(
self
,

X
,

mean
,

cov
):


N
,

D

=

X
.
shape


diff

=

X

-

mean


cov_inv

=

np
.
linalg
.
inv
(
cov

+

1e-6

*

np
.
eye
(
D
))


cov_det

=

np
.
linalg
.
det
(
cov

+

1e-6

*

np
.
eye
(
D
))


exponent

=

-
0.5

*

np
.
sum
(
diff

@

cov_inv

*

diff
,

axis
=
1
)


norm_const

=

1.0

/

(
np
.
sqrt
((
2

*

np
.
pi
)

**

D

*

cov_det
))


return

norm_const

*

np
.
exp
(
exponent
)


def

fit
(
self
,

X
,

verbose
=
False
):


np
.
random
.
seed
(
self
.
seed
)


N
,

D

=

X
.
shape


idx

=

np
.
random
.
choice
(
N
,

self
.
K
,

replace
=
False
)


self
.
means

=

X
[
idx
]
.
copy
()


self
.
covs

=

np
.
array
([
np
.
eye
(
D
)

for

_

in

range
(
self
.
K
)])


self
.
weights

=

np
.
ones
(
self
.
K
)

/

self
.
K


self
.
log_likelihoods

=

[]


self
.
history

=

[]



# 保存初始参数


self
.
history
.
append
({


"means"
:

self
.
means
.
copy
(),


"weights"
:

self
.
weights
.
copy
(),


"covs_diag"
:

[
self
.
covs
[
k
]
.
diagonal
()
.
copy
()

for

k

in

range
(
self
.
K
)]


})


for

iteration

in

range
(
self
.
max_iter
):



# ============ E 步 ============


resp

=

np
.
zeros
((
N
,

self
.
K
))


for

k

in

range
(
self
.
K
):


resp
[:,

k
]

=

self
.
weights
[
k
]

*

self
.
_gaussian_density
(


X
,

self
.
means
[
k
],

self
.
covs
[
k
]


)


resp_sum

=

resp
.
sum
(
axis
=
1
,

keepdims
=
True
)


resp_sum

=

np
.
maximum
(
resp_sum
,

1e-300
)


resp

/=

resp_sum



# 对数似然


weighted_density

=

np
.
zeros
(
N
)


for

k

in

range
(
self
.
K
):


weighted_density

+=

self
.
weights
[
k
]

*

self
.
_gaussian_density
(


X
,

self
.
means
[
k
],

self
.
covs
[
k
]


)


ll

=

np
.
sum
(
np
.
log
(
np
.
maximum
(
weighted_density
,

1e-300
)))


self
.
log_likelihoods
.
append
(
ll
)


if

len
(
self
.
log_likelihoods
)

>

1
:


if

abs
(
self
.
log_likelihoods
[
-
1
]

-

self
.
log_likelihoods
[
-
2
])

<

self
.
tol
:


break



# ============ M 步 ============


Nk

=

resp
.
sum
(
axis
=
0
)


for

k

in

range
(
self
.
K
):


Nk_safe

=

max
(
Nk
[
k
],

1e-10
)


self
.
means
[
k
]

=

(
resp
[:,

k
:
k
+
1
]
.
T

@

X
)

/

Nk_safe


diff

=

X

-

self
.
means
[
k
]


self
.
covs
[
k
]

=

(
diff
.
T

@

(
diff

*

resp
[:,

k
:
k
+
1
]))

/

Nk_safe


self
.
covs
[
k
]

+=

1e-6

*

np
.
eye
(
D
)


self
.
weights
[
k
]

=

Nk
[
k
]

/

N



# 保存历史


self
.
history
.
append
({


"means"
:

self
.
means
.
copy
(),


"weights"
:

self
.
weights
.
copy
(),


"covs_diag"
:

[
self
.
covs
[
k
]
.
diagonal
()
.
copy
()

for

k

in

range
(
self
.
K
)],


"Nk"
:

Nk
.
copy
(),


"resp_sample"
:

resp
[:
3
]
.
copy
(),


# 保存前3个样本的责任度


})


return

iteration

+

1


def

predict
(
self
,

X
):


N

=

X
.
shape
[
0
]


resp

=

np
.
zeros
((
N
,

self
.
K
))


for

k

in

range
(
self
.
K
):


resp
[:,

k
]

=

self
.
weights
[
k
]

*

self
.
_gaussian_density
(


X
,

self
.
means
[
k
],

self
.
covs
[
k
]


)


return

np
.
argmax
(
resp
,

axis
=
1
)

def

demo_em_algorithm
():


print_title
(
"第六部分：EM 算法"
)


print
(
"""

  EM 算法用于含隐变量的概率模型参数估计。

  高斯混合模型(GMM): P(x) = Σ_k α_k · N(x|μ_k, Σ_k)

  隐变量 z 表示样本属于哪个高斯成分（不可观测）。

    """
)



# 生成数据


np
.
random
.
seed
(
42
)


cluster1

=

np
.
random
.
randn
(
100
,

2
)

*

0.8

+

np
.
array
([
0
,

0
])


cluster2

=

np
.
random
.
randn
(
100
,

2
)

*

1.0

+

np
.
array
([
5
,

4
])


X

=

np
.
vstack
([
cluster1
,

cluster2
])


true_labels

=

np
.
array
([
0
]
*
100

+

[
1
]
*
100
)


np
.
random
.
seed
(
42
)


shuffle_idx

=

np
.
random
.
permutation
(
200
)


X

=

X
[
shuffle_idx
]


true_labels

=

true_labels
[
shuffle_idx
]


print_step
(
"步骤1：初始化参数"
)


gmm

=

GaussianMixtureEM
(
n_components
=
2
,

max_iter
=
100
,

seed
=
0
)


n_iters

=

gmm
.
fit
(
X
)


init

=

gmm
.
history
[
0
]


print_calc
(
f
"数据: N=200 个二维样本, K=2 个高斯成分"
)


print_calc
(
f
"随机选择2个样本作为初始均值:"
)


for

k

in

range
(
2
):


print_calc
(
f
"  成分
{
k
}
: μ₀ = [
{
init
[
'means'
][
k
][
0
]
:
.3f
}
,
{
init
[
'means'
][
k
][
1
]
:
.3f
}
]"
)


print_calc
(
f
"           Σ₀ = I (单位矩阵)"
)


print_calc
(
f
"           α₀ =
{
init
[
'weights'
][
k
]
:
.2f
}
"
)


print_end
()



# 展示前几步迭代的详细过程


print_step
(
"步骤2：EM 迭代过程（展示前3步）"
)


for

it

in

range
(
min
(
3
,

n_iters
)):


h

=

gmm
.
history
[
it

+

1
]


# it+1 因为 history[0] 是初始值


print_calc
(
f
""
)


print_calc
(
f
"━━ 第
{
it
+
1
}
 步 ━━"
)


print_calc
(
f
""
)



# E 步


print_calc
(
f
"【E步】计算责任度 γ(z_nk) = α_k·N(x_n|μ_k,Σ_k) / Σ_j α_j·N(x_n|μ_j,Σ_j)"
)


if

"resp_sample"

in

h
:


print_calc
(
f
"  前3个样本的责任度 [P(属于成分0), P(属于成分1)]:"
)


for

i

in

range
(
3
):


r

=

h
[
"resp_sample"
][
i
]


assignment

=

"成分0"

if

r
[
0
]

>

r
[
1
]

else

"成分1"


print_calc
(
f
"    样本
{
i
}
: x=[
{
X
[
i
][
0
]
:
.2f
}
,
{
X
[
i
][
1
]
:
.2f
}
] "


f
"→ γ=[
{
r
[
0
]
:
.4f
}
,
{
r
[
1
]
:
.4f
}
] → 归属
{
assignment
}
"
)



# M 步


print_calc
(
f
""
)


print_calc
(
f
"【M步】利用责任度更新参数:"
)


if

"Nk"

in

h
:


print_calc
(
f
"  有效样本数: N₀=
{
h
[
'Nk'
][
0
]
:
.1f
}
, N₁=
{
h
[
'Nk'
][
1
]
:
.1f
}
"
)


for

k

in

range
(
2
):


print_calc
(
f
"  成分
{
k
}
:"
)


print_calc
(
f
"    α = N_k/N =
{
h
[
'weights'
][
k
]
:
.4f
}
"
)


print_calc
(
f
"    μ = Σ γ_nk·x_n / N_k = [
{
h
[
'means'
][
k
][
0
]
:
.4f
}
,
{
h
[
'means'
][
k
][
1
]
:
.4f
}
]"
)


print_calc
(
f
"    σ²对角 = [
{
h
[
'covs_diag'
][
k
][
0
]
:
.4f
}
,
{
h
[
'covs_diag'
][
k
][
1
]
:
.4f
}
]"
)


print_calc
(
f
"  对数似然: LL =
{
gmm
.
log_likelihoods
[
it
]
:
.2f
}
"
)


print_end
()



# 收敛过程


print_step
(
"步骤3：收敛过程 — 对数似然变化"
)


print_calc
(
f
"EM 算法保证: LL(θ^(t+1)) ≥ LL(θ^(t))  （单调不减）"
)


print_calc
(
f
""
)


print_calc
(
f
"
{
'迭代'
:
^6
}

{
'对数似然 LL'
:
^16
}

{
'ΔLL'
:
^14
}
"
)


print_calc
(
f
"
{
'─'
*
38
}
"
)


for

i
,

ll

in

enumerate
(
gmm
.
log_likelihoods
):


if

i

==

0
:


print_calc
(
f
"
{
'第'
+
str
(
i
+
1
)
+
'步'
:
^6
}

{
ll
:
>14.2f
}

{
'—'
:
^14
}
"
)


else
:


delta

=

ll

-

gmm
.
log_likelihoods
[
i
-
1
]


marker

=

" ✓"

if

delta

>=

0

else

" ✗"


print_calc
(
f
"
{
'第'
+
str
(
i
+
1
)
+
'步'
:
^6
}

{
ll
:
>14.2f
}

{
delta
:
>+12.4f
}{
marker
}
"
)


print_calc
(
f
""
)


print_calc
(
f
"共迭代
{
n_iters
}
 步收敛 (ΔLL < 1e-6)"
)


print_end
()



# 最终参数


print_step
(
"步骤4：最终估计的模型参数"
)


print_calc
(
f
"真实参数:  簇0: μ=[0,0], σ²≈0.64  |  簇1: μ=[5,4], σ²≈1.0"
)


print_calc
(
f
""
)


for

k

in

range
(
2
):


print_calc
(
f
"成分
{
k
}
:"
)


print_calc
(
f
"  混合系数 α =
{
gmm
.
weights
[
k
]
:
.4f
}
"
)


print_calc
(
f
"  均值 μ = [
{
gmm
.
means
[
k
][
0
]
:
.4f
}
,
{
gmm
.
means
[
k
][
1
]
:
.4f
}
]"
)


print_calc
(
f
"  协方差对角 = [
{
gmm
.
covs
[
k
][
0
,
0
]
:
.4f
}
,
{
gmm
.
covs
[
k
][
1
,
1
]
:
.4f
}
]"
)


print_end
()



# 聚类结果


pred_labels

=

gmm
.
predict
(
X
)


acc1

=

np
.
mean
(
pred_labels

==

true_labels
)


acc2

=

np
.
mean
((
1

-

pred_labels
)

==

true_labels
)


cluster_acc

=

max
(
acc1
,

acc2
)


print_step
(
"步骤5：聚类评估"
)


print_calc
(
f
"将每个样本分配给责任度最高的成分"
)


print_calc
(
f
"成分0 样本数:
{
np
.
sum
(
pred_labels

==

0
)
}
"
)


print_calc
(
f
"成分1 样本数:
{
np
.
sum
(
pred_labels

==

1
)
}
"
)


print_calc
(
f
""
)


print_calc
(
f
"聚类准确率（考虑标签置换）:"
)


print_calc
(
f
"  方案1 (0→0, 1→1):
{
acc1
:
.4f
}
"
)


print_calc
(
f
"  方案2 (0→1, 1→0):
{
acc2
:
.4f
}
"
)


print_result
(
f
"最优聚类准确率:
{
cluster_acc
:
.4f
}
"
)


print_end
()



# 半监督扩展


print_step
(
"步骤6：扩展 — GMM 用于半监督分类"
)


print_calc
(
f
"思路: 用少量有标签数据建立 成分→类别 的映射"
)


labeled_pred

=

pred_labels
[:
20
]


labeled_true

=

true_labels
[:
20
]


mapping

=

{}


for

k

in

range
(
2
):


mask

=

labeled_pred

==

k


if

np
.
any
(
mask
):


mapping
[
k
]

=

Counter
(
labeled_true
[
mask
])
.
most_common
(
1
)[
0
][
0
]


print_calc
(
f
"  成分
{
k
}
 的标签样本多数为类别
{
mapping
[
k
]
}
 → 映射: 成分
{
k
}
→类别
{
mapping
[
k
]
}
"
)


mapped_pred

=

np
.
array
([
mapping
.
get
(
p
,

0
)

for

p

in

pred_labels
])


semi_acc

=

np
.
mean
(
mapped_pred

==

true_labels
)


print_result
(
f
"半监督分类准确率:
{
semi_acc
:
.4f
}
"
)


print_end
()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# 主函数


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def

main
():


print
(
"""

╔══════════════════════════════════════════════════════════╗

║       贝叶斯分类器综合演示（含详细计算过程）            ║

║                                                          ║

║  1. 贝叶斯决策论      — 最小风险决策框架                ║

║  2. 极大似然估计      — 参数估计的基础方法              ║

║  3. 朴素贝叶斯分类器  — 属性条件独立假设               ║

║  4. 半朴素贝叶斯      — 放松独立假设(SPODE/AODE)       ║

║  5. 贝叶斯网          — 有向图模型与概率推理            ║

║  6. EM 算法           — 含隐变量的参数估计              ║

╚══════════════════════════════════════════════════════════╝

    """
)


demo_bayesian_decision_theory
()


demo_mle
()


demo_naive_bayes
()


demo_semi_naive_bayes
()


demo_bayesian_network
()


demo_em_algorithm
()


print
(
"
\n
"

+

"="

*

60
)


print
(
"  所有演示完毕！"
)


print
(
"="

*

60
)

if

__name__

==

"__main__"
:


main
()

```
