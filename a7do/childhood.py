import time
import re
from collections import defaultdict

class Childhood:
    """
    Childhood learning module (ages 0–5).
    Produces associative memory primitives, not facts.
    """

    BURST_DURATION = 10.0  # seconds

    def __init__(self):
        self.active = False
        self.start_time = None

        self.imprints = []
        self.current_burst = defaultdict(set)

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def start_burst(self):
        self.active = True
        self.start_time = time.time()
        self.current_burst.clear()

    def is_active(self) -> bool:
        if not self.active:
            return False
        if time.time() - self.start_time >= self.BURST_DURATION:
            self.end_burst()
            return False
        return True

    def end_burst(self):
        self.active = False
        self.start_time = None

        if self.current_burst:
            self.imprints.append({
                "tags": {k: list(v) for k, v in self.current_burst.items()},
                "confidence": 0.2,
                "timestamp": time.time(),
                "stage": "childhood"
            })

        self.current_burst.clear()

    # --------------------------------------------------
    # Learning
    # --------------------------------------------------

    def absorb(self, text: str):
        if not self.is_active():
            return

        t = text.lower()

        # -----------------------------
        # Emotional words (very basic)
        # -----------------------------
        emotions = ["like", "love", "hate", "happy", "sad", "scared"]
        for e in emotions:
            if e in t:
                self.current_burst["emotion"].add(e)

        # -----------------------------
        # Motion verbs (lemmatised)
        # -----------------------------
        motion_map = {
            "ride": ["ride", "riding", "rode"],
            "run": ["run", "running", "ran"],
            "walk": ["walk", "walking", "walked"],
            "jump": ["jump", "jumping", "jumped"]
        }

        for root, forms in motion_map.items():
            if any(f in t for f in forms):
                self.current_burst["motion"].add(root)

        # -----------------------------
        # Objects
        # -----------------------------
        objects = ["bike", "dog", "cat", "ball", "car", "toy"]
        for o in objects:
            if o in t:
                self.current_burst["object"].add(o)

        # -----------------------------
        # Properties (colour etc.)
        # -----------------------------
        colours = ["blue", "red", "green", "yellow"]
        for c in colours:
            if c in t:
                self.current_burst["property"].add(c)

        # -----------------------------
        # Categories (proto-ontology)
        # -----------------------------
        category_map = {
            "bike": "vehicle",
            "car": "vehicle",
            "dog": "animal",
            "cat": "animal"
        }

        for obj, cat in category_map.items():
            if obj in t:
                self.current_burst["category"].add(cat)

        # -----------------------------
        # Self reference
        # -----------------------------
        if any(p in t for p in ["i ", "my ", "mine"]):
            self.current_burst["self"].add("true")

    # --------------------------------------------------
    # Introspection
    # --------------------------------------------------

    def summary(self):
        return {
            "active": self.active,
            "seconds_remaining": max(
                0,
                round(self.BURST_DURATION - (time.time() - self.start_time), 2)
            ) if self.active else 0,
            "imprints": self.imprints[-5:]
        }