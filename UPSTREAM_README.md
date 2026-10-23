# OFT Invariant Reduction - Reproducibility Package

This package accompanies the manuscript **Invariant Reduction and Falsification of a Warped Five-Dimensional Orbital Field Model: Quotient Geometry, Spectral Reconstruction, and Continuum-Equivalent Numerical Tests**.

## Scope
The package tests the mathematical invariant structure and a source-specific warped spectral sector of the revised OFT formulation. It does **not** claim experimental validation of OFT as a theory of nature.

## Reproduce

```bash
python -m pip install -r requirements.txt
python src/run_all_experiments.py
```

Frozen random seed: `20260812`.

The script regenerates all CSV outputs, all six figures, and `results/run_manifest.json`, which stores SHA-256 hashes for the generated result artifacts.

## Experiment registry

- E1: spectral conjugation invariance
- E2: non-isospectral perturbation control
- E3: weighted Gram invariance
- E4: overlap covariance
- E5: degenerate Higgs-block falsification
- E6: overall normalization quotient
- E7: unit quotient for `kL` and `M/k`
- E8: discriminant / critical-locus test
- E9: joint relational mixed-trace invariant
- E10: invariant-family reconstructibility ablation
- E11: finite-difference convergence of the Bessel-equivalent warped Sturm-Liouville problem
- E12: exact finite-warp boundary determinant versus the large-warp Bessel-zero approximation
- E13: numerical audit of the original OFT Appendix Table A.1
- E14: charged-lepton generation-spacing stress test

## Mathematical sector used in E11-E13

For an odd orbifold profile with Bessel order `nu` and warp modulus `kappa=kL`, define the dimensionless IR eigenvalue

`x = m / (k exp(-kL))`.

The finite-warp Dirichlet determinant is

`J_nu(x exp(-kappa)) Y_nu(x) - Y_nu(x exp(-kappa)) J_nu(x) = 0`.

Under `s=kw`, the equivalent Sturm-Liouville problem is

`[-d^2/ds^2 + nu^2] f = x^2 exp(2(s-kappa)) f`, `s in (0,kappa)`,

with Dirichlet endpoints for the odd profile. The code uses a centered second-order finite-difference scheme and a sparse generalized eigensolver.

## Evidence boundary

The finite-dimensional invariant tests and the continuum-equivalent odd-profile test establish internal mathematical properties only for the specified sectors and transformation classes. They do not demonstrate that Standard Model generations are KK modes, that higher modes are dark matter, that exactly three light generations follow, or that the model satisfies collider/precision constraints.

## Main files

- `manuscript.docx` / `manuscript.pdf`: main research article
- `supplementary_appendix.docx` / `supplementary_appendix.pdf`: detailed derivations and protocols
- `src/oft_invariants.py`: reusable numerical/invariant functions
- `src/run_all_experiments.py`: complete frozen experiment runner
- `results/all_experiments_summary.csv`: compact result table
- `results/run_manifest.json`: SHA-256 artifact manifest
