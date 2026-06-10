import pandas as pd
import pytest

from src.exceptions import ImbalanceError
from src.experiment.balance import check_balance


def test_balanced_frame_passes(frame):
    check_balance(frame)  # 3 vs 3, no raise


def test_imbalanced_frame_raises():
    df = pd.DataFrame({"variant": ["control"] * 10 + ["treatment"] * 2})
    with pytest.raises(ImbalanceError):
        check_balance(df)
