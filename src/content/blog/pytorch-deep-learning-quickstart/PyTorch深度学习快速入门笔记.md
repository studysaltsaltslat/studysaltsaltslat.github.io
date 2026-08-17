---
title: 'PyTorch 深度学习快速入门笔记'
description: '一份面向初学者的 PyTorch 快速入门笔记，涵盖 TensorBoard、图像预处理、卷积与池化、网络搭建、损失函数、训练验证及 GPU 推理。'
publishDate: '2026-08-17'
tags: ['PyTorch', '深度学习', 'torchvision', '神经网络', '机器学习']
language: '中文'
---

## 环境准备

创建环境：

```
create -n name python=3.6		//创建环境
conda activate name				//激活环境
conda env list					//查看已经创建的环境
```

```python
>>> import torch
>>> print(torch.__version__)
2.4.1
>>> print(torch.version.cuda)
11.8
>>> print(torch.cuda.is_available())
True
```



有个常见坑：`PIL` 读取彩色图片时通道顺序是 RGB，而 `cv2.imread()` 读进来默认是 BGR。所以把 cv2 的图片送入模型前，常需要转换：

```
img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
```

## 一些库的使用

### `Tensorboard`

TensorBoard 是一个把模型==训练过程可视化==的工具
核心作用：训练时记录数据，之后在浏览器中以曲线、图片、直方图等方式查看。

#### `tensorboard`的作用

训练模型时，终端可能只会输出：

```python
epoch 1: loss=2.30, accuracy=0.25
epoch 2: loss=1.76, accuracy=0.42
epoch 3: loss=1.05, accuracy=0.71
```

数字很多，不容易看出趋势，`TensorBoard`会把它们画成图。以便迅速判断：

- loss 是否持续下降：模型是否正在学
- accuracy 是否上升：预测是否变准
- 曲线是否乱跳：训练是否不稳定
- 训练集很好、验证集很差：是否过拟合
- 两个实验谁更好：模型或参数是否有改进

#### 使用方法

`TensorBoard`本身主要负责“看”，`SummaryWriter`负责“记”。

```mermaid
graph LR
训练代码 --> SummaryWriter记录数据;
SummaryWriter记录数据--> 日志文件;
日志文件--> TensorBoard显示图表;
```

```python
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter("logs")
```

上面这行会创建一个记录器，把日志放到`logs`文件夹。
接着训练时记录数据：
`writer.add_scalar("train_loss", loss, epoch)`
最后关闭：`writer.close()`
然后在终端启动`TensorBoard`：`tensorboard --logdir logs`
它通常会给出地址：`http://localhost:6006`
复制到浏览器打开，就能看图。 

#### 记录数字曲线(最常用)

例如记录损失值：

```python
from torch.utils.tensorboard import SummaryWriter
writer = SummaryWriter("logs")
for step in range(100):
    loss = 100 / (step + 1)  # 假设这是当前 loss
    writer.add_scalar("loss", loss, step)
writer.close()
```

同时记录训练集和测试集：

```python
writer.add_scalar("Loss/train", train_loss, epoch)
writer.add_scalar("Loss/val", val_loss, epoch)
writer.add_scalar("Accuracy/train", train_acc, epoch)
writer.add_scalar("Accuracy/val", val_acc, epoch)
```

名字里使用`/`，`TensorBoard`会自动分组。比如 `Loss/train`和`Loss/val`会放在同一类里，方便比较。

#### 记录图片

TensorBoard 也能显示图片，例如看看训练数据是否正确：
`writer.add_image("cat", image_tensor, 0)`
这里的 image_tensor 通常要是 PyTorch Tensor，形状为：
`[通道, 高, 宽]`，即`[C, H, W]`
彩色图片一般是：`[3, H, W]`
如果为`NumPy`图片，形状通常为`[H, W, C]`，要明确告知格式：
`writer.add_image("cat", image_array, 0, dataformats="HWC")`

这很适合检查：

- 图片是否读对了
- RGB/BGR 颜色是否颠倒
- 数据增强后的图片是什么样
- 模型生成的图片是否正常

