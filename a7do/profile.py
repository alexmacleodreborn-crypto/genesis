from dataclasses import dataclass
from typing import List


@dataclass
class ChildProfile:
    name: str
    description: str
    thinking_style: List[str]
    sensitivities: List[str]
    strengths: List[str]


def get_alex_profile() -> ChildProfile:
    return ChildProfile(
        name="Alex-shaped template",
        description=(
            "Pattern-seeking, system-driven, high-curiosity mind with autistic/ADHD traits; "
            "prefers structure, clear rules, and deep dives into special interests."
        ),
        thinking_style=[
            "pattern",
            "system",
            "rule_based",
            "hyperfocus",
            "abstraction",
            "symbolic_mapping",
        ],
        sensitivities=[
            "overwhelm",
            "ambiguity",
            "unstructured_noise",
        ],
        strengths=[
            "abstraction",
            "long_timescale_planning",
            "cross-domain_synthesis",
            "deep_focus",
        ],
    )
