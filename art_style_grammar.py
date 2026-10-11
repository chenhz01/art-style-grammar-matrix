#!/usr/bin/env python3
"""art-style-grammar-matrix: enumerate art-style x narration-grammar cards with a QA gate.

A skill-layer asset: a 35-style dictionary x 9 grammar dictionary (2-D orthogonal,
enumerable space) plus a delivery gate that validates generated cards before hand-off.
Pure stdlib. No network. No model calls.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys

# ---------------------------------------------------------------- dictionaries

STYLES = [
    "watercolor", "ink-wash", "cel-shaded", "stop-motion-clay", "charcoal-sketch",
    "art-deco-poster", "ukiyo-e", "risograph", "pixel-art", "blueprint-draft",
    "oil-impasto", "gouache-flat", "paper-cutout", "chalk-pastel", "woodcut",
    "linocut", "mosaic-tile", "stained-glass", "mid-century-cartoon", "rubber-hose",
    "vaporwave-grid", "brutalist-collage", "storybook-crayon", "atlas-engraving",
    "x-ray-schematic", "thermal-map", "halftone-print", "bauhaus-geometry",
    "swiss-typographic", "zine-punk", "fairy-tale-golden-age", "silhouette-theater",
    "marble-relief", "neon-noir", "botanical-plate",
]

GRAMMARS = [
    "reveal",          # start hidden -> progressive disclosure
    "compare",         # side-by-side states
    "build-up",        # components assemble stepwise
    "deconstruct",     # whole -> parts
    "timeline",        # temporal sweep
    "loop-emphasis",   # cycle a detail for retention
    "zoom-drill",      # macro -> micro
    "cause-chain",     # A causes B causes C
    "metaphor-map",    # abstract -> concrete analogy
]

CARD_SCHEMA_VERSION = "1.1"

# per-grammar step templates (narration syntax, style-agnostic)
GRAMMAR_STEPS = {
    "reveal":        ["tease", "hint", "disclose", "full-reveal", "settle"],
    "compare":       ["show-A", "show-B", "isolate-difference", "verdict"],
    "build-up":      ["empty-stage", "add-parts", "connect-parts", "name-whole"],
    "deconstruct":   ["show-whole", "split-parts", "explain-part-roles"],
    "timeline":      ["before", "turning-point", "after", "caption-span"],
    "loop-emphasis": ["introduce-detail", "loop-3x", "fade-to-context"],
    "zoom-drill":    ["macro-shot", "zoom-in", "micro-detail", "zoom-out"],
    "cause-chain":   ["state-A", "transition-arrow", "state-B", "consequence-C"],
    "metaphor-map":  ["abstract-concept", "concrete-analogy", "map-labels", "return"],
}

QA_REQUIRED_FIELDS = ["style", "grammar", "steps", "palette_hint", "motion_hint"]


class QAError(ValueError):
    """Raised when a card fails the delivery gate."""


# ---------------------------------------------------------------- core

def compose(style: str, grammar: str) -> dict:
    """Build one card: style x grammar -> styled step list + QA hints."""
    if style not in STYLES:
        raise KeyError(f"unknown style: {style!r} (see `styles` subcommand)")
    if grammar not in GRAMMARS:
        raise KeyError(f"unknown grammar: {grammar!r} (see `grammars` subcommand)")
    return {
        "schema": CARD_SCHEMA_VERSION,
        "style": style,
        "grammar": grammar,
        "steps": list(GRAMMAR_STEPS[grammar]),
        "palette_hint": _palette_hint(style),
        "motion_hint": _motion_hint(style, grammar),
    }


def enumerate_matrix(styles: list[str] | None = None,
                     grammars: list[str] | None = None) -> list[dict]:
    """Enumerate the cross-product (default: full 35 x 9 = 315 cards)."""
    styles = styles if styles is not None else STYLES
    grammars = grammars if grammars is not None else GRAMMARS
    unknown = [s for s in styles if s not in STYLES] + [g for g in grammars if g not in GRAMMARS]
    if unknown:
        raise KeyError(f"unknown entries: {unknown}")
    return [compose(s, g) for s, g in itertools.product(styles, grammars)]


def _palette_hint(style: str) -> str:
    if style in ("watercolor", "gouache-flat", "storybook-crayon", "fairy-tale-golden-age",
                 "botanical-plate", "chalk-pastel"):
        return "soft-muted, paper-warm base"
    if style in ("neon-noir", "vaporwave-grid", "x-ray-schematic", "thermal-map"):
        return "dark base, 2 accent hues max"
    return "limited 3-color print palette"


def _motion_hint(style: str, grammar: str) -> str:
    base = {
        "stop-motion-clay": "12fps stepped poses",
        "paper-cutout": "layer slides, no rotation",
        "silhouette-theater": "rear-light intensity shift",
        "pixel-art": "8px grid snaps",
    }.get(style, "eased 0.3s transforms")
    if grammar == "loop-emphasis":
        return base + "; loop cycle <=1.2s"
    if grammar == "zoom-drill":
        return base + "; zoom capped at 3x to avoid blur"
    return base


def qa_check(card: dict) -> list[str]:
    """Delivery gate. Returns list of problems (empty == PASS)."""
    problems: list[str] = []
    if not isinstance(card, dict):
        return ["card is not a JSON object"]
    for field in QA_REQUIRED_FIELDS:
        if field not in card or card[field] in (None, "", [], {}):
            problems.append(f"missing/empty required field: {field}")
    if "style" in card and card["style"] not in STYLES:
        problems.append(f"style not in dictionary: {card.get('style')!r}")
    if "grammar" in card and card["grammar"] not in GRAMMARS:
        problems.append(f"grammar not in dictionary: {card.get('grammar')!r}")
    steps = card.get("steps")
    if isinstance(steps, list):
        if not steps:
            problems.append("steps is empty")
        expected = GRAMMARS.index(card["grammar"]) >= 0 and GRAMMAR_STEPS.get(card.get("grammar"))
        if expected is not None and len(steps) != len(expected):
            problems.append(
                f"step count {len(steps)} != grammar template {len(expected)}")
    if isinstance(card, dict) and card.get("schema") != CARD_SCHEMA_VERSION:
        problems.append(f"schema mismatch (want {CARD_SCHEMA_VERSION})")
    return problems


# ---------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="art-style-grammar-matrix",
                                description="style x grammar card matrix with a QA delivery gate")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("styles", help="list the 35 styles")
    sub.add_parser("grammars", help="list the 9 grammars with step templates")
    c = sub.add_parser("compose", help="compose one card")
    c.add_argument("--style", required=True)
    c.add_argument("--grammar", required=True)
    e = sub.add_parser("enumerate", help="enumerate the matrix to JSON")
    e.add_argument("--styles", nargs="*", default=None)
    e.add_argument("--grammars", nargs="*", default=None)
    e.add_argument("--out", default="-")
    q = sub.add_parser("qa", help="run the delivery gate on a card JSON file")
    q.add_argument("--file", required=True)

    a = p.parse_args(argv)
    try:
        if a.cmd == "styles":
            for s in STYLES:
                print(s)
        elif a.cmd == "grammars":
            for g in GRAMMARS:
                print(f"{g}: {' -> '.join(GRAMMAR_STEPS[g])}")
        elif a.cmd == "compose":
            print(json.dumps(compose(a.style, a.grammar), indent=2))
        elif a.cmd == "enumerate":
            cards = enumerate_matrix(a.styles, a.grammars)
            payload = {"schema": CARD_SCHEMA_VERSION, "count": len(cards), "cards": cards}
            if a.out == "-":
                print(json.dumps(payload, indent=2))
            else:
                with open(a.out, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
                print(f"wrote {len(cards)} cards -> {a.out}")
        elif a.cmd == "qa":
            with open(a.file, encoding="utf-8") as f:
                card = json.load(f)
            problems = qa_check(card)
            if problems:
                print("FAIL:")
                for pr in problems:
                    print(f"  - {pr}")
                return 1
            print("PASS")
        return 0
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
