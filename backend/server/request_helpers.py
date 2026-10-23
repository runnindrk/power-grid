# -------------------------------------------------------------------------------------------------
# Imports

from flask import jsonify, request

from backend.rules.common.error_codes import ErrorCode

# -------------------------------------------------------------------------------------------------
# Reading the request

def get_payload():
    """Return the request JSON object, or an empty dict if it is missing or invalid."""
    payload = request.get_json(silent=True)

    if isinstance(payload, dict):
        return payload

    return {}


def has_text(payload, names):
    """Return True if every named field of the payload is a string."""
    for name in names:
        if not isinstance(payload.get(name), str):
            return False

    return True


def has_int(payload, names):
    """Return True if every named field is an integer; a boolean does not count as an integer."""
    for name in names:
        value = payload.get(name)

        if not isinstance(value, int) or isinstance(value, bool):
            return False

    return True

# -------------------------------------------------------------------------------------------------
# Building the reply

def build_reply(code, message, price_label=None):
    """Return the JSON reply of an action: the error code, a status, a message and maybe a price."""
    body = {"error_code": code.value, "status": "ok", "message": message}
    http_status = 200

    if code != ErrorCode.E_OK:
        body["status"] = "error"
        http_status = 400

    if price_label is not None:
        body["price_label"] = price_label

    return jsonify(body), http_status
