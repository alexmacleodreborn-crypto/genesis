import time
import re

from a7do.tagger import Tagger
from a7do.entities import EntityGraph
from .entity_facts import EntityFactLedger

from a7do.event_frame import EventMemory
from a7do.reoccurrence import ReoccurrenceTracker
from a7do.role_guard import LinguisticRoleGuard


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

        # Flow layer
        self.events = EventMemory(bind_window_s=20)
        self.reoccurrence = ReoccurrenceTracker()

        # Linguistic Role Guard
        self.lrg = LinguisticRoleGuard()

        # Unbound proper nouns waiting for an eligible target entity
        self.unbound_names = {}  # label -> {count,last_seen,source}

        # Debug / inspector
        self.log = []
        self.path = []

        # Lightweight signals
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

    def _ensure_user_entity(self):
        user = self.entities.find_by_name_or_alias(self.identity.user_name)
        if not user:
            user = self.entities.create("person")
            user.add_name(self.identity.user_name)
        return user

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

    def _detect_entities_from_text(self, text: str, speaker_entity_id: str):
        """
        Conservative entity detection:
        - 'dog' creates an animal entity
        - no names bound here
        """
        t = text.lower()
        created = []

        if "dog" in t:
            dog = self.entities.create("animal")
            dog.add_attribute("species:dog", 1.0)
            dog.link("owner", speaker_entity_id)
            created.append(dog)

            source = "childhood" if self.childhood.is_simple_input(text) else "adult"

            # identity:dog candidate
            self.facts.add_candidate(dog.id, "identity:dog", source)
            self.facts.try_promote_identity(dog.id, "identity:dog")

            self.emit("ENTITY", f"Detected animal entity {dog.id}")

        return created

    # ----------------------------
    # Binding logic with LRG
    # ----------------------------

    def _bind_proper_nouns(self, text: str, evt, created_entities: list, speaker, source: str):
        """
        Uses Linguistic Role Guard (LRG) rules:
        - PRONOUN / DETERMINER never bind as names
        - PROPER_NOUN binds only in naming contexts and only to eligible target
        - Aliases only promoted for already-known entities (and via time+repetition in ledger)
        """
        roles = self.lrg.classify(text)
        intent = self.lrg.speaker_intent(roles)
        naming_context = self.lrg.is_naming_context(text)

        # Track which known entities are referenced in this utterance
        referenced_entities = []

        for r in roles:
            if r.role != "PROPER_NOUN":
                continue
            existing = self.entities.find_by_name_or_alias(r.text)
            if existing:
                referenced_entities.append(existing)

        # Possessive reinforcement: "my dog ..."
        if intent["mentions_my"] and created_entities:
            # strengthen ownership candidate (still gated via identity rules)
            for ent in created_entities:
                self.facts.add_candidate(ent.id, "rel:owned_by_speaker", source)
                self.facts.try_promote_identity(ent.id, "rel:owned_by_speaker")
                self.emit("REL", f"Ownership candidate for {ent.id} (my ...)")

        # Speaker naming: "I am Alex ..." should never bind to animal.
        # We allow only reinforcing speaker entity, not creating a new entity.
        if intent["mentions_i"] and naming_context and not created_entities:
            for r in roles:
                if r.role == "PROPER_NOUN":
                    # optional: track as alias for speaker; do not overwrite creator anchor
                    self.emit("SPEAKER", f"Speaker proper noun observed: {r.text}")
            # do not bind further in speaker-centric utterance
            return

        # Determine eligible targets for naming
        # Priority: entities created this utterance (e.g., dog)
        # Else: referenced entity (if utterance is about someone already known)
        targets = []
        if created_entities:
            targets = created_entities
        elif referenced_entities:
            targets = referenced_entities

        # Process PROPER_NOUNs
        for r in roles:
            if r.role != "PROPER_NOUN":
                continue

            label = r.text
            existing = self.entities.find_by_name_or_alias(label)

            if existing:
                # If it's already a known entity, consider alias candidate only if the text suggests aliasing
                if "nickname" in text.lower() or "known as" in text.lower():
                    self.facts.add_candidate(existing.id, f"alias:{label}", "adult")
                    self.facts.try_promote_alias(existing.id, label)
                    self.emit("ALIAS", f"Alias reinforcement '{label}' -> {existing.id}")
                # Otherwise it's just a reference; no binding
                continue

            # Unknown proper noun: only bind in naming context AND only if we have a target
            if naming_context and targets:
                for ent in targets:
                    ent.add_name(label)
                    self.facts.add_candidate(ent.id, f"name:{label}", source)
                    self.facts.try_promote_identity(ent.id, f"name:{label}")
                    self.emit("BIND", f"Bound name '{label}' -> {ent.id}")
                    self.events.attach_entity(evt, ent.id)
            else:
                # store as unbound name candidate (for later binding when entity appears in same event)
                self.unbound_names[label] = {
                    "count": self.unbound_names.get(label, {}).get("count", 0) + 1,
                    "last_seen": time.time(),
                    "source": source
                }
                self.emit("NAME", f"Unbound proper noun '{label}' (no naming context or target)")

        # Late binding: if entity exists and unbound proper nouns exist AND the utterance is naming-context
        if naming_context and targets and self.unbound_names:
            for label, info in list(self.unbound_names.items()):
                for ent in targets:
                    ent.add_name(label)
                    self.facts.add_candidate(ent.id, f"name:{label}", info["source"])
                    self.facts.try_promote_identity(ent.id, f"name:{label}")
                    self.emit("BIND", f"Late-bound '{label}' -> {ent.id}")
                    self.events.attach_entity(evt, ent.id)
                del self.unbound_names[label]

    # ----------------------------
    # Auto future impressions
    # ----------------------------

    def _seed_future_impressions(self, evt):
        if not evt.entities:
            return

        seed = {
            "event_id": evt.event_id,
            "entities": evt.entities,
            "environments": list(evt.environments.keys()),
            "emotions": list(evt.emotions.keys()),
            "actions": list(evt.actions.keys()),
            "labels": evt.labels[-8:],
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
        e = self.entities.find_by_name_or_alias(label)
        if not e:
            return None, None

        frames = self.events.silo_events(e.id, n=12)
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
            return f"I don’t know who '{label}' is yet—tell me more about them consistently over time."

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

        speaker = self._ensure_user_entity()
        source = "childhood" if self.childhood.is_simple_input(text) else "adult"

        # Event frame (temporal binding)
        evt = self.events.start_or_bind()
        evt.add_utterance(text)
        evt.domains = list(dict.fromkeys(evt.domains + domains))

        # Add roles-based labels (PROPER_NOUN only, and never PRONOUN/DETERMINER)
        roles = self.lrg.classify(text)
        proper_labels = [r.text for r in roles if r.role == "PROPER_NOUN"]
        evt.labels = list(dict.fromkeys(evt.labels + proper_labels))

        # Attach speaker to event
        self.events.attach_entity(evt, speaker.id)

        # Signals
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
        created = self._detect_entities_from_text(text, speaker.id)
        for ent in created:
            self.events.attach_entity(evt, ent.id)

        # LRG binding (names/aliases/ownership)
        self._bind_proper_nouns(text, evt, created, speaker, source)

        # Reoccurrence
        self.reoccurrence.ingest_event(evt.entities, evt.environments, evt.emotions)
        self.emit("REOCCUR", "Reoccurrence updated")

        # Memory
        self.memory.add(kind="utterance", content=text, tags=domains)
        self.emit("MEMORY", "Episodic stored")

        # Impressions
        self._seed_future_impressions(evt)

        # Queries
        m = re.search(r"\bwho is\s+([A-Za-z']+)\b", text.lower())
        if m:
            label = m.group(1).strip()
            # try to restore original casing if user provided it in PROPER labels
            for L in proper_labels:
                if L.lower() == label:
                    label = L
                    break
            self.emit("RETRIEVE", f"Mind-path retrieve for '{label}'")
            answer = self._answer_who_is(label)
            self.emit("OUTPUT", "Answer ready")
            return self._result(answer, evt)

        if self.identity.is_user_identity_question(text):
            self.emit("OUTPUT", "Answer ready")
            return self._result(f"You are {self.identity.user_name}, the creator of this system.", evt)

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