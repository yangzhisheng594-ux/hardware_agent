# 本地小模型驱动的硬件设计助手

这是一个 Python 命令行程序，使用本地 Ollama 模型 `qwen3:4b`，结合简单 RAG 知识库检索、工具调用、规则校验和一次自动修正，生成硬件设计方案。

常见的 3.3V/I2C/温湿度传感器小板会优先走本地快速模板，未知或复杂需求再调用 Ollama 兜底。

## 环境准备

启动本地模型：

```bash
ollama run qwen3:4b
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 运行方式

在 `hardware_agent` 目录下运行：

```bash
python main.py --task "设计一个3.3V供电的温湿度传感器小板，包含I2C接口"
```

也可以从项目上级目录运行：

```bash
python hardware_agent/main.py --task "设计一个3.3V供电的温湿度传感器小板，包含I2C接口"
```

## 输出文件

程序会自动创建并写入 `outputs/` 目录：

- `design.json`：模型生成或修正后的结构化硬件设计。
- `validation_report.json`：纯 Python 规则校验结果，包含 `passed` 和 `checks`。
- `repair_report.json`：自动修正结果。即使未触发修正，也会生成并标记 `repair_attempted: false`。
- `trace.jsonl`：每一步流程的 JSONL trace 日志，使用追加模式写入。
- `final_report.md`：可读的 Markdown 最终摘要。

## 自动校验与修正

系统会检查供电、GND、I2C 上拉、去耦电容、元件完整性和引用来源。如果校验失败，程序会最多调用一次 `qwen3:4b` 尝试修正设计，并把结果写入 `repair_report.json`。

如果无法连接 Ollama，程序会输出：

```text
错误：无法连接到 Ollama，请确保已运行 ollama run qwen3:4b
```
