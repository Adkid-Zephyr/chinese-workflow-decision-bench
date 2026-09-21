# Feishu Message Classification Benchmark

[简体中文](README.md) · **English**

A reusable classification benchmark for Feishu-style workplace messages. Frozen inputs, prompts and labels make it possible to compare classification quality, false task assignments and end-to-end latency. Jev and Laya are the first evaluated models.

<img src="assets/xiaohongshu-scorecard-3x4-en.png" width="480" alt="Jev vs Laya: English scorecard in 3:4 portrait format">

[Download PNG](assets/xiaohongshu-scorecard-3x4-en.png) · [Download SVG](assets/xiaohongshu-scorecard-3x4-en.svg) · [Detailed results](RESULTS.md) · [Raw records](results/v1)

**This is an AI-assisted synthetic diagnostic, not private chat data, a general model leaderboard, or an independently annotated blind test.** It is not affiliated with Feishu and does not test the Feishu platform itself. An earlier 12-case pilot informed the design; these 64 cases and prompts were frozen before the recorded runs. Labels were not changed after inspecting results. Both models received the same structured requests.

## Results at a glance

<!-- quick-table-en:start -->

| Track | Jev correct | Laya correct | Jev median latency | Laya median latency |
|---|---:|---:|---:|---:|
| Choice | **64/64 (100.00%)** | 20/64 (31.25%) | 253 ms | 151 ms |
| Four-question workflow | **63/64 (98.44%)** | 18/64 (28.12%) | 250 ms | 415 ms |

<!-- quick-table-en:end -->

**Choice** asks one four-way classification question. **4Q / four-noul** asks four binary questions—relevance, action required, urgency and information value—then applies fixed decision thresholds. These are separate prompt/workflow tracks, not separate model weights.

A **false task assignment** is a message labeled `valuable` or `noise` in the reference that the model turns into `todo` or `urgent`. Each track includes 32 non-action cases. The scorecard reports all three dimensions separately; there is no weighted composite score.

## Dataset and protocol

- **64 Chinese synthetic cases**, eight per family: ownership, lifecycle, urgency, knowledge sharing, conditional requests, untrusted quoted content, thread context and cross-chat interference.
- **Four balanced labels**, 16 each: `urgent`, `todo`, `valuable`, `noise`. A constant-class baseline scores 16/64 (25%).
- Three repeated runs for every case and prompt mode, in a seeded shuffled order: **384 timed requests per model, 768 total**, plus two excluded warmups per model.
- Quality uses the **preselected first repeat**, keeping the denominator at 64 rather than treating repeated predictions as independent samples. All repeated results are published.
- Latency uses all successful timed requests: 192 per configuration after warmup. p95 uses linear interpolation. Failures remain in the quality denominator and are reported separately; no automatic retries.
- Reported metrics include accuracy, macro-F1, confusion matrices, false/missed tasks, urgent recall, repeat consistency and latency. Brier/ECE are descriptive diagnostics for probability-producing classifiers, not broad calibration claims.

Reference labels reflect an explicit product policy. A canceled or completed task without substantive new information is `noise`; relevant new knowledge or findings may be `valuable`. An ordinary deadline alone is not `urgent`. These choices may differ from another product's policy. See the frozen [manifest](data/manifest.json) and [cases](data/cases.jsonl).

## Recorded configurations

| Model | Configuration |
|---|---|
| Jev | `jev-1.13.0`; persistent HTTP client; latency includes network round trip |
| Laya | Multilingual base checkpoint; local Apple M4 MPS GPU; 32 GB unified memory; two CPU threads |

