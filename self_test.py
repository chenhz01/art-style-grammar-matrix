#!/usr/bin/env python3
"""self_test for art-style-grammar-matrix.

Three test classes per ALIGNMENT rule 97:
  A. functional unit tests   B. error/exception paths   C. extreme edge cases
Run:  python self_test.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import art_style_grammar as m  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def main() -> int:
    # ---------------- A. functional
    card = m.compose("watercolor", "reveal")
    check("A1 compose returns all required fields",
          all(f in card for f in m.QA_REQUIRED_FIELDS))
    check("A2 reveal template has 5 steps", len(card["steps"]) == 5)
    check("A3 qa_check passes a fresh card", m.qa_check(card) == [])
    full = m.enumerate_matrix()
    check("A4 full matrix is 315 cards", len(full) == 35 * 9,
          f"got {len(full)}")
    check("A5 qa_check passes every matrix card",
          all(m.qa_check(c) == [] for c in full))
    sub = m.enumerate_matrix(styles=["ink-wash"], grammars=["compare", "zoom-drill"])
    check("A6 subset enumeration honors args", len(sub) == 2)

    # ---------------- B. error paths
    try:
        m.compose("not-a-style", "reveal")
        check("B1 unknown style raises KeyError", False)
    except KeyError:
        check("B1 unknown style raises KeyError", True)
    try:
        m.enumerate_matrix(styles=["bogus"])
        check("B2 unknown entry in enumerate raises", False)
    except KeyError:
        check("B2 unknown entry in enumerate raises", True)
    check("B3 qa_check rejects missing fields",
          m.qa_check({"style": "watercolor"}) != [])
    check("B4 qa_check rejects wrong step count",
          m.qa_check({**card, "steps": ["only-one"]}) != [])
    check("B5 qa_check flags schema mismatch",
          m.qa_check({**card, "schema": "9.9"}) != [])

    # ---------------- C. extreme edges
    check("C1 qa_check on empty dict", m.qa_check({}) != [])
    check("C2 qa_check on non-dict (string)", m.qa_check("garbage") != [])
    huge = {**card, "steps": card["steps"] * 10_000}
    check("C3 qa_check survives 50k-step card", m.qa_check(huge) != [])  # count mismatch
    unicode_card = {**card, "style": "水墨风格"}  # unicode style injection
    check("C4 qa_check rejects unicode style not in dict",
          m.qa_check(unicode_card) != [])

    with tempfile.TemporaryDirectory() as td:
        bad = os.path.join(td, "broken.json")
        with open(bad, "w", encoding="utf-8") as f:
            f.write("{not json")
        rc = m.main(["qa", "--file", bad])
        check("C5 qa CLI handles corrupted JSON (rc=2)", rc == 2)
        ok = os.path.join(td, "card.json")
        with open(ok, "w", encoding="utf-8") as f:
            json.dump(card, f)
        check("C6 qa CLI PASS on good file", m.main(["qa", "--file", ok]) == 0)
        check("C7 styles CLI exit 0", m.main(["styles"]) == 0)
        check("C8 unknown style via CLI rc=2",
              m.main(["compose", "--style", "zzz", "--grammar", "reveal"]) == 2)

    # ---------------- report
    fails = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({detail})" if detail else ""))
    print(f"\ntotal={len(RESULTS)} pass={len(RESULTS)-len(fails)} fail={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
