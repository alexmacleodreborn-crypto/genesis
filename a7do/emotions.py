from typing import List, Tuple


EMOTION_WORDS = {
    "happy": (0.6, ["joy"]),
    "happiness": (0.6, ["joy"]),
    "sad": (-0.5, ["sadness"]),
    "sadness": (-0.5, ["sadness"]),
    "afraid": (-0.6, ["fear"]),
    "fear": (-0.6, ["fear"]),
    "kindness": (0.7, ["warmth"]),
    "love": (0.8, ["affection"]),
    "alone": (-0.4, ["loneliness"]),
    "safe": (0.5, ["safety"]),
    "hurt": (-0.4, ["hurt"]),
}


def infer_emotion_from_text(text: str) -> Tuple[float, List[str]]:
    words = [w.strip(".,!?").lower() for w in text.split()]
    valence = 0.0
    labels: List[str] = []
    count = 0
    for w in words:
        if w in EMOTION_WORDS:
            v, labs = EMOTION_WORDS[w]
            valence += v
            labels.extend(labs)
            count += 1
    if count > 0:
        valence /= count
    labels = list(sorted(set(labels)))
    return valence, labels


def blend_emotions(a: float, b: float, w: float = 0.5) -> float:
    w = max(0.0, min(1.0, w))
    return a * (1 - w) + b * w
