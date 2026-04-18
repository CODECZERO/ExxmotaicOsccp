"""shared.normalizer — Version-aware OCPP data normalization."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)



def normalize_boot_v16(
    charge_point_vendor: str,
    charge_point_model: str,
    **kwargs,
) -> Dict[str, Any]:
    """Normalize a V16 BootNotification into a charger upsert dict."""
    return {
        "vendor": charge_point_vendor,
        "model": charge_point_model,
        "serial_number": kwargs.get("charge_point_serial_number"),
        "firmware_version": kwargs.get("firmware_version"),
        "ocpp_version": "1.6",
    }


def normalize_boot_v201(
    charging_station: dict,
    reason: str,
    **kwargs,
) -> Dict[str, Any]:
    """Normalize a V201 BootNotification into a charger upsert dict."""
    return {
        "vendor": charging_station.get("vendor_name", ""),
        "model": charging_station.get("model", ""),
        "serial_number": charging_station.get("serial_number"),
        "firmware_version": charging_station.get("firmware_version"),
        "ocpp_version": "2.0.1",
    }



def normalize_status_v16(
    connector_id: int,
    error_code: str,
    status: str,
    **kwargs,
) -> Dict[str, Any]:
    """Normalize a V16 StatusNotification."""
    return {
        "connector_id": connector_id,
        "evse_id": 1,  # V16 has no EVSE concept — default to 1
        "status": status,
        "error_code": error_code,
    }


def normalize_status_v201(
    timestamp: str,
    connector_status: str,
    evse_id: int,
    connector_id: int,
    **kwargs,
) -> Dict[str, Any]:
    """Normalize a V201 StatusNotification."""
    return {
        "connector_id": connector_id,
        "evse_id": evse_id,
        "status": connector_status,
        "error_code": None,  # V201 StatusNotification has no error_code
    }



def normalize_start_tx_v16(
    connector_id: int,
    id_tag: str,
    meter_start: int,
    timestamp: str,
    **kwargs,
) -> Dict[str, Any]:
    """Normalize a V16 StartTransaction into a session creation dict."""
    return {
        "connector_id": connector_id,
        "evse_id": 1,
        "id_tag": id_tag,
        "meter_start": meter_start,
        "start_time": timestamp,
        "ocpp_version": "1.6",
    }



def normalize_stop_tx_v16(
    meter_stop: int,
    timestamp: str,
    transaction_id: int,
    **kwargs,
) -> Dict[str, Any]:
    """Normalize a V16 StopTransaction into a session update dict."""
    return {
        "transaction_id": str(transaction_id),
        "meter_stop": meter_stop,
        "stop_time": timestamp,
        "stop_reason": kwargs.get("reason"),
    }



def normalize_tx_event_v201(
    event_type: str,
    timestamp: str,
    trigger_reason: str,
    seq_no: int,
    transaction_info: dict,
    **kwargs,
) -> Dict[str, Any]:
    """Normalize a V201 TransactionEvent."""
    result: Dict[str, Any] = {
        "event_type": event_type,
        "transaction_id": transaction_info.get("transaction_id", ""),
        "timestamp": timestamp,
        "trigger_reason": trigger_reason,
        "seq_no": seq_no,
        "ocpp_version": "2.0.1",
    }

    # Extract optional fields
    id_token = kwargs.get("id_token")
    if id_token and isinstance(id_token, dict):
        result["id_tag"] = id_token.get("id_token", "")
    else:
        result["id_tag"] = ""

    evse = kwargs.get("evse")
    if evse and isinstance(evse, dict):
        result["evse_id"] = evse.get("id", 1)
        result["connector_id"] = evse.get("connector_id", 1)
    else:
        result["evse_id"] = 1
        result["connector_id"] = 1

    # Extract meter values if present
    meter_value = kwargs.get("meter_value")
    if meter_value:
        result["meter_value"] = meter_value

    # Stopped reason
    stopped_reason = transaction_info.get("stopped_reason")
    if stopped_reason:
        result["stop_reason"] = stopped_reason

    return result



def _parse_sampled_values(sampled_value: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    """
    Extract known measurands from a list of sampled values.
    Handles both V16 (standard) and V201 formats.
    """
    result: Dict[str, Optional[float]] = {
        "energy_wh": None,
        "power_w": None,
        "voltage": None,
        "current_a": None,
        "soc": None,
    }

    if not sampled_value:
        return result

    for sample in sampled_value:
        # Safely handle '0' which is falsy without wiping it
        val_raw = sample.get("value")
        if val_raw is None:
            val_raw = sample.get("Value")
        
        try:
            value = float(val_raw)
        except (ValueError, TypeError):
            continue

        meas_raw = sample.get("measurand")
        if meas_raw is None:
            meas_raw = sample.get("Measurand")
            
        measurand = str(meas_raw or "").lower().replace(".", "_").replace(" ", "_")

        # Unit Scaling
        unit = str(sample.get("unit") or sample.get("Unit") or "").lower()
        if unit == "kw" or unit == "kvar":
            value *= 1000
        elif unit == "kwh" or unit == "kvarh":
            value *= 1000

        if "energy" in measurand and "import" in measurand:
            result["energy_wh"] = value
        elif "power" in measurand and ("active" in measurand or not measurand) and "import" in measurand:
            result["power_w"] = value
        elif "power" in measurand and "active" in measurand:
             result["power_w"] = value # Fallback for just "Power.Active"
        elif "voltage" in measurand:
            result["voltage"] = value
        elif "current" in measurand and "import" in measurand:
            result["current_a"] = value
        elif "current" in measurand:
            result["current_a"] = value # Fallback for just "Current"
        elif "soc" in measurand:
            result["soc"] = value
        elif not measurand:
            # Default measurand is Energy.Active.Import.Register
            result["energy_wh"] = value

    return result


def normalize_meter_v16(
    connector_id: int,
    meter_value: List[Dict[str, Any]],
    **kwargs,
) -> List[Dict[str, Any]]:
    """Normalize V16 MeterValues into a list of meter reading dicts."""
    readings = []
    for mv in meter_value:
        # Check both cases for timestamp
        ts = mv.get("timestamp") or mv.get("Timestamp") or datetime.now(tz=timezone.utc).isoformat()
        
        # Check both cases for sampled values
        sampled = mv.get("sampled_value") or mv.get("sampledValue") or mv.get("SampledValue") or []
        
        parsed = _parse_sampled_values(sampled)
        readings.append({
            "connector_id": connector_id,
            "evse_id": 1,
            "timestamp": ts,
            "raw_json": sampled,
            **parsed,
        })
    return readings


def normalize_meter_v201(
    evse_id: int,
    meter_value: List[Dict[str, Any]],
    **kwargs,
) -> List[Dict[str, Any]]:
    """Normalize V201 MeterValues into a list of meter reading dicts."""
    readings = []
    for mv in meter_value:
        # Check both cases for timestamp
        ts = mv.get("timestamp") or mv.get("Timestamp") or datetime.now(tz=timezone.utc).isoformat()
        
        # Check both cases for sampled values
        sampled = mv.get("sampled_value") or mv.get("sampledValue") or mv.get("SampledValue") or []
        
        parsed = _parse_sampled_values(sampled)
        readings.append({
            "connector_id": 1,  # V201 uses evse_id as primary
            "evse_id": evse_id,
            "timestamp": ts,
            "raw_json": sampled,
            **parsed,
        })
    return readings
