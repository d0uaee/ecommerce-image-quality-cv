import re
import sys
from pathlib import Path

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['fr', 'en'], gpu=False)
    return _reader


_NOISE = re.compile(
    r'^[\d\W]+$'          # pure numbers or punctuation
    r'|^\d+[a-z]{0,3}$'   # prices like 299dh, 99€
    r'|^.$'               # single chars
)


def _is_meaningful(word: str) -> bool:
    w = word.strip()
    if len(w) < 2:
        return False
    if _NOISE.match(w.lower()):
        return False
    if re.match(r'^\d', w):  # starts with digit (e.g. "299DH", "54GB" edge cases)
        # allow alphanumeric product codes like "A54" — keep if letters follow digits meaningfully
        if not re.match(r'^\d+[A-Za-z]{2,}$', w):
            return False
    return True


def extract_text(image_path) -> dict:
    image_path = Path(image_path)
    try:
        reader = _get_reader()
        results = reader.readtext(str(image_path))
    except Exception as exc:
        return {
            "text_found": [],
            "prompt": "",
            "confidence": 0.0,
            "success": False,
            "error": str(exc),
        }

    if not results:
        return {"text_found": [], "prompt": "", "confidence": 0.0, "success": True}

    texts = [text for (_, text, _) in results]
    confidences = [conf for (_, _, conf) in results]

    avg_confidence = sum(confidences) / len(confidences)

    # collect individual words across all detected text blocks
    words = []
    for block in texts:
        for token in block.split():
            token_clean = re.sub(r'[^\w]', '', token)
            if token_clean:
                words.append(token_clean)

    meaningful = [w.lower() for w in words if _is_meaningful(w)]

    # deduplicate while preserving order
    seen = set()
    deduped = []
    for w in meaningful:
        if w not in seen:
            seen.add(w)
            deduped.append(w)

    prompt = " ".join(deduped[:4])

    return {
        "text_found": texts,
        "prompt": prompt,
        "confidence": round(avg_confidence, 4),
        "success": True,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr.py <image_path>")
        sys.exit(1)

    result = extract_text(sys.argv[1])
    print(f"success:    {result['success']}")
    print(f"confidence: {result['confidence']}")
    print(f"text_found: {result['text_found']}")
    print(f"prompt:     {result['prompt']!r}")
