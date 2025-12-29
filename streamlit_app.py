import time
import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests
import streamlit as st


# =========================================================
#  BING WEB SEARCH CONFIG (STREAMLIT SECRETS)
# =========================================================

BING_API_KEY = st.secrets["BING_API_KEY"]
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"


def perform_bing_search(query: str, max_results: int = 5) -> List[str]:
    """
    Calls Bing Web Search API and returns a list of snippets.
    """
    headers = {
        "Ocp-Apim-Subscription-Key": BING_API_KEY,
    }
    params = {
        "q": query,
        "count": max_results,
        "mkt": "en-US",
        "safeSearch": "Moderate",
    }

    try:
        resp = requests.get(BING_ENDPOINT, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        snippets: List[str] = []
        web_pages = data.get("webPages", {}).get("value", [])
        for item in web_pages[:max_results]:
            snippet = item.get("snippet") or item.get("name") or ""
            if snippet:
                snippets.append(snippet)

        if not snippets:
            return [f"(No snippets returned by Bing for '{query}'.)"]

        return snippets

    except Exception as e:
        return [f"(Search error for '{query}': {str(e)[:200]})"]


# =========================================================
#  DATA STRUCTURES
# =========================================================

@dataclass
class BackgroundPacket:
    domain: str
    notes: List[str] = field(default_factory=list)
    confidence: float = 0.0
    completeness: float = 0.0


@dataclass
class CoherenceState:
    sigma: float
    z: float
    divergence: float
    coherence: float


@dataclass
class GenesisConfig:
    truth_threshold: float = 0.55
    probing_threshold: float = 0.6
    max_iterations: int = 3
    memory_decay_rate: float = 0.005
    memory_reinforcement_step: float = 0.03
    persistence_file: str = "sledai_developmental_state.json"


@dataclass
class MemoryItem:
    kind: str
    content: str
    tags: List[str]
    strength: float
    created_at: float
    last_reinforced: float
    meta: Dict[str, Any] = field(default_factory=dict)


# =========================================================
#  GENESIS / SLEDAI DEVELOPMENTAL MIND
# =========================================================

class GenesisMind:
    """
    Developmental cognitive engine with:
    - Automatic early-learning (0–5) using Bing
    - Logs all early-learning searches
    - Stages: infancy → schooling → advanced
    - SLED-style coherence
    - Episodic + semantic + developmental + search-log memory
    """

    def __init__(self, config: Optional[GenesisConfig] = None):
        self.config = config or GenesisConfig()
        self.age_interactions: int = 0

        self.domains = [
            "language_symbols",
            "geography",
            "relationships_empathy",
            "science_engineering",
            "politics_economics",
            "philosophy",
            "mathematics",
            "computing_logic",
        ]

        self.memory: List[MemoryItem] = []
        self.self_profile: Dict[str, Any] = {
            "created_at": datetime.utcnow().isoformat(),
            "total_inputs": 0,
            "domain_counts": {d: 0 for d in self.domains},
            "top_tags": {},
        }

        self.stage: str = "infancy"
        self.early_learning_complete: bool = False

        self.last_search_log: List[Dict[str, Any]] = []
        self.early_learning_log: List[Dict[str, Any]] = []

    # ------------------------------
    #  PERSISTENCE
    # ------------------------------
    def save(self):
        data = {
            "config": asdict(self.config),
            "age_interactions": self.age_interactions,
            "memory": [asdict(m) for m in self.memory],
            "self_profile": self.self_profile,
            "stage": self.stage,
            "early_learning_complete": self.early_learning_complete,
            "last_search_log": self.last_search_log,
            "early_learning_log": self.early_learning_log,
        }
        with open(self.config.persistence_file, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, persistence_file: str) -> "GenesisMind":
        if not os.path.exists(persistence_file):
            return cls(GenesisConfig(persistence_file=persistence_file))
        with open(persistence_file, "r") as f:
            data = json.load(f)
        cfg = GenesisConfig(**data.get("config", {}))
        mind = cls(cfg)
        mind.age_interactions = data.get("age_interactions", 0)
        mind.memory = [MemoryItem(**m) for m in data.get("memory", [])]
        mind.self_profile = data.get("self_profile", mind.self_profile)
        mind.stage = data.get("stage", "infancy")
        mind.early_learning_complete = data.get("early_learning_complete", False)
        mind.last_search_log = data.get("last_search_log", [])
        mind.early_learning_log = data.get("early_learning_log", [])
        return mind

    # =====================================================
    #  TAGGING & DOMAIN DETECTION
    # =====================================================

    def _extract_tags(self, text: str) -> List[str]:
        words = text.lower().replace(",", " ").replace(".", " ").split()
        stop = {
            "the","and","or","of","in","a","an","to","for","is","are","as","on",
            "that","this","with","you","your","my","have","has","it","they","them",
            "was","were","from","about","into","over","under","very","just","more",
            "some","their","there","here","than","then"
        }
        tags = [w for w in words if len(w) > 3 and w not in stop]

        for t in tags:
            self.self_profile["top_tags"][t] = self.self_profile["top_tags"].get(t, 0) + 1

        return tags

    def _detect_domains(self, text: str) -> List[str]:
        q = text.lower()
        active: List[str] = []

        if any(w in q for w in ["word","language","symbol","meaning","sentence","name","story"]):
            active.append("language_symbols")
        if any(w in q for w in ["country","city","continent","border","map","capital","world"]):
            active.append("geography")
        if any(w in q for w in ["relationship","friend","family","feel","emotion","empathy","love","dog","people","kind","son","daughter","brother","sister"]):
            active.append("relationships_empathy")
        if any(w in q for w in ["physics","chemistry","biology","engineering","gravity","entropy","energy","force","atom"]):
            active.append("science_engineering")
        if any(w in q for w in ["election","policy","government","inflation","market","economy","power"]):
            active.append("politics_economics")
        if any(w in q for w in ["meaning of life","ethics","morality","consciousness","free will","soul"]):
            active.append("philosophy")
        if any(w in q for w in ["equation","theorem","proof","integral","derivative","probability","number"]):
            active.append("mathematics")
        if any(w in q for w in ["algorithm","code","program","logic","boolean","bit","neural","compute","software"]):
            active.append("computing_logic")

        if not active:
            active = ["language_symbols"]

        return active

    # =====================================================
    #  COHERENCE ENGINE
    # =====================================================

    def _compile_background(self, text: str, domains: List[str]) -> Dict[str, BackgroundPacket]:
        background: Dict[str, BackgroundPacket] = {}
        for d in domains:
            pkt = BackgroundPacket(domain=d)
            if d == "language_symbols":
                pkt.notes.append("Interpreting key terms and how you are framing the idea.")
                pkt.confidence = 0.75
                pkt.completeness = 0.65
            elif d == "relationships_empathy":
                pkt.notes.append("Considering emotional tone and relational context.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "science_engineering":
                pkt.notes.append("Mapping to scientific or engineering principles.")
                pkt.confidence = 0.8
                pkt.completeness = 0.7
            elif d == "politics_economics":
                pkt.notes.append("Contextualising power, incentives, institutions.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "geography":
                pkt.notes.append("Locational and spatial context if relevant.")
                pkt.confidence = 0.65
                pkt.completeness = 0.55
            elif d == "philosophy":
                pkt.notes.append("Conceptual and ethical framing.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "mathematics":
                pkt.notes.append("Underlying structural / quantitative patterns.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            elif d == "computing_logic":
                pkt.notes.append("Algorithmic and logical structuring.")
                pkt.confidence = 0.7
                pkt.completeness = 0.6
            background[d] = pkt
        return background

    def _compute_coherence(self, text: str, background: Dict[str, BackgroundPacket], iteration: int) -> CoherenceState:
        num_domains = len(background)
        domain_entropy = 0.3 + 0.15 * (num_domains - 1)

        if background:
            avg_conf = sum(p.confidence for p in background.values()) / num_domains
            avg_comp = sum(p.completeness for p in background.values()) / num_domains
        else:
            avg_conf = 0.0
            avg_comp = 0.0

        sigma_base = domain_entropy * (1.2 - 0.2 * avg_comp)
        sigma = max(0.05, sigma_base * (1.1 - 0.25 * iteration))

        z = min(0.98, 0.3 + 0.4 * avg_conf + 0.1 * iteration)

        divergence = sigma * z
        coherence = max(0.0, 1.0 - divergence)

        return CoherenceState(
            sigma=sigma,
            z=z,
            divergence=divergence,
            coherence=coherence,
        )

    # =====================================================
    #  MEMORY SYSTEM
    # =====================================================

    def _decay_memory(self):
        if not self.memory:
            return
        now = datetime.utcnow().timestamp()
        kept: List[MemoryItem] = []
        for m in self.memory:
            dt_min = (now - m.last_reinforced) / 60.0
            decay_factor = 1.0 - self.config.memory_decay_rate * dt_min
            m.strength = max(0.0, m.strength * decay_factor)
            if m.strength > 0.1:
                kept.append(m)
        self.memory = kept

    def _store_memory(self, kind: str, content: str, tags: List[str], strength: float, meta: Optional[Dict[str, Any]] = None):
        now = datetime.utcnow().timestamp()
        item = MemoryItem(
            kind=kind,
            content=content,
            tags=tags,
            strength=strength,
            created_at=now,
            last_reinforced=now,
            meta=meta or {},
        )
        self.memory.append(item)

    def _recall_memory(self, tags: List[str], k: int = 5) -> List[MemoryItem]:
        if not self.memory or not tags:
            return []
        tag_set = set(tags)
        scored = []
        now = datetime.utcnow().timestamp()
        for m in self.memory:
            m_tags = set(m.tags)
            overlap = len(tag_set.intersection(m_tags))
            if overlap == 0:
                continue
            age_min = max(1.0, (now - m.created_at) / 60.0)
            score = overlap * m.strength / age_min
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]

    # =====================================================
    #  BING SEARCH LOGGING
    # =====================================================

    def _search_and_log(self, query: str, context: str, for_early_learning: bool = False) -> List[str]:
        snippets = perform_bing_search(query)
        now = datetime.utcnow().timestamp()

        log_entries: List[Dict[str, Any]] = []
        for idx, s in enumerate(snippets):
            tags = self._extract_tags(s)
            self._store_memory(
                kind="search_log",
                content=s,
                tags=tags,
                strength=0.5,
                meta={"query": query, "context": context, "rank": idx},
            )
            entry = {
                "query": query,
                "rank": idx,
                "snippet": s[:250],
                "context": context,
                "time": now,
            }
            log_entries.append(entry)

        self.last_search_log = log_entries
        if for_early_learning:
            self.early_learning_log.extend(log_entries)

        return snippets

    # =====================================================
    #  EARLY LEARNING (0–5)
    # =====================================================

    def run_early_learning_if_needed(self):
        if self.early_learning_complete:
            return

        curriculum = [
            ("objects_basic", "simple objects for toddlers"),
            ("animals_basic", "common animals for young children"),
            ("family_basic", "family member words for kids"),
            ("emotions_basic", "basic emotions list for children"),
            ("actions_basic", "simple verbs for kids"),
            ("safety_basic", "safety rules for young children"),
            ("stories_basic", "short simple stories for children"),
        ]

        any_valid = False

        for module_name, query in curriculum:
            snippets = self._search_and_log(query, context=f"early_learning:{module_name}", for_early_learning=True)
            combined = "\n".join(snippets)

            if all("error" in s.lower() for s in snippets):
                continue

            tags = self._extract_tags(combined)
            if not tags:
                continue

            self._store_memory(
                kind="developmental",
                content=f"[EARLY CURRICULUM {module_name}] {combined[:800]}",
                tags=tags,
                strength=0.7,
                meta={"module": module_name, "query": query},
            )
            any_valid = True

        if any_valid:
            self.early_learning_complete = True
            self.stage = "schooling"
        else:
            self.early_learning_complete = False
            self.stage = "infancy"

    # =====================================================
    #  SCHOOLING & ADVANCED LEARNING
    # =====================================================

    def _learn_schooling(self, user_input: str, tags: List[str], domains: List[str]) -> Dict[str, Any]:
        q = f"{user_input} explained for school students"
        snippets = self._search_and_log(q, context="schooling")
        combined = "\n".join(snippets)
        search_tags = self._extract_tags(combined)

        lesson = f"Schooling lesson based on: {user_input}\nSnippets:\n" + "\n".join(snippets[:3])
        self._store_memory(
            kind="semantic",
            content=lesson,
            tags=tags + search_tags,
            strength=0.65,
            meta={"mode": "schooling", "query": q},
        )
        return {
            "lesson": lesson,
            "snippets": snippets,
            "search_tags": search_tags,
            "query": q,
        }

    def _learn_advanced(self, user_input: str, tags: List[str], domains: List[str]) -> Dict[str, Any]:
        q = f"{user_input} detailed explanation"
        snippets = self._search_and_log(q, context="advanced")
        combined = "\n".join(snippets)
        search_tags = self._extract_tags(combined)

        recalled = self._recall_memory(tags, k=5)
        synthesis_lines = []
        synthesis_lines.append("Advanced synthesis of your query using what I know and what I can see:")
        if recalled:
            synthesis_lines.append("\nFrom our previous interactions I recall:")
            for m in recalled[:3]:
                synthesis_lines.append(f"- ({m.kind}) {m.content[:160]}")
        synthesis_lines.append("\nFrom external information I see summaries like:")
        for s in snippets[:3]:
            synthesis_lines.append(f"- {s}")
        synthesis = "\n".join(synthesis_lines)

        self._store_memory(
            kind="semantic",
            content=synthesis,
            tags=tags + search_tags,
            strength=0.75,
            meta={"mode": "advanced", "query": q},
        )
        return {
            "synthesis": synthesis,
            "snippets": snippets,
            "search_tags": search_tags,
            "recalled": recalled,
            "query": q,
        }

    # =================================================
