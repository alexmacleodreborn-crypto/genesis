from collections import defaultdict
from a7do.reflection import ReflectionStore


class SleepEngine:
    def __init__(self, reflection_store: ReflectionStore):
        self.reflections = reflection_store
        self.last_sleep_event = {}

    def run_for_entity(self, entity_id, event_frames):
        if len(event_frames) < 3:
            return []

        # Cluster by environment + emotion
        clusters = defaultdict(list)
        for evt in event_frames:
            key = (
                tuple(sorted(evt.environments.keys())),
                tuple(sorted(evt.emotions.keys()))
            )
            clusters[key].append(evt)

        created = []

        for (envs, emos), frames in clusters.items():
            freq = len(frames)
            consistency = len(set(f.event_id for f in frames)) / len(frames)
            breadth = (len(envs) + len(emos)) / max(1, freq)
            last_seen = max(f.t1 for f in frames)
            support = [f.event_id for f in frames]

            pattern = f"env:{','.join(envs)}|emo:{','.join(emos)}"
            rv = self.reflections.create_version(
                entity_id=entity_id,
                pattern=pattern,
                freq=freq,
                consistency=min(consistency, 1.0),
                breadth=min(breadth, 1.0),
                last_seen_ts=last_seen,
                support_events=support
            )
            created.append(rv)

        return created