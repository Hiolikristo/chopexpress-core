from typing import Any, Dict


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    checks = {
        "background_check_passed": bool(payload.get("background_check_passed", False)),
        "identity_verified": bool(payload.get("identity_verified", False)),
        "license_valid": bool(payload.get("license_valid", False)),
        "insurance_valid": bool(payload.get("insurance_valid", False)),
        "vehicle_registration_valid": bool(payload.get("vehicle_registration_valid", False)),
        "recertification_up_to_date": bool(payload.get("recertification_up_to_date", False)),
    }

    reasons = [f"{name} is not satisfied." for name, ok in checks.items() if not ok]
    passed = all(checks.values())

    return {
        "driver_id": payload.get("driver_id", "unknown"),
        "eligible_for_activation": passed,
        "checks": checks,
        "reasons": reasons,
        "compliance_status": "approved" if passed else "hold",
    }


def driver_compliance(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def driver_compliance_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)