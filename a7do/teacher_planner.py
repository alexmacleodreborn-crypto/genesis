from a7do.experience import ExperienceEvent

def generate_day_schedule(world, day):
    """
    Generates a grounded infant learning day.
    """

    events = []

    place = "bedroom"

    # parents must exist
    if "dad" in world.people:
        dad = "dad"
    else:
        return []

    # Example core learning
    events.append(
        ExperienceEvent(
            place=place,
            agent=dad,
            action="rolled",
            obj="ball",
            emphasis=["ball"],
            environment={
                "noise": "quiet",
                "layout": ["bed", "window"]
            }
        )
    )

    events.append(
        ExperienceEvent(
            place=place,
            agent=dad,
            action="said",
            obj="catch",
            emphasis=["catch", "ball"]
        )
    )

    return events