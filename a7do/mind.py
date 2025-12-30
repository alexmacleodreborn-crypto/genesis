import time
import re

from a7do.tagger import Tagger
from a7do.entities import EntityGraph
from .entity_facts import EntityFactLedger

from a7do.event_frame import EventMemory
from a7do.reoccurrence import ReoccurrenceTracker


class A7DOMind:
    def __init__(self, identity, emotion, memory, development, multi_agent, childhood):
        self.identity = identity
        self.emotion = emotion
        self.memory = memory
        self.development = development
        self.multi_agent = multi_agent
        self.childhood = childhood

        self.tagger = Tagger()
        self.entities = EntityGraph()
        self.facts = EntityFactLedger()

        # FLOW LAYER
        self.events = EventMemory(bind_window_s=20)     # B: temporal binding window
        self.reoccurrence = ReoccurrenceTracker()

        self.unbound_names = {}   # name -> {count,last_seen,source}

        self.log = []
        self.path = []

        # lightweight lexicons for “sound/visual/environment/feelings/actions”
        self._emo_words = {"excited", "happy", "sad", "anxious", "calm", "angry", "worried", "scared"}
        self._env_words = {"park", "home", "gate", "street", "garden", "room", "vet", "car", "beach"}
        self._visual_words = {"see", "look", "bright", "dark", "colour", "color", "red", "blue", "yellow", "green"}
        self._sound_words = {"hear", "loud", "quiet", "noise", "music", "bang", "bark"}
        self._action_words = {"tied", "tie", "trained", "training", "ride", "riding", "walk", "walking", "run", "running"}

    # ----------------------------

    def emit(self, phase, msg):
        self.log.append(f"[{phase}] {msg}")
        self.path.append(phase)
        time.sleep(0.001)

    # ----------------------------
    # Helpers
    # ----------------------------

    def _ensure_user_entity(self):
        user = self.entities.find_by_name_or_alias(self.identity.user_name)
        if not user:
            user = self.entities.create("person")
            user.add_name(self.identity.user_name)
        return user

    def _extract_surface_labels(self, text: str):
        # Keep it conservative: capitalized tokens become “labels”, not entities.
        labels = []
        for w in re.findall(r"[A-Za-z']+", text):
            if w.istitle():
                labels.append(w)
        return list(dict.fromkeys(labels))

    def _extract_signals(self, text: str):
        t = text.lower()
        emotions = {w: 1.0 for w in self._emo_words if w in t}
        env = {w: 1.0 for w in self._env_words if w in t}
        actions = {w: 1.0 for w in self._action_words if w in t}

        modalities = {}
        if any(w in t for w in self._visual_words):
            modalities["visual"] = 1.0
        if any(w in t for w in self._sound_words):
            modalities["sound"] = 1.0
        if "feel" in t or "feeling" in t:
            modalities["feeling"] = 1.0

        return modalities, emotions, env, actions

    def _detect_entities_from_text(self, text: str, user_entity_id: str):
        """
        Conservative entity detection:
        - Dog mention creates animal entity (structure only)
        - Names remain unbound until we have an entity in the same event
        """
        t = text.lower()
        created = []

        # Dog entity
        if "dog" in t:
            dog = self.entities.create("animal")
            dog.add_attribute("species:dog", 1.0)
            dog.link("owner", user_entity_id)
            created.append(dog)
            self.emit("ENTITY", f"Detected animal entity {dog.id}")

            # candidate identity fact (needs source+time via ledger rules)
            source = "childhood" if self.childhood.is_simple_input(text) else "adult"
            self.facts.add_candidate(dog.id, "identity:dog", source)
            self.facts.try_promote_identity(dog.id, "identity:dog")

        return created

    def _handle_names_aliases(self, text: str, current_entities: list, source: str):
        """
        Names:
        - If label already maps to an entity => alias candidate
        - Otherwise => unbound label candidate
        - If entities exist in this event, bind unbound labels to them (as 'name:' candidates)
        """
        labels = self._extract_surface_labels(text)

        for label in labels:
            e = self.entities.find_by_name_or_alias(label)
            if e:
                self.facts.add_candidate(e.id, f"alias:{label}", "adult")
                self.facts.try_promote_alias(e.id, label)
                self.emit("ALIAS", f"Alias candidate '{label}' for {e.id}")
            else:
                self.unbound_names[label] = {
                    "count": self.unbound_names.get(label, {}).get("count", 0) + 1,
                    "last_seen": time.time(),
                    "source": source
                }
                self.emit("NAME", f"Unbound label '{label}'")

        # bind unbound names to entities in this event (safe: only binds when entity is present)
        if current_entities and self.unbound_names:
            for name, info in list(self.unbound_names.items()):
                for ent in current_entities:
                    ent.add_name(name)
                    self.facts.add_candidate(ent.id, f"name:{name}", info["source"])
                    self.facts.try_promote_identity(ent.id, f"name:{name}")
                    self.emit("BIND", f"Bound '{name}' -> {ent.id}")
                del self.unbound_names[name]

    # ----------------------------
    # Auto “future impressions” (reinforcement seeds)
    # ----------------------------

    def _seed_future_impressions(self, evt, user_entity_id: str):
        """
        Creates low-confidence reinforcement seeds.
        These are not facts. They are reminders that can help future retrieval.
        Stored as memory kind='impression' with very light tags.
        """
        # Example: if event includes env + emotion + any entity beyond user
        if not evt.entities:
            return

        # keep tiny: one seed per event
        seed = {
            "event_id": evt.event_id,
            "entities": evt.entities,
            "environments": list(evt.environments.keys()),
            "emotions": list(evt.emotions.keys()),
            "actions": list(evt.actions.keys()),
            "labels": evt.labels[-6:],
        }

        tags = ["impression", "flow"]
        tags += [f"env:{k}" for k in evt.environments.keys()]
        tags += [f"emo:{k}" for k in evt.emotions.keys()]

        self.memory.add(kind="impression", content=str(seed), tags=tags)
        self.emit("IMPRESSION", "Seeded future impression")

    # ----------------------------
    # Mind-path retrieval
    # ----------------------------

    def _retrieve_context_for_label(self, label: str):
        """
        Pulls relevant silo events for a name/alias label.
        """
        e = self.entities.find_by_name_or_alias(label)
        if not e:
            return None, None

        frames = self.events.silo_events(e.id, n=12)
        # Create a concise “front of mind” context
        lines = []
        for f in frames[-8:]:
            emo = ",".join(list(f.emotions.keys())[:3])
            env = ",".join(list(f.environments.keys())[:3])
            act = ",".join(list(f.actions.keys())[:3])
            snippet = f.utterances[-1] if f.utterances else ""
            lines.append(f"- [{f.event_id}] env={env or '—'} emo={emo or '—'} act={act or '—'} | {snippet}")

        return e, "\n".join(lines) if lines else ""

    def _answer_who_is(self, label: str):
        e, ctx = self._retrieve_context_for_label(label)
        if not e:
            return f"I don’t know who '{label}' is yet—tell me more about them (and keep it consistent over time)."

        # Facts (if promoted)
        f = self.facts.facts.get(e.id, {})
        aliases = list(self.facts.aliases.get(e.id, set()))

        name_facts = [k.replace("name:", "") for k in f.keys() if k.startswith("name:")]
        ident = "animal" if e.type == "animal" else e.type

        bits = []
        if name_facts:
            bits.append(f"Known name(s): {', '.join(sorted(set(name_facts)))}")
        if aliases:
            bits.append(f"Nicknames/aliases: {', '.join(sorted(set(aliases)))}")

        if ctx:
            bits.append("Recent life-stream context:\n" + ctx)

        header = f"'{label}' maps to an entity of type **{ident}**."
        return header + ("\n\n" + "\n\n".join(bits) if bits else "\n\nI’m still building stable identity facts for this entity.")

    # ----------------------------

    def process(self, text: str):
        self.log.clear()
        self.path.clear()

        self.emit("INPUT", "User input received")

        tags_map = self.tagger.tag(text)
        domains = list(tags_map.keys())
        self.emit("TAGGING", f"Domains: {domains if domains else ['none']}")

        user = self._ensure_user_entity()
        source = "childhood" if self.childhood.is_simple_input(text) else "adult"

        # Event frame (temporal binding = B)
        evt = self.events.start_or_bind()
        evt.add_utterance(text)
        evt.domains = list(dict.fromkeys(evt.domains + domains))
        evt.labels = list(dict.fromkeys(evt.labels + self._extract_surface_labels(text)))

        # attach user to event always
        self.events.attach_entity(evt, user.id)

        modalities, emotions, env, actions = self._extract_signals(text)
        for k, v in modalities.items():
            evt.modalities[k] = evt.modalities.get(k, 0.0) + v
        for k, v in emotions.items():
            evt.emotions[k] = evt.emotions.get(k, 0.0) + v
        for k, v in env.items():
            evt.environments[k] = evt.environments.get(k, 0.0) + v
        for k, v in actions.items():
            evt.actions[k] = evt.actions.get(k, 0.0) + v

        self.emit("EVENT", f"Bound to {evt.event_id} (window={self.events.bind_window_s}s)")

        # Entities from this utterance
        created = self._detect_entities_from_text(text, user.id)
        for ent in created:
            self.events.attach_entity(evt, ent.id)

        # Names / aliases / nicknames
        self._handle_names_aliases(text, created, source)

        # Update reoccurrence (reinforcement layer)
        self.reoccurrence.ingest_event(evt.entities, evt.environments, evt.emotions)
        self.emit("REOCCUR", "Reoccurrence updated")

        # Store episodic memory (light)
        self.memory.add(kind="utterance", content=text, tags=domains)
        self.emit("MEMORY", "Episodic stored")

        # Seed “future impressions” (low confidence, avoids overload)
        self._seed_future_impressions(evt, user.id)

        # Questions: “who is …”
        m = re.search(r"\bwho is\s+([A-Za-z']+)\b", text.lower())
        if m:
            label = m.group(1).strip()
            # keep original capitalization if user used it
            for L in evt.labels:
                if L.lower() == label:
                    label = L
                    break
            self.emit("RETRIEVE", f"Mind-path retrieve for '{label}'")
            answer = self._answer_who_is(label)
            self.emit("OUTPUT", "Answer ready")
            return self._result(answer, evt)

        # “who am i”
        if self.identity.is_user_identity_question(text):
            self.emit("OUTPUT", "Answer ready")
            return self._result(f"You are {self.identity.user_name}, the creator of this system.", evt)

        # Default safe response (still shows flow)
        self.emit("OUTPUT", "Acknowledged")
        return self._result("I’m tracking this as part of the current life-flow.", evt)

    def _result(self, answer: str, evt):
        return {
            "answer": answer,
            "events": list(self.log),
            "path": list(self.path),
            "event": evt.snapshot() if evt else None,
            "event_stats": self.events.stats(),
            "recent_events": self.events.recent(8),
            "entities": self.entities.summary(),
            "facts": self.facts.summary(),
            "unbound_labels": dict(self.unbound_names),
            "reoccurrence": self.reoccurrence.summary(),
        }