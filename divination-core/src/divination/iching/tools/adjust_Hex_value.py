import json
from importlib import resources
from pathlib import Path
def load() -> dict[int, dict]:
    """从内嵌的 JSON 文件里加载 64 卦的资料。
    取出卦序、卦名和先天卦序"""
    path = resources.files("divination.iching") / "data" / "hexagrams.json"
    records = json.loads(path.read_text(encoding="utf-8"))
    for record in records:
        value = record["value"]
        num = value + 1
        record["value"] = num
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    text = "[\n" + ",\n".join("  " + line for line in lines) + "\n]\n"
    Path(str(path)).write_text(text, encoding="utf-8")

if __name__ == "__main__":
    load()