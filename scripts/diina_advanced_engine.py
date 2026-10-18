#!/usr/bin/env python3
"""
DIINA Advanced Engine v1.0
==========================
A pure-Python (standard library only) advanced engine implementing
the core machine-learning and optimization concepts covered by the
DIINA research benchmark (supervised learning, gradient descent,
backpropagation, regularization, cross-validation, metrics, and
ensemble-style evaluation).

This module is self-contained and requires no third-party packages.

Usage:
    python diina_advanced_engine.py            # run the full demo
    python diina_advanced_engine.py --quick    # run with reduced iterations
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

__version__ = "1.0.0"
__author__ = "DIINA Advanced Engine"

# ----------------------------------------------------------------------------
# Section 1: Activation functions
# ----------------------------------------------------------------------------


def relu(z: float) -> float:
    """Rectified Linear Unit: max(0, z)."""
    return max(0.0, z)


def relu_grad(z: float) -> float:
    """Derivative of ReLU."""
    return 1.0 if z > 0 else 0.0


def sigmoid(z: float) -> float:
    """Logistic sigmoid: 1 / (1 + e^-z)."""
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


def sigmoid_grad(a: float) -> float:
    """Derivative of sigmoid given its output a = sigmoid(z)."""
    return a * (1.0 - a)


def tanh(z: float) -> float:
    """Hyperbolic tangent."""
    return math.tanh(z)


def tanh_grad(a: float) -> float:
    """Derivative of tanh given its output a = tanh(z)."""
    return 1.0 - a * a


ACTIVATIONS: Dict[str, Tuple[Callable[[float], float], Callable[[float], float]]] = {
    "relu": (relu, relu_grad),
    "sigmoid": (sigmoid, sigmoid_grad),
    "tanh": (tanh, tanh_grad),
}


# ----------------------------------------------------------------------------
# Section 2: Loss functions
# ----------------------------------------------------------------------------


def mse_loss(y_hat: float, y: float) -> float:
    """Mean squared error (single sample): 0.5 * (y_hat - y)^2."""
    d = y_hat - y
    return 0.5 * d * d


def mse_grad(y_hat: float, y: float) -> float:
    """Gradient of MSE w.r.t. prediction: (y_hat - y)."""
    return y_hat - y


def binary_cross_entropy(y_hat: float, y: float, eps: float = 1e-12) -> float:
    """Binary cross-entropy for a single sample."""
    p = min(max(y_hat, eps), 1.0 - eps)
    return -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))


def binary_cross_entropy_grad(y_hat: float, y: float, eps: float = 1e-12) -> float:
    """Gradient of BCE w.r.t. the predicted probability."""
    p = min(max(y_hat, eps), 1.0 - eps)
    return (p - y) / (p * (1.0 - p))


LOSSES: Dict[str, Tuple[Callable[[float, float], float], Callable[[float, float], float]]] = {
    "mse": (mse_loss, mse_grad),
    "bce": (binary_cross_entropy, binary_cross_entropy_grad),
}


# ----------------------------------------------------------------------------
# Section 3: Regularization penalties (L1 / L2)
# ----------------------------------------------------------------------------


def l1_penalty(weights: Sequence[float], lam: float) -> float:
    """L1 (Lasso) penalty: lambda * sum |w_j|."""
    return lam * sum(abs(w) for w in weights)


def l2_penalty(weights: Sequence[float], lam: float) -> float:
    """L2 (Ridge) penalty: lambda * sum w_j^2."""
    return lam * sum(w * w for w in weights)


REGULARIZERS: Dict[str, Callable[[Sequence[float], float], float]] = {
    "l1": l1_penalty,
    "l2": l2_penalty,
    "none": lambda w, lam: 0.0,
}


# ----------------------------------------------------------------------------
# Section 4: Linear / logistic regression trained by gradient descent
# ----------------------------------------------------------------------------


@dataclass
class TrainReport:
    """Container for training-run statistics and diagnostics."""
    final_loss: float
    train_metric: float
    val_metric: Optional[float] = None
    epochs: int = 0
    weight_history: List[List[float]] = field(default_factory=list)
    loss_history: List[float] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def summary(self) -> Dict[str, object]:
        return {
            "final_loss": round(self.final_loss, 6),
            "train_metric": round(self.train_metric, 6),
            "val_metric": round(self.val_metric, 6) if self.val_metric is not None else None,
            "epochs": self.epochs,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
        }


class GradientDescentRegressor:
    """
    Linear/logistic regression trained with mini-batch gradient descent.

    Supports:
      * L1 / L2 regularization
      * configurable learning rate
      * training/validation loss tracking (overfitting diagnostics)
    """

    def __init__(
        self,
        learning_rate: float = 0.05,
        epochs: int = 200,
        batch_size: int = 16,
        regularization: str = "l2",
        reg_lambda: float = 1e-3,
        loss: str = "mse",
        activation: Optional[str] = None,
        seed: int = 42,
        verbose: bool = False,
    ) -> None:
        if learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        self.lr = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size
        self.reg_name = regularization
        if regularization not in REGULARIZERS:
            raise ValueError(f"unknown regularization {regularization!r}")
        self.reg_fn = REGULARIZERS[regularization]
        self.reg_lambda = reg_lambda
        self.loss_name = loss
        if loss not in LOSSES:
            raise ValueError(f"unknown loss {loss!r}")
        self.loss_fn, self.loss_grad_fn = LOSSES[loss]
        self.act_name = activation
        self.act_fn, self.act_grad_fn = ACTIVATIONS[activation] if activation else (lambda z: z, lambda z: 1.0)
        self.seed = seed
        self.verbose = verbose
        self.weights: List[float] = []
        self.bias: float = 0.0

    # -- model ---------------------------------------------------------------

    def _forward_one(self, x: Sequence[float]) -> Tuple[float, float]:
        z = self.bias + sum(w * xi for w, xi in zip(self.weights, x))
        a = self.act_fn(z)
        return z, a

    def predict(self, X: Sequence[Sequence[float]]) -> List[float]:
        return [self._forward_one(x)[1] for x in X]

    # -- training ------------------------------------------------------------

    def fit(
        self,
        X: Sequence[Sequence[float]],
        y: Sequence[float],
        X_val: Optional[Sequence[Sequence[float]]] = None,
        y_val: Optional[Sequence[float]] = None,
    ) -> "TrainReport":
        if len(X) != len(y):
            raise ValueError("X and y must have the same length")
        rng = random.Random(self.seed)
        n, d = len(X), len(X[0])
        self.weights = [rng.gauss(0.0, 0.01) for _ in range(d)]
        self.bias = 0.0

        t0 = time.perf_counter()
        loss_history: List[float] = []
        weight_history: List[List[float]] = []

        for epoch in range(self.epochs):
            indices = list(range(n))
            rng.shuffle(indices)
            epoch_loss = 0.0
            for start in range(0, n, self.batch_size):
                batch = indices[start:start + self.batch_size]
                if not batch:
                    continue
                grad_w = [0.0] * d
                grad_b = 0.0
                for idx in batch:
                    x = X[idx]
                    z, a = self._forward_one(x)
                    y_hat = a
                    y_true = y[idx]
                    epoch_loss += self.loss_fn(y_hat, y_true)
                    dl = self.loss_grad_fn(y_hat, y_true)
                    da = self.act_grad_fn(a)
                    delta = dl * da          # chain rule
                    for j in range(d):
                        grad_w[j] += delta * x[j]
                    grad_b += delta
                m = len(batch)
                # regularization gradient contribution
                for j in range(d):
                    if self.reg_name == "l1":
                        grad_w[j] += self.reg_lambda * (1.0 if self.weights[j] > 0 else -1.0)
                    elif self.reg_name == "l2":
                        grad_w[j] += self.reg_lambda * 2.0 * self.weights[j]
                for j in range(d):
                    self.weights[j] -= self.lr * grad_w[j] / m
                self.bias -= self.lr * grad_b / m
            mean_loss = epoch_loss / n
            loss_history.append(mean_loss)
            weight_history.append(list(self.weights))
            if self.verbose and (epoch % max(1, self.epochs // 10) == 0 or epoch == self.epochs - 1):
                print(f"  [epoch {epoch + 1:4d}/{self.epochs}] loss = {mean_loss:.6f}")

        elapsed = time.perf_counter() - t0
        train_preds = self.predict(X)
        train_metric = self.score(y, train_preds)
        val_metric = None
        if X_val is not None and y_val is not None:
            val_preds = self.predict(X_val)
            val_metric = self.score(y_val, val_preds)

        return TrainReport(
            final_loss=loss_history[-1] if loss_history else float("nan"),
            train_metric=train_metric,
            val_metric=val_metric,
            epochs=self.epochs,
            weight_history=weight_history,
            loss_history=loss_history,
            elapsed_seconds=elapsed,
        )

    def score(self, y_true: Sequence[float], y_pred: Sequence[float]) -> float:
        """Return accuracy for classification losses, R^2 for regression."""
        if self.loss_name == "bce":
            correct = sum(
                1 for p, t in zip(y_pred, y_true)
                if (1.0 if p >= 0.5 else 0.0) == t
            )
            return correct / len(y_true) if y_true else 0.0
        mean_t = sum(y_true) / len(y_true) if y_true else 0.0
        ss_res = sum((t - p) ** 2 for p, t in zip(y_pred, y_true))
        ss_tot = sum((t - mean_t) ** 2 for t in y_true)
        return 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0


# ----------------------------------------------------------------------------
# Section 5: Classification metrics (confusion-matrix based)
# ----------------------------------------------------------------------------


def confusion_matrix(y_true: Sequence[float], y_pred: Sequence[float], threshold: float = 0.5) -> Dict[str, int]:
    """Compute binary confusion-matrix counts."""
    tp = fp = tn = fn = 0
    for p, t in zip(y_pred, y_true):
        pred_pos = (p >= threshold)
        if pred_pos and t == 1:
            tp += 1
        elif pred_pos and t == 0:
            fp += 1
        elif (not pred_pos) and t == 0:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def precision_recall_f1(y_true: Sequence[float], y_pred: Sequence[float], threshold: float = 0.5) -> Dict[str, float]:
    """Precision, Recall and F1-score from a binary confusion matrix."""
    cm = confusion_matrix(y_true, y_pred, threshold)
    tp, fp, fn = cm["tp"], cm["fp"], cm["fn"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


# ----------------------------------------------------------------------------
# Section 6: K-Fold cross-validation
# ----------------------------------------------------------------------------


def kfold_indices(n: int, k: int, rng: random.Random) -> List[List[int]]:
    """Generate k disjoint folds of index lists."""
    indices = list(range(n))
    rng.shuffle(indices)
    folds: List[List[int]] = [[] for _ in range(k)]
    for i, idx in enumerate(indices):
        folds[i % k].append(idx)
    return folds


def kfold_cross_validate(
    X: Sequence[Sequence[float]],
    y: Sequence[float],
    k: int = 5,
    seed: int = 42,
    **model_kwargs: object,
) -> Dict[str, float]:
    """Run k-fold cross-validation and return mean/std of the metric."""
    if k < 2:
        raise ValueError("k must be >= 2")
    n = len(X)
    rng = random.Random(seed)
    folds = kfold_indices(n, k, rng)
    scores: List[float] = []
    for fold_idx, val_idx in enumerate(folds):
        val_set = set(val_idx)
        train_idx = [i for i in range(n) if i not in val_set]
        X_train = [X[i] for i in train_idx]
        y_train = [y[i] for i in train_idx]
        X_val = [X[i] for i in val_idx]
        y_val = [y[i] for i in val_idx]
        model = GradientDescentRegressor(**model_kwargs)  # type: ignore[arg-type]
        model.fit(X_train, y_train)
        preds = model.predict(X_val)
        s = model.score(y_val, preds)
        scores.append(s)
        if model.verbose:
            print(f"  fold {fold_idx + 1}/{k}: score = {s:.4f}")
    mean_score = statistics.fmean(scores) if scores else 0.0
    std_score = statistics.pstdev(scores) if len(scores) > 1 else 0.0
    return {"mean": mean_score, "std": std_score, "folds": k, "scores": scores}  # type: ignore[dict-item]


# ----------------------------------------------------------------------------
# Section 7: Synthetic data generators (pure standard library)
# ----------------------------------------------------------------------------


def make_regression_data(
    n: int = 200,
    noise: float = 0.1,
    seed: int = 0,
) -> Tuple[List[List[float]], List[float]]:
    """Synthetic linear regression data: y = 3x1 - 2x2 + 1.5x3 + noise."""
    rng = random.Random(seed)
    X: List[List[float]] = []
    y: List[float] = []
    for _ in range(n):
        x = [rng.uniform(-2.0, 2.0) for _ in range(3)]
        target = 3.0 * x[0] - 2.0 * x[1] + 1.5 * x[2] + rng.gauss(0.0, noise)
        X.append(x)
        y.append(target)
    return X, y


def make_classification_data(
    n: int = 200,
    seed: int = 0,
) -> Tuple[List[List[float]], List[float]]:
    """Synthetic binary classification data (two Gaussian blobs)."""
    rng = random.Random(seed)
    X: List[List[float]] = []
    y: List[float] = []
    for i in range(n):
        label = i % 2
        center = [1.5, 1.5, 1.5] if label == 1 else [-1.5, -1.5, -1.5]
        x = [c + rng.gauss(0.0, 1.0) for c in center]
        X.append(x)
        y.append(float(label))
    return X, y


def train_test_split(
    X: Sequence[Sequence[float]],
    y: Sequence[float],
    test_size: float = 0.2,
    seed: int = 42,
) -> Tuple[List[List[float]], List[List[float]], List[float], List[float]]:
    """Simple shuffled train/test split."""
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be in (0, 1)")
    rng = random.Random(seed)
    idx = list(range(len(X)))
    rng.shuffle(idx)
    n_test = max(1, int(len(X) * test_size))
    test_idx = idx[:n_test]
    train_idx = idx[n_test:]
    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]
    return X_train, X_test, y_train, y_test


# ----------------------------------------------------------------------------
# Section 8: Demonstration / self-test pipeline
# ----------------------------------------------------------------------------


def demo(quick: bool = False) -> Dict[str, object]:
    """Run the full DIINA advanced-engine demonstration pipeline."""
    print("=" * 72)
    print(f" DIINA Advanced Engine v{__version__} — pure standard-library demo")
    print("=" * 72)

    results: Dict[str, object] = {}

    # --- 1. Regression with gradient descent + L2 regularization -------------
    print("\n[1] Regression task — mini-batch gradient descent (L2)")
    X_reg, y_reg = make_regression_data(n=120 if quick else 300, noise=0.15, seed=7)
    X_tr, X_te, y_tr, y_te = train_test_split(X_reg, y_reg, test_size=0.25, seed=7)
    reg_model = GradientDescentRegressor(
        learning_rate=0.05,
        epochs=60 if quick else 250,
        batch_size=16,
        regularization="l2",
        reg_lambda=1e-3,
        loss="mse",
        activation=None,
        seed=42,
        verbose=True,
    )
    rep = reg_model.fit(X_tr, y_tr)
    preds = reg_model.predict(X_te)
    r2 = reg_model.score(y_te, preds)
    print(f"  weights      = {[round(w, 4) for w in reg_model.weights]}")
    print(f"  bias         = {reg_model.bias:.4f}")
    print(f"  test R^2     = {r2:.4f}")
    results["regression"] = {"report": rep.summary(), "test_r2": round(r2, 4)}

    # --- 2. Binary classification with logistic activation ------------------
    print("\n[2] Binary classification — logistic model (BCE loss)")
    X_cls, y_cls = make_classification_data(n=120 if quick else 300, seed=11)
    Xc_tr, Xc_te, yc_tr, yc_te = train_test_split(X_cls, y_cls, test_size=0.25, seed=11)
    cls_model = GradientDescentRegressor(
        learning_rate=0.10,
        epochs=80 if quick else 300,
        batch_size=16,
        regularization="l2",
        reg_lambda=1e-3,
        loss="bce",
        activation="sigmoid",
        seed=42,
        verbose=True,
    )
    rep_c = cls_model.fit(Xc_tr, yc_tr)
    cls_preds = cls_model.predict(Xc_te)
    acc = cls_model.score(yc_te, cls_preds)
    metrics = precision_recall_f1(yc_te, cls_preds)
    print(f"  test accuracy    = {acc:.4f}")
    print(f"  precision        = {metrics['precision']:.4f}")
    print(f"  recall           = {metrics['recall']:.4f}")
    print(f"  f1-score         = {metrics['f1']:.4f}")
    results["classification"] = {
        "report": rep_c.summary(),
        "test_accuracy": round(acc, 4),
        **{k: round(v, 4) for k, v in metrics.items()},
    }

    # --- 3. K-fold cross-validation -----------------------------------------
    print("\n[3] 5-fold cross-validation on classification task")
    cv = kfold_cross_validate(
        X_cls, y_cls, k=5, seed=42,
        learning_rate=0.10,
        epochs=60 if quick else 250,
        batch_size=16,
        regularization="l2",
        reg_lambda=1e-3,
        loss="bce",
        activation="sigmoid",
    )
    print(f"  folds  = {cv['folds']}")
    print(f"  scores = {[round(s, 4) for s in cv['scores']]}")  # type: ignore[index]
    print(f"  mean   = {cv['mean']:.4f}  (std = {cv['std']:.4f})")
    results["cross_validation"] = {
        "mean": round(cv["mean"], 4),  # type: ignore[arg-type]
        "std": round(cv["std"], 4),    # type: ignore[arg-type]
        "folds": cv["folds"],
        "scores": [round(s, 4) for s in cv["scores"]],  # type: ignore[union-attr]
    }

    # --- 4. L1 vs L2 comparison ---------------------------------------------
    print("\n[4] L1 vs L2 regularization comparison (regression task)")
    comparison: Dict[str, Dict[str, float]] = {}
    for reg in ("l1", "l2", "none"):
        m = GradientDescentRegressor(
            learning_rate=0.05,
            epochs=60 if quick else 200,
            batch_size=16,
            regularization=reg,
            reg_lambda=5e-3,
            loss="mse",
            seed=42,
        )
        m.fit(X_tr, y_tr)
        p = m.predict(X_te)
        s = m.score(y_te, p)
        n_zero = sum(1 for w in m.weights if abs(w) < 1e-3)
        comparison[reg] = {"test_r2": round(s, 4), "near_zero_weights": n_zero}
        print(f"  reg={reg:<5s} test R^2 = {s:.4f}  near-zero weights = {n_zero}")
    results["regularization_comparison"] = comparison

    # --- 5. Learning-rate sensitivity ---------------------------------------
    print("\n[5] Learning-rate sensitivity (regression task)")
    lr_results: Dict[str, float] = {}
    for lr in (0.01, 0.05, 0.20, 0.60):
        m = GradientDescentRegressor(
            learning_rate=lr,
            epochs=40 if quick else 150,
            batch_size=16,
            regularization="none",
            loss="mse",
            seed=42,
        )
        r = m.fit(X_tr, y_tr)
        lr_results[str(lr)] = round(r.final_loss, 5)
        print(f"  lr = {lr:<5} final training loss = {r.final_loss:.6f}")
    results["learning_rate_sensitivity"] = lr_results

    print("\n" + "=" * 72)
    print(" DIINA Advanced Engine demo finished successfully.")
    print("=" * 72)
    return results


def _in_jupyter_kernel() -> bool:
    """Return True when running inside an interactive Jupyter/IPython kernel.

    Jupyter passes a ``-f <path>/kernel-<uuid>.json`` connection-file argument
    to the kernel process, which argparse would otherwise reject.
    """
    try:
        return any(a == "-f" or a.endswith("kernel.json") for a in sys.argv[1:])
    except Exception:
        return False


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="diina_advanced_engine",
        description="DIINA Advanced Engine — pure standard-library ML demo.",
    )
    parser.add_argument("--quick", action="store_true", help="run with reduced iteration counts")
    parser.add_argument("--json", action="store_true", help="emit machine-readable summary at the end")

    # Notebook-safe parsing: Jupyter injects `-f .../kernel-<uuid>.json` into
    # sys.argv when this file is run inside a notebook cell (e.g. via %run).
    # parse_known_args ignores such extra arguments instead of raising
    # SystemExit(2). Explicit argv keeps normal CLI behavior intact.
    if argv is not None:
        args, _unknown = parser.parse_known_args(argv)
    elif _in_jupyter_kernel():
        args, _unknown = parser.parse_known_args([])
    else:
        args, _unknown = parser.parse_known_args()
    try:
        results = demo(quick=args.quick)
    except Exception as exc:  # pragma: no cover
        print(f"[FATAL] DIINA engine error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    code = main()
    # do NOT call sys.exit in IPython/Jupyter environment:
    if not _in_jupyter_kernel():
        sys.exit(code)