Laya checkpoint revision: `1c5edc17a7acd8701df6fc341c0d179f1c62c982`. Default context and question-prefix budgets are 1,024 and 256 tokens. No domain fine-tuning was performed. The [pinned inference source](https://github.com/Adkid-Zephyr/laya/tree/ef7d7d269e2e34c763c228144dc10fe7d421acf9) changes download filtering only, not model computation.

These are real deployment paths, **not a same-hardware inference comparison**. Network conditions, background load and thermal state were not controlled as in a laboratory throughput study.

## Environment checks and interpretation

A small follow-up checked eight fixed, stratified cases with both prompt modes. CPU and MPS agreed on **16/16 labels and returned probabilities**, at the precision exposed by the runtime. The full weight SHA-256 matches the published Hub blob. None of the original cases truncated Laya's state, instructions or candidate options.

This reduces suspicion of an MPS-specific failure, but CPU and MPS share software and weights: it does not rule out shared implementation problems or substitute for an independent CUDA replication. The 16 diagnostic calls are not added to the original 768 timed requests.

The observed gap is consistent with weaker generalization to this workflow, but does **not** establish that Jev has more knowledge or better pretraining. The test mainly measures ownership, negation, cancellation, context and rule application—not encyclopedic recall. The [evidence-based analysis](docs/ANALYSIS.md) distinguishes findings from hypotheses and remaining unknowns; the [environment check](results/v1/environment_check.json) is fully recorded.

## Evaluate another classifier

The standard `choice` track accepts a small Python adapter. It receives the frozen `state` and `questions`, never reference labels, and returns a label with optional probabilities.

```python
# my_classifier.py
def create():
    def predict(request):
        label = your_classifier(request)
        return {"label": label}
    return predict
```

```bash
python evaluate.py --adapter my_classifier:create \
  --model-id my-classifier-v1 --output results/my-classifier-v1 --repeats 3
```

Try the complete pipeline without a model or API:

```bash
python evaluate.py --adapter adapters.constant:create --kind baseline \
  --model-id constant-noise --output results/constant-noise
```

The constant baseline should score 16/64. It is a plumbing check, not a latency competitor. Outputs include metadata, per-request records and a summary; existing runs cannot be overwritten. Missing probabilities are not fabricated. Backend failures are retained, and asynchronous accelerators must be synchronized before an adapter returns.

Submit the executable adapter, exact model/revision, software/device/precision details, any prompt or training changes, and all raw records. New submissions are reviewed before being added to the published scorecard. Changing data or labels requires a new benchmark version. [Additional adapter guidance](docs/ADDING_MODELS.md).

## Reproduce and audit

The adapter runner and offline metric checks use the Python standard library. For the recorded Jev/Laya backends, use Python 3.11 and `pip install -r requirements.txt`; follow the [backend setup instructions](README.md#复现). `bench.py` preserves the original two-model protocol.

```bash
python -m unittest discover -s tests -v
python privacy_check.py
python summarize.py
python render_report.py
```

Do not rerun `freeze.py` or relabel cases when reproducing v1. Dataset and request hashes are verified. Initial dataset/protocol freeze commit: `0ce2d5f`.

To regenerate the English portrait scorecard:

```bash
pip install -r requirements-viz.txt
python plot_social.py --lang en
```

The image is **1440 × 1920 (3:4)** and carries the same metrics and caveats as the Chinese scorecard. `--lang zh` generates the Chinese chart and table; Chinese rendering requires Hiragino Sans GB or Noto Sans CJK. SVG text is converted to paths for portable viewing.

## Limitations, privacy and license

Synthetic cases are cleaner and more balanced than real conversations. Some cases are related, labels lack independent multi-annotator validation, and the prompts were informed by earlier exploration. Results do not establish real-world error rates, statistical significance, or general model rankings. First-repeat 64/64 does not mean a model is infallible; later-repeat variation is published.

Public artifacts contain fictional people and scenarios—not real chats, customer information, API keys, account email addresses, device serial numbers or local user paths. Code, tests and reports were prepared with OpenAI Codex assistance. This project is not affiliated with Artificial Analysis, Laya or TypeSafe.

Code, synthetic data and authored benchmark records are MIT-licensed. Model weights are not distributed and retain their upstream licenses.
