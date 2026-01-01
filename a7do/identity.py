class Identity:
    def __init__(self, name: str = "A7DO", creator: str = "Alex Macleod"):
        self.name = name
        self.creator = creator

    def panel_markdown(self) -> str:
        return (
            f"**Agent:** {self.name}\n\n"
            f"**Default speaker/creator:** {self.creator}\n\n"
            f"**Core:** Entities · Objects · Relationships · Events · Experiences · Recall"
        )