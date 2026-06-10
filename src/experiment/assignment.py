"""Person-level random assignment. Depends only on id + seed — never on outcomes."""

import hashlib

from src.constants import SEED


def assign_variant(customer_unique_id: str, seed: int = SEED) -> str:
    digest = hashlib.md5(f"{customer_unique_id}-{seed}".encode()).hexdigest()
    return "treatment" if int(digest, 16) % 2 == 1 else "control"