### `transforms`

#### 内置`__call__`函数

让对象可以像函数一样直接用括号调用
如下方例子，输出都为`ZhangFei`，但前者无需用`.hello`

```python
class Person:
    def __call__(self,name):
        print(name)
    def  hello(self,name):
        print(name)

person = Person()
person("ZhangFei")
person.hello("ZhangFei")
```

#### `ToTensor`

把`PIL Image`或`numpy.ndarray`转换成`ToTensor`的形式。

```python
trans_totensor = transforms.ToTensor()
img_tensor = trans_totensor(img)
writer.add_image("ants_image", img_tensor)
```

#### `Normalize`

作用：Normalize a tensor image with mean and standard deviation.(不支持PIL格式)

```
output[channel] = (input[channel] - mean[channel]) / std[channel]
```


<table style="width: 100%; border: none;">
  <tr>
    <td style="border: none; vertical-align: top; text-align: center;">
      <img src="/assets/pytorch-deep-learning-quickstart/image-20260807073811484.png" alt="归一化前" style="width: 100%;" />
      <p style="text-align: center;">归一化前</p>
    </td>
    <td style="border: none; vertical-align: top; text-align: center;">
      <img src="/assets/pytorch-deep-learning-quickstart/image-20260807073824201.png" alt="归一化后" style="width: 100%;" />
      <p style="text-align: center;">归一化后</p>
    </td>
  </tr>
</table>

#### `Resize`

作用：Resize the input image to the given size.

旧版的`Resize`只能是

```
If the image is torch Tensor, it is expected
to have [..., H, W] shape, where ... means a maximum of two leading dimensions
```

代码：

```python
print(img.size)     #The format of PIL
trans_resize = transforms.Resize((224, 224))
img_resize = trans_resize(img)
print(img_resize.size) 
writer.close()
```

输出结果：

```python
(768, 512)
(224, 224)
```

#### `Compose`

作用：把多个图像预处理操作按顺序组合起来。

```python
from torchvision import transforms
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])
```

当执行`img = transform(img)`时，它等价于依次执行：

```python
img = transforms.Resize((224, 224))(img)
img = transforms.ToTensor()(img)
img = transforms.Normalize(...)(img)
```

常用于给 Dataset 统一指定训练/测试数据的预处理流程。

#### `Crop`

通常训练集使用`RandomCrop`，测试集用`CenterCrop`，以保证评估结果稳定。

##### `RandomCrop`

`transforms.RandomCrop`会从图像中随机选择一个位置，裁剪出指定大小的区域。
`transforms.RandomCrop((224, 224))`
每次读取同一张图，裁剪位置都可能不同。这是一种数据增强：让模型看到同一物体的不同局部和位置，从而减少对固定位置的依赖，提升泛化能力。

##### `CenterCrop`

`transforms.CenterCrop`会从图像正中央裁剪出指定大小的区域。
`transforms.CenterCrop((224, 224))`
例如原图是 300×400，它会保留中心的 224×224 部分，四周会被裁掉。

### `torchvision`中的数据集使用

