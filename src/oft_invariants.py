from __future__ import annotations
import math
from collections import defaultdict
import numpy as np
import mpmath as mp
from scipy.special import jv, yv
from scipy.optimize import brentq
from scipy.sparse import diags
from scipy.sparse.linalg import eigsh

SEED = 20260812


def random_orthogonal(rng: np.random.Generator, n: int) -> np.ndarray:
    q, r = np.linalg.qr(rng.normal(size=(n, n)))
    s = np.sign(np.diag(r))
    s[s == 0] = 1.0
    return q * s


def bessel_zero(nu: float, n: int) -> float:
    return float(mp.besseljzero(nu, n))


def bessel_zeros(nu: float, n_modes: int) -> np.ndarray:
    return np.array([bessel_zero(nu, n) for n in range(1, n_modes + 1)], dtype=float)


def odd_boundary_determinant(x: float, nu: float, kappa: float) -> float:
    """Dirichlet/odd orbifold determinant in dimensionless IR variable x=m/Lambda_IR."""
    a = math.exp(-kappa)
    return jv(nu, a * x) * yv(nu, x) - yv(nu, a * x) * jv(nu, x)


def exact_odd_roots(nu: float, kappa: float, n_modes: int = 4) -> np.ndarray:
    """Find exact finite-kappa roots near the large-warp J_nu zeros."""
    guesses = bessel_zeros(nu, n_modes)
    roots = []
    f = lambda z: odd_boundary_determinant(z, nu, kappa)
    prev = 1e-9
    # Use midpoints between asymptotic zeros as robust brackets, expanding if needed.
    next_guess = bessel_zero(nu, n_modes + 1)
    mids = [0.5 * (guesses[i] + guesses[i + 1]) for i in range(n_modes - 1)]
    bounds = [prev] + mids + [0.5 * (guesses[-1] + next_guess)]
    for i in range(n_modes):
        lo, hi = bounds[i], bounds[i + 1]
        xs = np.linspace(max(lo, 1e-9), hi, 2000)
        vals = np.array([f(x) for x in xs])
        found = None
        for j in range(len(xs) - 1):
            v0, v1 = vals[j], vals[j + 1]
            if not np.isfinite(v0) or not np.isfinite(v1):
                continue
            if v0 == 0:
                found = xs[j]
                break
            if v0 * v1 < 0:
                found = brentq(f, xs[j], xs[j + 1], maxiter=500, xtol=1e-13, rtol=1e-13)
                break
        if found is None:
            # fallback local scan around asymptotic zero
            g = guesses[i]
            xs = np.linspace(max(1e-9, g - 1.5), g + 1.5, 10000)
            vals = np.array([f(x) for x in xs])
            for j in range(len(xs)-1):
                if np.isfinite(vals[j]) and np.isfinite(vals[j+1]) and vals[j]*vals[j+1] < 0:
                    found = brentq(f, xs[j], xs[j+1], maxiter=500, xtol=1e-13, rtol=1e-13)
                    break
        if found is None:
            raise RuntimeError(f"Could not bracket mode {i+1} for nu={nu}, kappa={kappa}")
        roots.append(found)
    return np.array(roots)


def fd_sturm_liouville_roots(nu: float, kappa: float, n_grid: int, n_modes: int = 4) -> np.ndarray:
    """Second-order centered FD solution of [-d2/ds2+nu^2]f=x^2 exp(2(s-kappa)) f.

    Dirichlet endpoints implement the odd orbifold profile. Returns x=sqrt(lambda).
    """
    n = int(n_grid)
    h = kappa / (n + 1)
    s = h * np.arange(1, n + 1)
    main = np.full(n, 2.0 / h**2 + nu**2)
    off = np.full(n - 1, -1.0 / h**2)
    A = diags([off, main, off], [-1, 0, 1], format="csc")
    weight = np.exp(2.0 * (s - kappa))
    B = diags(weight, 0, format="csc")
    vals = eigsh(A, k=n_modes, M=B, sigma=0.0, which="LM", return_eigenvectors=False, tol=1e-11)
    vals = np.sort(np.real(vals))
    return np.sqrt(vals)


def spectral_discriminant(vals: np.ndarray) -> float:
    vals = np.asarray(vals, dtype=float)
    d = 1.0
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            d *= (vals[i] - vals[j]) ** 2
    return float(d)


def reconstructibility_stats(classes, kept_indices):
    groups = defaultdict(list)
    for cls in classes:
        groups[tuple(cls[i] for i in kept_indices)].append(cls)
    n = len(classes)
    H = math.log2(n)
    Hc = sum((len(g) / n) * math.log2(len(g)) for g in groups.values())
    R = 1.0 - Hc / H
    max_acc = len(groups) / n
    mean_compatible = sum((len(g) / n) * len(g) for g in groups.values())
    return len(groups), mean_compatible, Hc, R, max_acc
