"""ANCOVA/CUPED-style covariate adjustment: Y_adj = Y - theta*(X - x_mean).

theta is estimated pooled across arms on PRE-injection data so the synthetic
effect cannot contaminate it (Deng et al. 2013, generalized to any
pre-treatment covariate). See docs/adr/0007-covariate-adjustment-not-cuped.md.
"""

import numpy as np
from numpy.typing import NDArray


def cuped_theta(y: NDArray[np.float64], x: NDArray[np.float64]) -> float:
    """theta = cov(Y, X) / var(X), estimated treatment-independently."""
    var_x = float(np.var(x, ddof=1))
    if var_x == 0.0:
        raise ValueError("covariate has zero variance; cannot estimate theta")
    cov_yx = float(np.cov(y, x)[0, 1])
    return cov_yx / var_x


def cuped_adjust(
    y: NDArray[np.float64],
    x: NDArray[np.float64],
    theta: float,
    x_mean: float,
) -> NDArray[np.float64]:
    """Adjusted outcome with same expected arm difference, lower variance."""
    return np.asarray(y - theta * (x - x_mean), dtype=np.float64)
