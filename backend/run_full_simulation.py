from __future__ import annotations

import importlib
import os
import traceback
from typing import Callable, Optional, Sequence


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM_DIR = os.path.join(BASE_DIR, "sim")
OUTPUT_DIR = os.path.join(SIM_DIR, "output")


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _resolve_callable(
    module_name: str,
    candidate_names: Sequence[str],
) -> Callable[[], object]:
    """
    Import a module dynamically and return the first callable that exists.
    """
    module = importlib.import_module(module_name)

    for name in candidate_names:
        fn = getattr(module, name, None)
        if callable(fn):
            print(f"[{module_name}] using callable: {name}()")
            return fn

    raise ImportError(
        f"No usable callable found in module '{module_name}'. "
        f"Expected one of: {', '.join(candidate_names)}"
    )


def _resolve_optional_callable(
    module_name: str,
    candidate_names: Sequence[str],
) -> Optional[Callable[[], object]]:
    """
    Same as _resolve_callable, but returns None instead of failing hard.
    Useful for optional engines.
    """
    try:
        return _resolve_callable(module_name, candidate_names)
    except Exception as exc:
        print(f"[warn] optional module '{module_name}' unavailable: {exc}")
        return None


def _resolve_market_simulator_runner() -> Callable[[], object]:
    return _resolve_callable(
        "market_simulator",
        (
            "run_market_simulation",
            "main",
            "run_simulation",
            "simulate_market",
            "run",
        ),
    )


def _resolve_dd_comparison_runner() -> Callable[[], object]:
    return _resolve_callable(
        "dd_comparison_engine",
        (
            "run_dd_comparison",
            "main",
            "run_comparison",
            "compare",
            "run",
        ),
    )


def _resolve_analytics_runner() -> Callable[[], object]:
    return _resolve_callable(
        "visual_analytics_engine",
        (
            "generate_charts",
            "main",
            "run_analytics",
            "run",
        ),
    )


def _resolve_validation_runner() -> Optional[Callable[[], object]]:
    return _resolve_optional_callable(
        "real_world_validation_engine",
        (
            "run_real_world_validation",
            "main",
            "run_validation",
            "validate_real_world",
            "run",
        ),
    )


def _resolve_gas_runner() -> Optional[Callable[[], object]]:
    return _resolve_optional_callable(
        "gas_intelligence_engine",
        (
            "main",
            "run_gas_intelligence",
            "run",
        ),
    )


def _find_real_driving_log() -> Optional[str]:
    """
    Accept either:
      sim/input/evidence/real_driving_log.csv
    or
      sim/input/real_driving_log.csv
    """
    candidates = [
        os.path.join(SIM_DIR, "input", "evidence", "real_driving_log.csv"),
        os.path.join(SIM_DIR, "input", "real_driving_log.csv"),
    ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return None


def run_market_step() -> None:
    print("\n1. Running market simulator...")
    runner = _resolve_market_simulator_runner()
    runner()


def run_dd_comparison_step() -> None:
    print("\n2. Running DoorDash comparison engine...")
    runner = _resolve_dd_comparison_runner()
    runner()


def run_analytics_step() -> None:
    print("\n3. Generating analytics charts...")
    runner = _resolve_analytics_runner()
    runner()


def run_gas_step() -> None:
    print("\n4. Running gas intelligence...")
    runner = _resolve_gas_runner()

    if runner is None:
        print("Skipping gas intelligence: no usable callable found.")
        return

    runner()


def run_real_world_validation_step() -> None:
    print("\n5. Running real-world validation...")

    log_path = _find_real_driving_log()
    if log_path is None:
        print(
            "Skipping real-world validation: missing real_driving_log.csv.\n"
            "Accepted locations:\n"
            f" - {os.path.join('sim', 'input', 'evidence', 'real_driving_log.csv')}\n"
            f" - {os.path.join('sim', 'input', 'real_driving_log.csv')}"
        )
        return

    print(f"Found real driving log: {log_path}")

    runner = _resolve_validation_runner()
    if runner is None:
        print("Skipping real-world validation: no usable callable found.")
        return

    try:
        runner()
    except FileNotFoundError as exc:
        print(f"Validation skipped due to file-path issue inside validation engine: {exc}")
    except Exception:
        print("Validation engine raised an error:")
        traceback.print_exc()


def main() -> None:
    ensure_output_dir()

    print("=" * 46)
    print("ChopExpress Full Simulation Pipeline")
    print("=" * 46)

    steps = [
        ("market simulation", run_market_step),
        ("dd comparison", run_dd_comparison_step),
        ("analytics", run_analytics_step),
        ("gas intelligence", run_gas_step),
        ("real-world validation", run_real_world_validation_step),
    ]

    failures: list[tuple[str, str]] = []

    for step_name, step_fn in steps:
        try:
            step_fn()
        except Exception as exc:
            failures.append((step_name, str(exc)))
            print(f"\n[error] step failed: {step_name}")
            traceback.print_exc()

    print("\n" + "=" * 46)
    print("Simulation complete")
    print("=" * 46)

    if failures:
        print("\nStep summary:")
        for step_name, message in failures:
            print(f" - {step_name}: {message}")
    else:
        print("\nAll steps completed without uncaught errors.")


if __name__ == "__main__":
    main()