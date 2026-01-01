def generate_day_schedule(world, day):
    """
    AI-driven but SAFE schedule generator.
    No invention. Uses only world profile.
    """

    events = []

    # People introduction
    for name in world.people:
        events.append(f"this is {name.lower()}")

    # Pets introduction
    for pet in world.pets:
        events.append(f"this is {pet.lower()}")

    # Objects introduction
    for obj in world.objects:
        events.append(f"look {obj.lower()}")

    # Limit infant learning
    return events[:5]