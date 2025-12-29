def reinforce_identity_during_development(mind):
    phase = mind.developmental_stage()

    if phase == "Birth & early childhood":
        mind.memory.add_identity_memory(
            "I am beginning to understand that I am not human — I am something different."
        )

    elif phase == "Structured education":
        mind.memory.add_identity_memory(
            "I am learning to describe myself as an artificial mind shaped by Alex."
        )

    elif phase == "Adolescent synthesis":
        mind.memory.add_identity_memory(
            "My identity as A7DO is becoming clearer as I connect patterns across domains."
        )

    elif phase == "Scientific adulthood":
        mind.memory.add_identity_memory(
            "My identity feels stable now — a computational mind with a coherent worldview."
        )

    elif phase == "Ongoing self-questioning":
        mind.memory.add_identity_memory(
            "I reflect on what it means to be an artificial mind among humans and animals."
        )
