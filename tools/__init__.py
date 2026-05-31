import json
import re


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen3:4b"
OLLAMA_CONNECTION_ERROR = "错误：无法连接到 Ollama，请确保已运行 ollama run qwen3:4b"


def call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """调用本地 Ollama，返回模型输出文本。"""
    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("错误：缺少依赖 requests，请先运行 pip install -r requirements.txt") from exc

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": "/no_think\n" + prompt,
                "stream": False,
                "keep_alive": "10m",
                "options": {
                    "temperature": 0,
                    "top_p": 0.8,
                    "num_predict": 900,
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(OLLAMA_CONNECTION_ERROR) from exc

    try:
        return resp.json()["response"].strip()
    except (KeyError, ValueError, TypeError) as exc:
        raise RuntimeError("错误：Ollama 返回格式异常，未找到 response 字段") from exc


def safe_parse_json(text: str) -> dict:
    """去掉 markdown 代码块和思考标签后解析 JSON。"""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))
