# match
配件寿命预测代码：对配件寿命进行预测，从而进行预防性更换
## 故障率函数(Probability)
$$
\lambda(t) = \frac{\beta}{\theta} (\frac{t}{\theta})^(\beta - 1) ,  \beta > 0, \theta > 0, t > 0
$$

整个算法的核心为上述故障率函数，算法思路将配件分为两个生命周期：平稳工作期和快速衰退期，根据拟合得到的结果预测故障率达到阈值的时间，
即剩余寿命预测

目前实现部分为寿命预测，并在此基础上实现了较为粗浅的备件策略，即通过故障率计算仓库备件最大值和最小值，寿命预测部分进行了数据测试，
拟合效果较为理想，但对数据输入要求较高，要将数据转化为0——1之间的故障率，虽然市场部分配件有此类转化的对照数据表，据此可以拟合得到函数，
但仍有一些没有转化方式的数据存在

另外函数要求存在变点检测和数据滤波功能，其中变点检测进行了较为粗浅的实现：进行预测，如果实际检测结果和预测结果相差较大，则定为变点。
而噪音滤波功能未实现

## 自适应多阶段Wiener退化模型

此算法的核心为wiener退化模型：


定义退化程度为 $\{X(t), t \geqslant 0\}$, 漂移参数为 $\mu$ ，扩散参数为 $\sigma$ 的 (一元) Wiener 过程：

$$
X(t)=\mu t+\sigma B(t)
$$

根据定义, 对带漂移的 Wiener 过程, 显然有如下的性质成立:

（1）时刻 $t \sim t+\Delta t$ 之间的增量服从正态分布, 即 $\Delta X=X(t+\Delta t)-X(t) \sim$ $N\left(\mu \Delta t, \sigma^2 \Delta t\right)$ 。

（2）对任意两个不相交的时间区间,增量 $X\left(t_4\right)-X$ $\left(t_3\right)$ 与 $X\left(t_2\right)-X\left(t_1\right)$ 相互独立

于是可以通过储存的数据进行极大似然估计，得到 $\mu$ 和 $\sigma$ ,再根据已知参数对配件寿命等进行估计

极大似然估计：

$$
\mu =\frac{1}{N} \frac{\sum \Delta X_i}{\sum \Delta t_i}
$$

$$
\sigma^2 = \frac{N}{(N-1) * \sum \Delta t_i} \sum (\Delta X(t)_i - \mu  t_i)^2
$$

得到上述参数后，在模型中加入参数：退化程度阈值l和可靠度阈值R，并以此计算可靠度和剩余寿命：

可靠度：以配件当前退化程度预测其能用到给定时间点的概率

$$
P(X(\Delta t) < l - X(t_s)) = \phi (\frac {l - X(t_i) - \mu \Delta t}{\sigma \sqrt{\Delta t}})
$$

依据可靠度反推时间点：即预测一个时间点为最近可能发生故障(故障概率大于阈值)的点：

$$
\phi (\frac {l - X(t_i) - \mu \Delta t}{\sigma \sqrt{\Delta t}}) < R
$$

$$
\frac {l - X(t_i) - \mu \Delta t}{\sigma \sqrt{\Delta t}} < \phi ^{-1} (R)
$$

得到的解取正数
