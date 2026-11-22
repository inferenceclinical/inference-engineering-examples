"""CLI: python -m ie01_gate [FILE|-]

Reads one raw JSON envelope. Exit 0 with the Evaluation JSON on stdout (whatever the decision);
exit 2 with a ParserError line on stderr and nothing on stdout; exit 3 for usage errors.
"""
import json
import sys

from .gate import evaluate_envelope
from .parser import ParserError, parse_strict_json


def main(argv):
    if len(argv) > 1:
        print("usage: python -m ie01_gate [FILE|-]", file=sys.stderr)
        return 3
    source = argv[0] if argv else "-"
    try:
        raw = sys.stdin.buffer.read() if source == "-" else open(source, "rb").read()
    except OSError as exc:
        print(f"usage: cannot read {source}: {exc.strerror}", file=sys.stderr)
        return 3
    try:
        envelope = parse_strict_json(raw)
    except ParserError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(evaluate_envelope(envelope), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
