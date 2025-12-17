from typing import Any, List

def extract_text_from_message(message: Any) -> str:
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        return "".join(
            str(seg.get("data", {}).get("text", "")) for seg in message
            if isinstance(seg, dict) and seg.get("type") == "text"
        )
    return ""

def extract_image_urls(message: Any) -> List[str]:
    res = []
    if isinstance(message, list):
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") in ["image", "face"]:
                url = seg.get("data", {}).get("url")
                if url:
                    res.append(url)
    return res

def extract_qq_from_at(text: str) -> str:
    import re
    m = re.search(r"\[CQ:at,qq=(\d+)\]", text)
    if m:
        return m.group(1)
    m = re.search(r"@(\d{5,12})", text)
    if m:
        return m.group(1)
    return None