from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader

DUDE_NAMES = frozenset({"DUDE", "THE DUDE"})

SCENE_HEADING_RE = r"^(?:INT|EXT|I/E|INT\./EXT\.|INT\.\s*/\s*EXT\.)[.!]?\s+"

CUE_RE = r"^[A-Z][A-Z .'’\-]*\s*(?:\([A-Z’.,\s\-]+\))?$"

MIN_CUE_INDENT = 20
DIALOGUE_INDENT_LO = 8
DIALOGUE_INDENT_HI = 16
PAREN_INDENT_LO = 16
PAREN_INDENT_HI = 20

SKIP_PREFIXES = (
    "(CONTINUED",
    "CONTINUED:",
    "CONTINUED (",
    "FADE OUT:",
    "FADE IN:",
    "FAST FADE OUT:",
    "CUT TO:",
    "DISSOLVE TO:",
    "SMASH CUT TO:",
    "WIDE ON",
    "CLOSE ON",
    "BACK TO",
    "MATCH CUT TO:",
)


@dataclass
class DialogueTurn:
    scene: int
    heading: str
    character: str
    text: str
    speaker_is_dude: bool


def _clean_text(lines: list[str]) -> str:
    return " ".join(line.strip() for line in lines if line.strip()).strip()


def _page_number(line: str) -> bool:
    return line.strip().rstrip(".").isdigit()


def _is_skip(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if _page_number(line):
        return True
    return stripped.startswith(SKIP_PREFIXES)


def _is_scene_heading(line: str) -> bool:
    import re

    return bool(re.match(SCENE_HEADING_RE, line.strip(), re.IGNORECASE))


def _is_cue_lines(line: str) -> bool:
    import re

    return bool(re.match(CUE_RE, line.strip()))


def _character_name(cue: str) -> str:
    name = cue.strip()
    if "(" in name:
        name = name.split("(", 1)[0]
    return name.strip()


def _extract_pages(path: Path) -> list[str]:
    reader = PdfReader(str(path))
    return [page.extract_text(extraction_mode="layout") or "" for page in reader.pages]


def parse_layout(pages: list[str]) -> list[DialogueTurn]:
    turns: list[DialogueTurn] = []
    scene = 0
    heading = ""
    turn_text: list[str] = []
    turn_char = ""

    def flush_turn(next_cue: str | None = None) -> None:
        nonlocal turn_text, turn_char
        text = _clean_text(turn_text)
        if turn_char and text:
            turns.append(
                DialogueTurn(
                    scene=scene,
                    heading=heading,
                    character=turn_char,
                    text=text,
                    speaker_is_dude=turn_char.upper() in DUDE_NAMES,
                )
            )
        turn_text = []
        turn_char = ""
        if next_cue:
            turn_char = _character_name(next_cue)

    for page in pages:
        for line in page.splitlines():
            stripped = line.strip()
            indent = len(line) - len(line.lstrip())

            if _is_skip(line):
                continue

            if _is_scene_heading(line):
                flush_turn()
                scene += 1
                heading = " ".join(stripped.split())
                continue

            if indent == 0:
                flush_turn()
                continue

            if indent >= MIN_CUE_INDENT and _is_cue_lines(line):
                flush_turn(next_cue=stripped)
                continue

            if DIALOGUE_INDENT_LO <= indent < DIALOGUE_INDENT_HI:
                turn_text.append(stripped)
                continue

            if PAREN_INDENT_LO <= indent < PAREN_INDENT_HI:
                turn_text.append(stripped)
                continue

    flush_turn()
    return turns


def parse_script(path: str | Path) -> list[DialogueTurn]:
    return parse_layout(_extract_pages(Path(path)))


if __name__ == "__main__":
    import sys

    for turn in parse_script(sys.argv[1] if len(sys.argv) > 1 else "data/thebiglebowski.pdf"):
        print(f"[{turn.scene}] {turn.character}" + (" (DUDE)" if turn.speaker_is_dude else ""))
        print(f"    {turn.text}")