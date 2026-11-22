"""Strict raw-JSON boundary: duplicate members are a transport/parser error, never a gate Evaluation."""
import json


class ParserError(ValueError):
    """Raised for text that is not acceptable strict JSON. `kind` is a stable code; diagnostics carry no values."""

    def __init__(self, kind, detail):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail = kind, detail


class DuplicateKeyError(ParserError):
    pass


def _reject_duplicates(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise DuplicateKeyError("DUPLICATE_KEY", f"object member name {key!r} repeated")
        seen.add(key)
    return dict(pairs)


def _reject_constant(name):
    raise ParserError("NONSTANDARD_CONSTANT", f"{name} is not valid JSON (RFC 8259)")


def parse_strict_json(text):
    """Parse JSON text, rejecting repeated member names at any depth and NaN/Infinity."""
    if isinstance(text, (bytes, bytearray)):
        try:
            text = bytes(text).decode("utf-8")
        except UnicodeDecodeError:
            raise ParserError("ENCODING", "input is not UTF-8") from None
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
    except ParserError:
        raise
    except json.JSONDecodeError as exc:
        raise ParserError("MALFORMED_JSON", f"line {exc.lineno} column {exc.colno}") from None
