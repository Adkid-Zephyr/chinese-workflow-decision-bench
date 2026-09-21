# 接入其他分类器

本仓库是**固定 Feishu 消息分类任务**的可复用benchmark，不是可对任意任务直接排名的通用智力榜。Jev与Laya是首批参测模型，数据、协议与评分器不依赖二者。

标准track为`choice`：任何模型只需返回`urgent / todo / valuable / noise`之一。概率可选；没有概率时不计算Brier/ECE，也不伪造置信度。已有的`four_noul`是特定组合工作流track，应单独比较，不能与choice混成总分。

## 1. 写一个 adapter

在你自己的Python模块（例如`my_classifier.py`）中实现：

```python
def create():
    # 在这里初始化本地模型或HTTP连接；不要把密钥硬编码进代码。
    def predict(request):
        # request只有state和questions，包含虚构viewer、目标消息与上下文。
        # 这里调用自己的分类器；不要读取data/cases.jsonl中的expected标签。
        label = your_classifier(request)
        return {"label": label}
    return predict
```

需要概率时，返回：

```python
{
    "label": "todo",
    "probabilities": {"urgent": 0.1, "todo": 0.7, "valuable": 0.1, "noise": 0.1}
}
```

接口故障应抛出异常，runner将其记为失败并保留在64例分母里。不要在adapter中偷偷重试、根据标签调提示、丢弃难例，或返回预先存好的答案。若需要翻译、检索、微调或特殊提示，这属于新的**模型+处理流程配置**，应明确命名、记录并独立展示。异步GPU操作需在返回前同步。

## 2. 运行

```bash
python evaluate.py --adapter my_classifier:create \
  --model-id my-classifier-v1 --output results/my-classifier-v1 --repeats 3
```

无需任何模型或API，也能先验证整条链路：

```bash
python evaluate.py --adapter adapters.constant:create --kind baseline \
  --model-id constant-noise --output results/constant-noise
```

恒定noise基线应得到16/64；它只验证协议和计分，不能把其运行延迟当成模型性能。

每轮输出`metadata.json`、逐请求`raw.jsonl`、`summary.json`。不同模型的目录独立保存，禁止覆盖。质量固定使用repeat=0；全部重复用于延迟与一致性统计。默认三次；调试可减少重复，但不应与完整三次结果混排。

## 3. 提交结果

提交时附上可执行adapter、模型版本/权重revision、软件版本、设备和精度、提示或训练变更、所有原始结果与摘要。API地址、凭据和个人路径不要提交。只提交模型名和汇总分数不足以进入结果表。

现有`plot_results.py`和`render_report.py`是已发表v1报告的冻结视图，自动读取v1记录；不会自动把未经审核的自报结果混入已验证成绩图。新模型经记录完整性、协议一致性和隐私检查后，再显式扩展图表的参测配置列表。若更换数据或标签，必须创建新的benchmark版本，不能覆盖v1。
