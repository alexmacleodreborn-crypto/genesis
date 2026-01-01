import random
from typing import List
from a7do.experience import ExperienceEvent

def generate_two_day_schedule(world, homeplot, seed: int = 7):
    """
    Produces two days of grounded infant learning.
    Rules:
    - every event has a room
    - agent must be mum/dad (parents) in early stage
    - includes place transitions so movement is grounded
    """
    rng = random.Random(seed)

    # Pick canonical caregivers
    mum = next((p.name for p in world.people.values() if p.role.lower() == "mum"), None)
    dad = next((p.name for p in world.people.values() if p.role.lower() == "dad"), None)

    # Require parents before schedules are meaningful
    if not mum or not dad:
        return {0: [], 1: []}

    # Ensure baseline objects exist (if you created them in world profile, we use them)
    ball = "ball" if "ball" in world.objects else None
    dog = next(iter(world.animals.keys()), None)  # first animal if any

    # Rooms (must exist in homeplot)
    hall = "hall"
    b1 = "bedroom_1"
    kitchen = "kitchen"

    def rand_pos():
        return (round(rng.uniform(0.2, 0.8), 2), round(rng.uniform(0.2, 0.8), 2))

    # Day 0: home anchors + parent + first object experience in bedroom
    day0: List[ExperienceEvent] = [
        ExperienceEvent(room=hall, agent=mum, action="said", obj="hello",
                        emphasis=["hello"], sound={"source": mum, "pattern": "soft voice", "volume": "soft"},
                        motor={"type": "still", "intensity": "low"}, pos_xy=rand_pos()),
        ExperienceEvent(room=hall, agent=dad, action="showed", obj="home",
                        emphasis=["home"], pos_xy=rand_pos()),
        # transition hall -> bedroom_1 (movement inferred)
        ExperienceEvent(room=hall, agent=dad, action="carried", obj="you",
                        emphasis=["bedroom"], to_room=b1, motor={"type": "carried", "intensity": "steady"}, pos_xy=rand_pos()),
    ]

    if ball:
        day0 += [
            ExperienceEvent(room=b1, agent=dad, action="rolled", obj=ball,
                            emphasis=[ball], motor={"type": "crawl", "intensity": "slow"},
                            sound={"source": dad, "pattern": "clap", "volume": "soft"},
                            pos_xy=rand_pos()),
            ExperienceEvent(room=b1, agent=dad, action="said", obj="catch",
                            emphasis=["catch", ball], pos_xy=rand_pos())
        ]

    # Day 1: expand — pet + kitchen + repeat ball word
    day1: List[ExperienceEvent] = [
        ExperienceEvent(room=b1, agent=mum, action="woke", obj="you",
                        emphasis=["wake"], sound={"source": mum, "pattern": "soft voice", "volume": "soft"},
                        pos_xy=rand_pos()),
        # local movement within bedroom (learning to walk metric scaffold)
        ExperienceEvent(room=b1, agent=dad, action="helped", obj="walk",
                        emphasis=["walk"], motor={"type": "walk", "intensity": "gentle"},
                        pos_xy=rand_pos()),
        # transition to kitchen
        ExperienceEvent(room=b1, agent=mum, action="led", obj="you",
                        emphasis=["kitchen"], to_room=kitchen, motor={"type": "walk", "intensity": "gentle"},
                        pos_xy=rand_pos()),
    ]

    if dog:
        day1 += [
            ExperienceEvent(room=kitchen, agent=dad, action="showed", obj=dog,
                            emphasis=[dog], sound={"source": dog, "pattern": "bark", "volume": "low"},
                            pos_xy=rand_pos()),
            ExperienceEvent(room=kitchen, agent=mum, action="said", obj="clap",
                            emphasis=["clap", dog], pos_xy=rand_pos()),
        ]

    if ball:
        day1.append(
            ExperienceEvent(room=kitchen, agent=dad, action="rolled", obj=ball,
                            emphasis=[ball], pos_xy=rand_pos())
        )

    # Cap to “infant dose”
    day0 = day0[:6]
    day1 = day1[:6]

    return {0: day0, 1: day1}