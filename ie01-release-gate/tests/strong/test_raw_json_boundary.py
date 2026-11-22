"""Raw serialized JSON boundary: repeated members are parser errors, not fabricated gate Evaluations."""
import pytest

from fixtures_loader import RAW
from ie01_gate import DuplicateKeyError, ParserError, evaluate_envelope, parse_strict_json

EXPECT = {
    "R-DUP-TOP-RESULTS": ("DuplicateKeyError", "DUPLICATE_KEY"),
    "R-DUP-ROW-STATUS": ("DuplicateKeyError", "DUPLICATE_KEY"),
    "R-NONSTANDARD-NAN": ("ParserError", "NONSTANDARD_CONSTANT"),
    "R-TRUNCATED": ("ParserError", "MALFORMED_JSON"),
    "R-OK-C1": (None, {"decision": "ALLOW", "reasons": [], "warnings": []}),
}


@pytest.mark.parametrize("raw_id", sorted(EXPECT))
def test_raw(raw_id):
    text = (RAW / f"{raw_id}.json").read_bytes()
    error_class, expected = EXPECT[raw_id]
    try:
        parsed = parse_strict_json(text)
        outcome = ("parsed", evaluate_envelope(parsed))
    except ParserError as exc:
        outcome = (type(exc).__name__, exc.kind)
    assert outcome == ((error_class, expected) if error_class else ("parsed", expected))
    if error_class == "DuplicateKeyError":
        assert issubclass(DuplicateKeyError, ParserError)
