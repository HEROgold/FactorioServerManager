"""Hypothesis strategies for FSM's data, with realistic values from Faker.

Hypothesis draws a seed and Faker turns it into a value, so a failing example
shrinks and replays like any other Hypothesis example.
"""

from faker import Faker  # skylos: ignore[SKY-D223] -- dev dependency
from hypothesis import strategies as st  # skylos: ignore[SKY-D223] -- dev dependency

_fake = Faker()


def _seeded(seed: int) -> Faker:
    _fake.seed_instance(seed)
    return _fake


seeds = st.integers(min_value=0, max_value=2**32 - 1)

emails = seeds.map(lambda seed: _seeded(seed).email())
display_names = seeds.map(lambda seed: _seeded(seed).user_name())
passwords = seeds.map(lambda seed: _seeded(seed).password(length=16))
# Factorio mod names: letters, digits, `-` and `_`,
# like "Krastorio2" or "even-distribution".
mod_names = st.from_regex(r"[A-Za-z][A-Za-z0-9_-]{0,30}", fullmatch=True)
