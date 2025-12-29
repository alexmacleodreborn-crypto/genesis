from dataclasses import dataclass, field
from typing import List, Dict, Any
from .utils import now_ts


@dataclass
class MemoryItem:
    kind: str                   # 'childhood', 'experience', 'identity', 'inference'
    content: str
    source: str                 # 'auto_childhood', 'user_question', 'internal_question', etc.
    tags: List[str]
    links: List[int]
    learned_via: str            # 'auto_childhood', 'dialogue', 'inference', 'cross_reference'
    from_steps: List[int]       # timeline steps that produced this memory
    emotion_valence: float      # -1.0 to 1.0
    emotion_labels: List[str]
    created_at: float = field(default_factory=now_ts)


class MemorySystem:
    def __init__(self):
        self.memories: List[MemoryItem] = []

    def add_memory(
        self,
        kind: str,
        content: str,
        source: str,
        tags: List[str],
        links: List[int],
        learned_via: str,
        from_steps: List[int],
        emotion_valence: float,
        emotion_labels: List[str],
    ) -> int:
        item = MemoryItem(
            kind=kind,
            content=content,
            source=source,
            tags=tags,
            links=links,
            learned_via=learned_via,
            from_steps=from_steps,
            emotion_valence=emotion_valence,
            emotion_labels=emotion_labels,
        )
        self.memories.append(item)
        return len(self.memories) - 1

    def size(self) -> int:
        return len(self.memories)

    def get(self, idx: int) -> MemoryItem:
        return self.memories[idx]

    def find_related(self, tags: List[str], k: int = 5) -> List[int]:
        if not tags:
            return []
        tag_set = set(tags)
        scored = []
        for i, m in enumerate(self.memories):
            overlap = len(tag_set.intersection(set(m.tags)))
            if overlap > 0:
                scored.append((overlap, i))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [idx for _, idx in scored[:k]]

    def summary_lines(self) -> List[str]:
        lines = []
        for i, m in enumerate(self.memories):
            tags = ", ".join(m.tags[:5])
            links = ", ".join(str(idx) for idx in m.links) if m.links else "none"
            emo = f"{m.emotion_valence:+.2f} [{', '.join(m.emotion_labels)}]" if m.emotion_labels else "0.00 []"
            lines.append(
                f"[{i}] kind={m.kind}, src={m.source}, via={m.learned_via}, "
                f"tags=[{tags}], links→[{links}], emo={emo}, from_steps={m.from_steps}"
            )
        return lines
