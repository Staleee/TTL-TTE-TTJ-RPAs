"""
Generate verification examples for the Lebanon visa form.

Produces a set of filled PDFs (and PNG renderings cropped to the visa-type /
duration / bottom-row area) so the highlighter color and bottom labels can be
visually inspected without spinning up the API server.

Run from the ``Lebanese RPA`` folder:

    python verify_examples.py

Outputs are written to ``verify_output/``.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import fitz  # PyMuPDF

from fill_visa_form import generate_filled_pdf_bytes


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR / "Visa_Application_Form.pdf"
DATA_PATH = SCRIPT_DIR / "visa_applicant_data.json"
OUTPUT_DIR = SCRIPT_DIR / "verify_output"

# Region of interest: Section 25 (visa type/duration) down to the bottom row
# (Arabic accompaniment + AED label). Coordinates in PDF points (612x792 page).
CROP_RECT = fitz.Rect(40, 540, 612, 770)
RENDER_DPI = 220


def _load_base_data() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _with_visa_type(base: dict, visa_type: str) -> dict:
    data = copy.deepcopy(base)
    data.setdefault("visa_info", {})["type"] = visa_type
    return data


def _render_crop_png(pdf_bytes: bytes, png_path: Path) -> None:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    zoom = RENDER_DPI / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, clip=CROP_RECT, alpha=False)
    pix.save(png_path)
    doc.close()


def _safe_write(path: Path, writer) -> bool:
    try:
        writer(path)
        return True
    except PermissionError:
        print(f"  ! {path.name} is locked (open in another app); skipped")
        return False


def _write_example(name: str, data: dict) -> None:
    pdf_bytes, _ = generate_filled_pdf_bytes(data, str(TEMPLATE_PATH))
    pdf_path = OUTPUT_DIR / f"{name}.pdf"
    png_path = OUTPUT_DIR / f"{name}.png"
    wrote_pdf = _safe_write(pdf_path, lambda p: p.write_bytes(pdf_bytes))
    wrote_png = _safe_write(png_path, lambda p: _render_crop_png(pdf_bytes, p))
    parts = []
    if wrote_pdf:
        parts.append(pdf_path.name)
    if wrote_png:
        parts.append(png_path.name)
    if parts:
        print(f"  - {' + '.join(parts)}")


def main() -> None:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Template not found: {TEMPLATE_PATH}")
    if not DATA_PATH.exists():
        raise SystemExit(f"Sample data not found: {DATA_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    base = _load_base_data()
    base_no_companion = copy.deepcopy(base)
    base_no_companion.pop("accompany_name", None)
    base_no_companion.pop("companion_name", None)
    base_no_companion.pop("client_name", None)

    print("Generating verification examples in:", OUTPUT_DIR)

    _write_example("single_entry", _with_visa_type(base_no_companion, "single_entry"))
    _write_example("double_entry", _with_visa_type(base_no_companion, "double_entry"))
    _write_example("multiple_entry", _with_visa_type(base_no_companion, "multiple_entry"))

    full_payload = _with_visa_type(base, "two_entry")
    _write_example("full_payload", full_payload)

    with_client_name = copy.deepcopy(full_payload)
    with_client_name["client_name"] = "Maria Rodriguez"
    with_client_name.pop("accompany_name", None)
    with_client_name.pop("companion_name", None)
    _write_example("with_client_name", with_client_name)

    arabic_companion = _with_visa_type(base_no_companion, "two_entry")
    arabic_companion["companion_name"] = "\u0623\u062d\u0645\u062f \u0639\u0644\u064a"  # أحمد علي
    _write_example("arabic_companion", arabic_companion)

    # ── ZERP-120 verification scenarios ───────────────────────────────────
    # #4 - companion name must render to the LEFT of "بمرافقة العائلة".
    # Long Arabic name to make the layout obvious.
    zerp120_arabic_long = _with_visa_type(base_no_companion, "two_entry")
    zerp120_arabic_long["companion_name"] = (
        "\u064a\u0627\u0633\u0645\u064a\u0646\u0627 "
        "\u0627\u0646\u0637\u0648\u0627\u0646 \u0632\u064a\u0627\u062f "
        "\u0645\u0641\u0631\u062c"
    )  # ياسمينا انطوان زياد مفرج (matches the customer screenshot)
    _write_example("zerp120_companion_arabic_long", zerp120_arabic_long)

    # #2 - Double / Multiple entry: the `pro` payload sends an empty
    # `arrival_date_to_dubai` so the form leaves field 19's end date and
    # field 25 (Expected Departure) blank. Simulate that here by clearing
    # the value in `trip_info`.
    double_empty_dep = _with_visa_type(base, "double_entry")
    double_empty_dep["trip_info"] = {
        **double_empty_dep.get("trip_info", {}),
        "arrival_date_to_dubai": "",
    }
    _write_example("zerp120_double_entry_empty_departure", double_empty_dep)

    multiple_empty_dep = _with_visa_type(base, "multiple_entry")
    multiple_empty_dep["trip_info"] = {
        **multiple_empty_dep.get("trip_info", {}),
        "arrival_date_to_dubai": "",
    }
    _write_example("zerp120_multiple_entry_empty_departure", multiple_empty_dep)

    print("Done.")


if __name__ == "__main__":
    main()