[Datasets — Torchvision 0.28 documentation](https://docs.pytorch.org/vision/stable/datasets.html)

## 搭建网络模型

### `nn.Module`

`nn.Module` 是 PyTorch 中所有神经网络模型的基类。

```python
import torch
from torch import nn

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()

    def forward(self, input):
        output = input + 1
        return output

net = Net()
x = torch.tensor(1.0)
output = net(x)
print(output)
```

输出：`tensor(2.)`

### `Convolution Layers`

作用：用一个小的“滤波器”在输入上滑动，提取局部特征。

图片：高度 × 宽度，使用 `Conv2d`
音频或时间序列：时间长度，使用 `Conv1d`
视频或三维医学图像：深度 × 高度 × 宽度，使用 `Conv3d`

#### 参数设置

##### `padding`

卷积前在输入边缘补零或其他数值，例如：

```python
nn.Conv2d(3, 16, kernel_size=3, padding=1)
```

对于 `3 × 3` 卷积核，`padding=1` 通常可以保持高宽不变。

常见选择：

```python
nn.Conv2d(3, 16, kernel_size=3, padding="same")
```

`padding="same"` 表示尽量保持输入和输出空间尺寸相同，但通常要求步幅为 1。

也可以使用：

```
nn.Conv2d(3, 16, kernel_size=3, padding="valid")
```

`valid` 表示不进行填充，空间尺寸会变小。

##### `kernel_size`

`kernel_size`表示为卷积核大小。

常见卷积核：`1 × 1`、`3 × 3`、`5 × 5`、`7 × 7`，其中`3 × 3` 是最常见的选择。

卷积核越大，看到的局部区域越大，但参数量和计算量也会增加。现代网络通常用多个 `3 × 3` 卷积代替一个较大的卷积核。

#### `nn.Conv2d`

下图是模拟8 张 RGB 图片经过卷积层的代码：

```python
import torch
import torch.nn as nn

conv = nn.Conv2d(
    in_channels=3,
    out_channels=16,
    kernel_size=3
)
```

参数含义：

`in_channels=3`：输入有 3 个通道，例如 RGB 图像
`out_channels=16`：使用 16 个卷积核，输出 16 个特征图
`kernel_size=3`：卷积核大小为 `3 × 3`

输入形状：`(batch_size, channels, height, width)`，

`x = torch.randn(8, 3, 32, 32)`

| 参数 | 含义                        |
| ---- | --------------------------- |
| 8    | 一次处理 8 张图片           |
| 3    | 每张图片有 3 个通道，即 RGB |
| 32   | 图片高度为 32               |
| 32   | 图片宽度为 32               |

其中`torch.randn(...)` 随机生成一个形状为 `(8, 3, 32, 32)` 的张量，常用于测试代码。

输出形状：

```python
y = conv(x)
print(y.shape)
# torch.Size([8, 16, 30, 30])
```

| 参数 | 含义                       |
| ---- | -------------------------- |
| 8    | 仍然是 8 张图片            |
| 16   | 卷积层生成了 16 个特征通道 |
| 30   | 输出高度为 30              |
| 30   | 输出宽度为 30              |

二维卷积操作：

```python
import torch.nn.functional as F
import torch
#输入数据
input = torch.tensor([[1, 2, 0, 3, 1],
                      [0, 1, 2, 3, 1],
                      [1, 2, 1, 0, 0],
                      [5, 2, 3, 1, 1],
                      [2, 1, 0, 1, 1]])

#卷积核
kernel = torch.tensor([
    [1, 2, 1],
    [0, 1, 0],
    [2, 1, 0],
])

#由于卷积为4个参数，需要通过reshape改变维度
input = torch.reshape(input, (1, 1, 5, 5))
kernel = torch.reshape(kernel, (1, 1, 3, 3))

output_0 = F.conv2d(input, kernel,stride=1)
output_1 = F.conv2d(input, kernel,stride=2)
print(output_0)
print(output_1)
```

结果：

```python
tensor([[[[10, 12, 12],
          [18, 16, 16],
          [13,  9,  3]]]])
tensor([[[[10, 12],
          [13,  3]]]])
```

### `Pooling Layers`

池化缩小特征图，保留局部区域最重要或平均的特征。池化==不改变批量大小和通道数，只缩小高、宽==。

常见的池化为最大池化和平均池化。

```python
nn.MaxPool1d
nn.MaxPool2d
nn.MaxPool3d

nn.AvgPool1d
nn.AvgPool2d
nn.AvgPool3d
```

最大池化强调“最强响应”，例如出现的明显边缘或纹理；平均池化保留区域整体的平均信息。

对于图片，常用为`nn.MaxPool2d`和`nn.AvgPool2d`，输入形状与 `Conv2d` 一样：

```python
(batch_size, channels, height, width)
```

例如`x = torch.randn(8, 16, 32, 32)`表示8 张图片，每张有 16 个特征通道，每张特征图大小为 32 × 32。

#### 参数

##### `kernel_size` 和 `stride`

```python
nn.MaxPool2d(kernel_size=2, stride=2)
```

`kernel_size=2`表示每次查看一个 `2 × 2` 区域；`stride=2`表示每次向右或向下移动 2 格。

这正好把高和宽各缩小一半：`32 × 32 -> 16 × 16`

若`stride=1`，如下面代码所示：

```
nn.MaxPool2d(kernel_size=2, stride=1)
```

池化窗口每次移动一格，区域之间重叠，尺寸只会略微减小：`32 × 32 -> 31 × 31`

如果不写 `stride`：

```python
nn.MaxPool2d(kernel_size=2)
```

默认等价于：

```python
nn.MaxPool2d(kernel_size=2, stride=2)
```

##### `padding`

池化同样可以在边缘补充内容：

```python
nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
```

实践中池化最常见的写法为：`nn.MaxPool2d(2)`

也就是 `2 × 2` 窗口、步幅为 2，不填充。其等价于：

```python
nn.MaxPool2d(
    kernel_size=2,
    stride=2,    # stride 不写时，默认等于 kernel_size
    padding=0    # padding 的默认值为 0
)
```

#### `MaxPool`

```python
import torch

input = torch.tensor([[1, 2, 0, 3, 1],
                      [0, 1, 2, 3, 1],
                      [1, 2, 1, 0, 0],
                      [5, 2, 3, 1, 1],
                      [2, 1, 0, 1, 1]])

input = torch.reshape(input, (1, 1, 5, 5))

class Net(torch.nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.Maxpool = torch.nn.MaxPool2d(kernel_size=2, stride=2)

    def forward(self, x):
        output = self.Maxpool(x)
        return output

net = Net()
output = net(input)
print(output)
```

输出结果：

```python
tensor([[[[2, 3],
          [5, 3]]]])
```

由于输入是 `5 × 5`，而池化窗口是 `2 × 2`且`stride=2`，最右边列和最下面行不足以组成完整的 `2 × 2` 窗口，会被默认丢弃。
如果需保留边缘不完整的区域，可启用 `ceil_mode=True`：

```python
self.Maxpool = torch.nn.MaxPool2d(
    kernel_size=2,
    stride=2,
    ceil_mode=True
)
```

这时输出为 `3 × 3`，边缘窗口只对实际存在的数据取最大值：

```python
tensor([[[[2, 3, 1],
          [5, 3, 1],
          [2, 1, 1]]]])
```

### `Non-linear Activation`

激活函数通常放在卷积层或全连接层之后，用来给神经网络加入“非线性表达能力”。

```python
import torch

input = torch.tensor([[1, -0.5],
                      [-1, 3]])
input = torch.reshape(input, (1, 1, 2, 2))

class Net(torch.nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.relu = torch.nn.ReLU()

    def forward(self, x):
        output = self.relu(x)
        return output

net = Net()
output = net(input)
print(output)
```

输出结果：

```python
tensor([[[[1., 0.],
          [0., 3.]]]])
```

### `linear Layers`

`nn.Linear` 是 PyTorch 中最常用的全连接层，也叫线性层。

```
nn.Linear(in_features, out_features)
```

数学公式：
$$
y = xW^T + b
$$
输入的每个特征都会和输出层的每个神经元连接，并进行加权求和。

<img src="/assets/pytorch-deep-learning-quickstart/image-20260809140947221.png" alt="image-20260809140947221" style="zoom: 15%;" />

```python
import torch
import torch.nn as nn

linear = nn.Linear(
    in_features=3,
    out_features=2
)
# 也可写为linear = nn.Linear(3,2)
# 此时输入形状为(1, 3)，输出形状为(1, 2)
x = torch.tensor([[1.0, 2.0, 3.0]])
y = linear(x)

print(y.shape)
# torch.Size([1, 2])
```

#### 内部原理

当线性层代码为`linear = nn.Linear(3, 2)`时，这个层内部会自动创建：

```python
linear.weight
linear.bias
```

它们的形状是：

```py
print(linear.weight.shape)
# torch.Size([2, 3])

print(linear.bias.shape)
# torch.Size([2])
```

可以理解为：

```
2 个输出神经元
每个神经元有 3 个输入权重
每个神经元还有 1 个偏置
```

参数数量是：
$$
\text{参数量} = \text{out\_features} \times \text{in\_features} + \text{out\_features}
$$
$\text{out\_features} \times \text{in\_features}$为`weight`的参数量，$out\_features$为`bias`的参数量。

例如，`nn.Linear(3, 2)`中，参数量：2 × 3 + 2 = 8

#### 代码

```python
import torchvision
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
dataset = torchvision.datasets.CIFAR10
(root='./dataset',train=False,
 transform=torchvision.transforms.ToTensor(),download=False)
dataloader = DataLoader(dataset=dataset,batch_size=64)

class Net(nn.Module):
    def __init__(self):
        super(Net,self).__init__()
        self.linear = nn.Linear(196608,10)
    def forward(self, x):
        output = self.linear(x)
        return output

net = Net()

for data in dataloader:
    img, label = data
    print(img.shape)
    output = torch.reshape(img,(1,1,1,-1))
    # output = torch.flatten(img)可达到相同效果
    print(output.shape)
    output = net(output)
    print(output.shape)
```

输出结果：

```python
torch.Size([64, 3, 32, 32])
torch.Size([1, 1, 1, 196608])
torch.Size([1, 1, 1, 10])
```

### `Sequential`的使用

以`CIFAR10`为例，模型如下图所示：

<img src="/assets/pytorch-deep-learning-quickstart/image-20260809161919296.png" alt="image-20260809161919296" style="zoom: 33%;" />

卷积核的通道和输入通道相同，卷积核的个数和输出通道相同。

代码如下：

```python
import torch
from torch import nn
from torch.nn import Conv2d,MaxPool2d,Flatten,Linear,Sequential
from torch.utils.tensorboard import SummaryWriter
class Net(nn.Module):
    def __init__(self):
        super(Net,self).__init__()
        self.network = Sequential(
            Conv2d(3,32,5,padding="same"),
            MaxPool2d(2),
            Conv2d(32,32,5,padding="same"),
            MaxPool2d(2),
            Conv2d(32,64,5,padding="same"),
            MaxPool2d(2),
            Flatten(),
            Linear(1024,64),
            Linear(64,10)
        )

    def forward(self,x):
        return self.network(x)

net = Net()
print(net)
input = torch.ones((64,3,32,32))
output = net(input)
print(output.shape)

writer = SummaryWriter("logs_seq")
writer.add_graph(net,input)
writer.close()
```

输出结果：

```python
Net(
  (network): Sequential(
    (0): Conv2d(3, 32, kernel_size=(5, 5), stride=(1, 1), padding=same)
    (1): MaxPool2d(kernel_size=2, stride=2, padding=0, dilation=1, ceil_mode=False)
    (2): Conv2d(32, 32, kernel_size=(5, 5), stride=(1, 1), padding=same)
    (3): MaxPool2d(kernel_size=2, stride=2, padding=0, dilation=1, ceil_mode=False)
    (4): Conv2d(32, 64, kernel_size=(5, 5), stride=(1, 1), padding=same)
    (5): MaxPool2d(kernel_size=2, stride=2, padding=0, dilation=1, ceil_mode=False)
    (6): Flatten(start_dim=1, end_dim=-1)
    (7): Linear(in_features=1024, out_features=64, bias=True)
    (8): Linear(in_features=64, out_features=10, bias=True)
  )
)
torch.Size([64, 10])
```

<img src="/assets/pytorch-deep-learning-quickstart/image-20260809230136587.png" alt="image-20260809230136587" style="zoom: 40%;" />

### 损失函数与反向传播

作用：

计算实际输出和目标之间的差距，为更新输出提供一定依据(反向传播)

#### `L1loss`

`L1loss`是绝对误差，公式为：\(\mathrm{L1} = \frac{1}{N}\sum_i|\hat y_i-y_i|\)

代码如下：

```python
import torch
import torch.nn as nn

inputs = torch.tensor([1,2,3])
targets = torch.tensor([1,2,5])
# ((1-1)+(2-2)+(5-3))/3 = 0.6667

loss = nn.L1Loss()
print(loss(inputs.float(),targets.float()))
```

输出结果：`tensor(0.6667)`

#### `MSEloss`

`MSELoss`是均方误差，公式为：\(\mathrm{MSE} = \frac{1}{N}\sum_i(\hat y_i-y_i)^2\)

代码如下：

```python
loss_mse = nn.MSELoss()
print(loss_mse(inputs.float(),targets.float()))
# ((1-1)^2+(2-2)^2+(5-3)^2)/3 = 1.3333
```

输出结果：`tensor(1.3333)`

#### `Softmax`+交叉熵

`CrossEntropyLoss`是单标签多分类，适用于每个样本只属于一个类别，例如猫 / 狗 / 鸟三分类。

公式如下：
$$
\operatorname{loss}(x, \text{class}) = -\log\left( \frac{\exp(x[\text{class}])}{\sum_j \exp(x[j])} \right) = -x[\text{class}] + \log\left( \sum_j \exp(x[j]) \right)
$$
例如，下图中图片为狗，

<img src="/assets/pytorch-deep-learning-quickstart/image-20260810091244357.png" alt="image-20260810091244357" style="zoom: 60%;" />

```python
target = ["person", "dog", "cat"]
output = [0.1, 0.2, 0.3]
# target = 1 (class=dog)
#Loss(x,class) = -0.2+log(exp(0.1)+exp(0.2)+exp(0.3))
```

### 优化器 `optim`

```python
import torch
import torchvision
from torch import nn
from torch.nn import Conv2d,MaxPool2d,Flatten,Linear,Sequential
from torch.optim import optimizer
from torch.utils.data import Dataset,DataLoader
from torch.utils.tensorboard import SummaryWriter
dataset = torchvision.datasets.CIFAR10(root='./dataset',train=False,download=False,
                                       transform=torchvision.transforms.ToTensor())
dataloader = DataLoader(dataset,batch_size=1)
class Net(nn.Module):
    def __init__(self):
        super(Net,self).__init__()
        self.model1 = Sequential(
            Conv2d(3,32,5,padding="same"),
            MaxPool2d(2),
            Conv2d(32,32,5,padding="same"),
            MaxPool2d(2),
            Conv2d(32,64,5,padding="same"),
            MaxPool2d(2),
            Flatten(),
            Linear(1024,64),
            Linear(64,10)
        )


    def forward(self,x):
        return self.model1(x)

loss = nn.CrossEntropyLoss()
net = Net()
optim = torch.optim.SGD(net.parameters(),lr=0.01)
for data in dataloader:
    imgs,targets = data					# 前向传播，得到预测
    output = net(imgs)  				# 计算损失
    result_loss = loss(output,targets)		# 梯度清零
    optim.zero_grad()					# 反向传播，计算新梯度
    result_loss.backward()				# 更新参数
    optim.step()
```

`loss(...)`：**计算损失值**，衡量预测和正确答案相差多少。

`result_loss.backward()`：**反向传播**，根据损失计算每个网络参数的梯度。

`optim.step()`：**优化器**，根据这些梯度更新参数。

## 模型训练

### 现有网络模型使用及修改

```python
import torchvision
from torch import nn
import ssl
import certifi
from torchvision.models import VGG16_Weights

ssl._create_default_https_context = lambda: ssl.create_default_context(
    cafile=certifi.where()
)
vgg16_false = torchvision.models.vgg16(weights=None)
vgg16_true = torchvision.models.vgg16(weights=VGG16_Weights.DEFAULT)

print(vgg16_true)
train_data = torchvision.datasets.CIFAR10("./dataset", train=True, download=False, transform=torchvision.transforms.ToTensor())
vgg16_true.classifier.add_module("add_linear", nn.Linear(1000, 10))
print(vgg16_true)

print(vgg16_false)
vgg16_false.classifier[6] = nn.Linear(4096, 10)
print(vgg16_false)
```

由于`vgg_16`全连接层为`Linear(4096, 1000, bias=True)`，输出是1000，即可以识别1000个类别。但`CIFAR10`只有10个类别，有两种方法：

1. 在`module`后再加一个线性层，即`nn.Linear(1000, 10)`
2. 将最后一层从 `Linear(4096, 1000)` 替换为 `Linear(4096, 10)`(更常见)

### 模型的保存与读取

#### 模型的保存

```python
import torch
import torchvision

vgg16 = torchvision.models.vgg16(weights= None)
# method 1
torch.save(vgg16, 'vgg16_method1.pth')

# method 2 官方推荐
torch.save(vgg16.state_dict() , 'vgg16_method2.pth')
print(vgg16)

# 陷阱1
class Net(torch.nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = torch.nn.Conv2d(3, 64, 3)
    def forward(self, x):
        x = self.conv1(x)
        return x
model = Net()
torch.save(model, 'net_method1.pth')
```

#### 模型的读取

```python
import torch
from module_save import *
import torchvision

# method 1
model = torch.load('vgg16_method1.pth')
print(model)

# method 2
vgg16.load_state_dict(torch.load('vgg16_method2.pth'))

# 陷阱1
model = torch.load("net_method1.pth")
print(model)
```

在自己定义的模型`net`中，需要在加载的文档中引入`class`：

```python
from module_save import *
```

### 完整的模型训练-GPU训练

模型文件通常单独放在一个`py`文件中，下面是`model.py`的代码：

```python
import torch
from torch.nn import Module,Conv2d,MaxPool2d,Flatten,Linear,Sequential
class Net(Module):
    def __init__(self):
        super(Net, self).__init__()
        self.model = Sequential(
            Conv2d(3,32,5,padding="same"),
            MaxPool2d(2),
            Conv2d(32,32,5,padding="same"),
            MaxPool2d(2),
            Conv2d(32,64,5,padding="same"),
            MaxPool2d(2),
            Flatten(),
            Linear(1024,64),
            Linear(64,10)
        )
    def forward(self, x):
        x = self.model(x)
        return x

if __name__ == "__main__":
    net = Net()
    input = torch.ones(64,3,32,32)
    output = net(input)
    print(output.size())
```

其中，`if __name__ == "__main__"`表示只有当 Python 文件被直接运行时，下面的缩进代码才会执行。若在其它文件导入，如`from net import Net`，则不会执行。

作用：可以把定义的模型和测试模型放在同一个文件，且不会在导入模型时意外运行测试代码。



### 完整的模型验证套路

在分类模型中，输出表示对每个类别预测的概率。如`[0.1,0.2]`表示识别为类别1的概率为0.1，识别为类别2的概率为0.2，且最终识别为类别1。可以对比输出与真实结果，计算正确率。

```python
import torch
outputs = torch.tensor([[0.1,0.2],[0.3,0.4],])
print(outputs.argmax(dim=1))
preds = outputs.argmax(dim=1)
targets = torch.tensor([0,1])
print((preds == targets).sum())
```

其中，`argmax`表示输出最大值所在的索引， `dim=1`表示横向看，`0`表示纵向看。`(preds == targets).sum()`输出预测正确的个数



```python
import torch
import torchvision
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

from model import *

train_data = torchvision.datasets.CIFAR10(root='./dataset', train=True, download=False,
                                          transform=torchvision.transforms.ToTensor())
test_data = torchvision.datasets.CIFAR10(root='./dataset', train=False, download=False,
                                          transform=torchvision.transforms.ToTensor())

# 利用DataLoader加载数据集
train_loader = DataLoader(train_data, batch_size=64)
test_loader = DataLoader(test_data, batch_size=64)

# 创建网络模型
net = Net()

# 损失函数
loss_fn = torch.nn.CrossEntropyLoss()

# 优化器
learning_rate = 0.01
optimizer = torch.optim.SGD(net.parameters(), lr=learning_rate)

# 设置训练网络的一些参数
# 记录训练的次数
total_train_step = 0
# 记录测试的次数
total_test_step = 0
# 训练的轮数
epoch = 10

# 添加tensorboard
writer = SummaryWriter("./logs_train")

for i in range(epoch):
    print("---------第 {} 轮训练开始---------".format(i+1))

    # 训练步骤开始
    net.train()
    for data in train_loader:
        inputs, labels = data
        outputs = net(inputs)
        loss = loss_fn(outputs, labels)

        # 优化器优化模型
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_train_step += 1
        if total_train_step % 100 == 0:
            print("训练次数：{},Loss:{}".format(total_train_step,loss.item()))
            writer.add_scalar("train_loss", loss.item(), total_train_step)

    # 测试步骤开始
    net.eval()
    total_test_loss = 0
    total_accuracy = 0
    with torch.no_grad():
        for data in test_loader:
            inputs, labels = data
            outputs = net(inputs)
            loss = loss_fn(outputs, labels)
            total_test_loss += loss.item()
            accuracy = (outputs.argmax(1) == labels).sum()
            total_test_step += 1
            total_accuracy += accuracy

    print("整体测试集上的Loss:{}".format(total_test_loss))
    print("整体测试集上的正确率:{}".format(total_accuracy/len(test_data)))
    writer.add_scalar("test_loss", total_test_loss, total_test_step)
    writer.add_scalar("test_accuracy", total_accuracy/len(test_data), total_test_step)

    # 保存模型
    # torch.save(net, "net_{}.pth".format(i+1))
    # print("模型已保存")

writer.close()
```

### 利用GPU训练

#### 方法1

对网络模型、数据(输入、标注)、损失函数后加上`.cuda()`即可：

```python
net = net.cuda()
loss_fn = loss_fn.cuda()

inputs = inputs.cuda()
labels = labels.cuda()
# 训练数据和测试数据都要
```

若没有GPU，为了代码的规范性，可以写成：

```python
if torch.cuda.is_available:
    inputs = inputs.cuda()
    labels = labels.cuda()
```

若要对比GPU对于CPU的加速情况，可以`import time`，在训练前后分别记录时间：

```python
import time
start_time = time.time()
...
end_time = time.time()
print(end_time - start_time)
```

得到利用GPU和CPU的时间分别为：

```
48.737282037734985
143.42298674583435
```

也可以登录`google colab`进行GPU训练。

#### 方法2

利用`.to(device)`

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
```

对网络模型、数据(输入、标注)、损失函数后加上`.to(device)`即可：

```python
net = net.to(device)
loss_fn = loss_fn.to(device)

inputs = inputs.to(device)
labels = labels.to(device)
```

### 完整的模型验证套路

由于png格式是4个通道，除了RGB三个通道外，还有一个透明度通道。所以需要调用`.convert('RGB')`保留其颜色通道。

在训练模型时，`model.eval()` 把模型切换到评估模式，配合 `torch.no_grad()`，更省内存、速度更快。

```python
model.eval()
with torch.no_grad():
    output = model(image)
```

训练前需切回：`model.train()`。

```python
tensor([[-0.1600, -9.7866,  6.9017,  6.3408,  4.1983, 13.5008, -0.4002, -0.7823, 7.8787, -9.3244]])
tensor([5])
```

其中`label`如下：

```python
{'airplaine:'0,'automobile:'1,'bird':2,'cat':3,'deer':4,'dog':5,'frog:'6,'horse:'7,'ship:'8,'truck:'9}
```

`tensor([5])`对应为`dog`，预测正确。完整代码如下：

```python
import cv2
from PIL import Image
from model import *
import torchvision

image_path = "./imgs/dog2.png"
image = Image.open(image_path).convert('RGB')
print(image)

transform = torchvision.transforms.Compose([
    torchvision.transforms.Resize((32,32)),
    torchvision.transforms.ToTensor()
])
image = transform(image)
print(image.shape)

model = torch.load('net_40_gpu.pth', weights_only=False,map_location='cpu')
print(model)
image = torch.reshape(image, (-1,3,32,32))
model.eval()
with torch.no_grad():
    output = model(image)
print(output)
print(output.argmax(dim=1))
```
