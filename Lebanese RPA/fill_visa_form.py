#!/usr/bin/env python3
"""
Lebanon Visa Application Form Filler

Automatically fills the Lebanon Visa Application Form
by overlaying text onto the PDF based on data from a JSON file or dict.

Usage (CLI):
    python fill_visa_form.py --data visa_applicant_data.json --output output/filled_form.pdf

Usage (API):
    from fill_visa_form import generate_filled_pdf_bytes
    pdf_bytes, full_name = generate_filled_pdf_bytes(applicant_data_dict, template_path)
"""

import argparse
import json
import os
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

# Path to our bundled Arabic font (in the repo) – no system install needed
_SCRIPT_DIR = Path(__file__).resolve().parent
BUNDLED_ARABIC_FONT = _SCRIPT_DIR / "fonts" / "NotoSansArabic-Regular.ttf"
NOTO_ARABIC_URL = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf"


def _ensure_arabic_font() -> Optional[Path]:
    """Use bundled font if present; else try to download it once. Returns path if we have a usable font file."""
    if BUNDLED_ARABIC_FONT.exists():
        return BUNDLED_ARABIC_FONT
    try:
        BUNDLED_ARABIC_FONT.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(NOTO_ARABIC_URL, BUNDLED_ARABIC_FONT)
        if BUNDLED_ARABIC_FONT.exists():
            return BUNDLED_ARABIC_FONT
    except Exception:
        pass
    return None

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is not installed. Run: pip install pymupdf")
    exit(1)

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    print("Warning: arabic-reshaper or python-bidi not installed. Arabic text may not display correctly.")

try:
    from deep_translator import GoogleTranslator
    TRANSLATION_SUPPORT = True
except ImportError:
    TRANSLATION_SUPPORT = False
    print("Warning: deep-translator not installed. Arabic translation will not work.")

from field_config import (
    FIELD_COORDINATES,
    CHECKBOX_MAPPINGS,
    TEXT_FIELD_MAPPINGS,
    FONT_NAME,
    FONT_SIZE,
    CHECKBOX_CHAR,
    CHECKBOX_FONT_SIZE,
    ARABIC_ACCOMPANIMENT_OF_FAMILY,
    BOTTOM_LABEL_FONT_SIZE,
    VISA_TYPE_TEXT_RECTS,
    VISA_DURATION_TEXT_RECTS,
    get_bottom_left_label,
)


def get_nested_value(data: dict, path: str):
    """
    Get a value from nested dictionary using dot notation.
    Example: get_nested_value(data, "personal_info.last_name")
    """
    keys = path.split(".")
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value


def load_applicant_data(json_path: str) -> dict:
    """Load applicant data from JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_full_name(data: dict) -> str:
    """Extract full name from applicant data."""
    personal = data.get("personal_info", {})
    first_name = personal.get("first_name", "")
    middle_name = personal.get("middle_name", "")
    last_name = personal.get("last_name", "")
    
    # Build full name, excluding N/A values
    name_parts = []
    for part in [first_name, middle_name, last_name]:
        if part and part.upper() != "N/A":
            name_parts.append(part)
    
    return " ".join(name_parts)


def insert_text(page, x: float, y: float, text: str, fontsize: int = FONT_SIZE):
    """Insert text at specified coordinates on the PDF page.
    N/A values are included as per form instructions.
    """
    if text and text.strip():
        # Create text insertion point
        point = fitz.Point(x, y)
        page.insert_text(
            point,
            text,
            fontname=FONT_NAME,
            fontsize=fontsize,
            color=(0, 0, 0),  # Black text
        )


def draw_yellow_text_highlight(page, x: float, y: float, width: float, height: float):
    """Draw semi-transparent yellow highlight so the text underneath still shows (highlighter effect)."""
    rect = fitz.Rect(x, y, x + width, y + height)
    try:
        page.draw_rect(rect, fill=(1, 1, 0), color=(1, 1, 0), fill_opacity=0.4)
    except TypeError:
        page.draw_rect(rect, fill=(1, 1, 0), color=(1, 1, 0))


def insert_checkbox(page, x: float, y: float):
    """Insert a checkbox mark (X) at specified coordinates."""
    point = fitz.Point(x, y)
    page.insert_text(
        point,
        CHECKBOX_CHAR,
        fontname=FONT_NAME,
        fontsize=CHECKBOX_FONT_SIZE,
        color=(0, 0, 0),
    )


def redact_area(page, x: float, y: float, width: float, height: float):
    """Redact (white out) an area on the PDF page."""
    rect = fitz.Rect(x, y, x + width, y + height)
    # Add a white rectangle to cover the existing content
    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))


def redact_existing_dates(page):
    """Redact pre-filled dates at point 19 (Duration of Immediate Trip)."""
    # The existing dates "12/12/ 2025" and "30/01/2026" are at y=383.1 (bottom=393.2)
    # Only redact the date line, not the question label above it
    # Date line starts at y=383, redact from y=382 to y=394 (height=12)
    redact_area(page, 328, 382, 215, 12)


def fill_checkboxes(page, data: dict):
    """Draw yellow highlight on visa type and duration (no cross)."""
    try:
        page.wrap_contents()
    except Exception:
        pass
    # NOTE: Purpose of Trip is already in the PDF template (we don’t fill it)
    
    # Visa Info – visa type and duration highlighted in yellow (no cross)
    visa = data.get("visa_info", {})
    
    # Visa Type: yellow highlight on the actual text (Single Entry / Two Entry / Multiple Entry)
    visa_type_raw = (visa.get("type") or "").strip()
    visa_type = visa_type_raw.lower().replace(" ", "_")
    if not visa_type and " " in visa_type_raw:
        visa_type = visa_type_raw.lower()
    if visa_type in CHECKBOX_MAPPINGS["visa_type"]:
        checkbox_key = CHECKBOX_MAPPINGS["visa_type"][visa_type]
        if checkbox_key in VISA_TYPE_TEXT_RECTS:
            x, y, w, h = VISA_TYPE_TEXT_RECTS[checkbox_key]
            draw_yellow_text_highlight(page, x, y, w, h)
    
    # Visa Duration: yellow highlight on the actual text (15 days / 1 month / 3 months / 6 months)
    duration_raw = (visa.get("duration_of_visit") or visa.get("duration") or "").strip()
    duration_key = duration_raw.lower().replace(" ", "_") if duration_raw else ""
    if not duration_key and duration_raw:
        duration_key = duration_raw.lower()
    if duration_key and duration_key in CHECKBOX_MAPPINGS["visa_duration"]:
        checkbox_key = CHECKBOX_MAPPINGS["visa_duration"][duration_key]
        if checkbox_key in VISA_DURATION_TEXT_RECTS:
            x, y, w, h = VISA_DURATION_TEXT_RECTS[checkbox_key]
            draw_yellow_text_highlight(page, x, y, w, h)

    # Purpose of Trip: not filled here – PDF template already has it


def translate_to_arabic(text: str) -> str:
    """Translate text to Arabic using Google Translate."""
    if not TRANSLATION_SUPPORT:
        print("Warning: Translation not available, returning original text")
        return text
    
    if not text or not text.strip():
        return text
    
    try:
        translator = GoogleTranslator(source='auto', target='ar')
        translated = translator.translate(text)
        print(f"✓ Translated '{text}' to Arabic: '{translated}'")
        return translated
    except Exception as e:
        print(f"Warning: Translation failed for '{text}': {e}")
        return text


def reshape_arabic_text(text: str) -> str:
    """Reshape Arabic text for proper display (connected letters, RTL)."""
    if ARABIC_SUPPORT:
        # Reshape Arabic characters to connect properly
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply bidirectional algorithm for RTL display
        bidi_text = get_display(reshaped_text)
        return bidi_text
    return text


def insert_arabic_text(page, x: float, y: float, text: str, fontsize: int = FONT_SIZE):
    """Insert Arabic text at specified coordinates using an Arabic-supporting font."""
    if text and text.strip():
        point = fitz.Point(x, y)
        # Try reshaped first, then raw – some fonts need one or the other
        for display_text in [reshape_arabic_text(text), text]:
            font_attempts = [
                {"fontfile": "C:/Windows/Fonts/arial.ttf", "fontname": "Arial"},
                {"fontfile": "C:/Windows/Fonts/tahoma.ttf", "fontname": "Tahoma"},
                {"fontfile": "C:/Windows/Fonts/times.ttf", "fontname": "Times"},
                {"fontfile": "/System/Library/Fonts/GeezaPro.ttc", "fontname": "GeezaPro"},
                {"fontfile": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "fontname": "DejaVuSans"},
                {"fontfile": "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf", "fontname": "NotoSansArabic"},
                {"fontname": "figo"},
            ]
            for font_config in font_attempts:
                try:
                    page.insert_text(point, display_text, fontsize=fontsize, color=(0, 0, 0), **font_config)
                    return
                except Exception:
                    continue
        try:
            page.insert_text(point, text, fontname="helv", fontsize=fontsize, color=(0, 0, 0))
        except Exception:
            pass


# English fallback when no Arabic font – bottom right is NEVER left empty
BOTTOM_RIGHT_FALLBACK_ENGLISH = "Accompanied by family"
_ARABIC_FONT_NAME = "NotoArabic"


def insert_bottom_right_full_line(
    page, x: float, y: float, companion_name: str, fontsize: int = BOTTOM_LABEL_FONT_SIZE
):
    """
    Insert the whole bottom-right line in ONE go with ONE font so it actually shows (no tofu, companion included).
    Uses the bundled Noto Arabic font; if missing, uses English 'Accompanied by family' + companion.
    """
    phrase_ar = ARABIC_ACCOMPANIMENT_OF_FAMILY
    if companion_name:
        line_ar = phrase_ar + " / " + companion_name
        line_en = BOTTOM_RIGHT_FALLBACK_ENGLISH + " / " + companion_name
    else:
        line_ar = phrase_ar
        line_en = BOTTOM_RIGHT_FALLBACK_ENGLISH
    point = fitz.Point(x, y)
    font_path = _ensure_arabic_font()
    if font_path is not None and font_path.exists():
        try:
            page.insert_font(fontname=_ARABIC_FONT_NAME, fontfile=str(font_path))
            # Reshape ONLY the phrase so it connects; leave companion name raw so it doesn't turn into squares
            phrase_display = reshape_arabic_text(phrase_ar)
            text = phrase_display + (" / " + companion_name if companion_name else "")
            page.insert_text(point, text, fontname=_ARABIC_FONT_NAME, fontsize=fontsize, color=(0, 0, 0))
            return
        except Exception:
            try:
                page.insert_font(fontname=_ARABIC_FONT_NAME, fontfile=str(font_path))
                text_raw = phrase_ar + (" / " + companion_name if companion_name else "")
                page.insert_text(point, text_raw, fontname=_ARABIC_FONT_NAME, fontsize=fontsize, color=(0, 0, 0))
                return
            except Exception:
                pass
    try:
        page.insert_text(point, line_en, fontname="helv", fontsize=fontsize, color=(0, 0, 0))
    except Exception:
        pass


def fill_text_fields(page, data: dict):
    """Fill all text fields based on data values."""
    # Job title (Title/Position): not filled here – PDF template already has it

    for json_path, coord_key in TEXT_FIELD_MAPPINGS.items():
        value = get_nested_value(data, json_path)
        if value and coord_key in FIELD_COORDINATES:
            x, y = FIELD_COORDINATES[coord_key]
            insert_text(page, x, y, str(value))
    
    # Fill departure_date_from_dubai to both trip_start_date and arrival_date fields
    departure_from_dubai = get_nested_value(data, "trip_info.departure_date_from_dubai")
    if departure_from_dubai:
        if "trip_start_date" in FIELD_COORDINATES:
            x, y = FIELD_COORDINATES["trip_start_date"]
            insert_text(page, x, y, str(departure_from_dubai))
        if "arrival_date" in FIELD_COORDINATES:
            x, y = FIELD_COORDINATES["arrival_date"]
            insert_text(page, x, y, str(departure_from_dubai))
    
    # Fill arrival_date_to_dubai to both trip_end_date and departure_date fields
    arrival_to_dubai = get_nested_value(data, "trip_info.arrival_date_to_dubai")
    if arrival_to_dubai:
        if "trip_end_date" in FIELD_COORDINATES:
            x, y = FIELD_COORDINATES["trip_end_date"]
            insert_text(page, x, y, str(arrival_to_dubai))
        if "departure_date" in FIELD_COORDINATES:
            x, y = FIELD_COORDINATES["departure_date"]
            insert_text(page, x, y, str(arrival_to_dubai))
    
    # Bottom right: one line, one font – Arabic phrase + companion so nothing is tofu and companion always shows
    if "accompanied_by_arabic" in FIELD_COORDINATES:
        x, y = FIELD_COORDINATES["accompanied_by_arabic"]
        companion_name = (get_nested_value(data, "companion_name") or get_nested_value(data, "accompany_name") or "").strip()
        insert_bottom_right_full_line(page, x, y, companion_name, BOTTOM_LABEL_FONT_SIZE)
    
    # Bottom left: dynamic label from visa type + duration (e.g. "Two Entry 6M AED 465")
    visa = data.get("visa_info", {})
    visa_type = visa.get("type") or ""
    duration = visa.get("duration_of_visit") or visa.get("duration") or ""
    label_text = get_bottom_left_label(visa_type, duration)
    if label_text and "visa_type_label" in FIELD_COORDINATES:
        x, y = FIELD_COORDINATES["visa_type_label"]
        insert_text(page, x, y, label_text, fontsize=BOTTOM_LABEL_FONT_SIZE)


def generate_filled_pdf_bytes(data: dict, template_path: str) -> Tuple[bytes, str]:
    """
    Generate a filled PDF from applicant data and return as bytes.
    
    Args:
        data: Dictionary containing applicant data
        template_path: Path to the blank PDF form template
    
    Returns:
        Tuple of (pdf_bytes, full_name)
    """
    # Open the PDF template
    doc = fitz.open(template_path)
    
    # Get the first page (the form is typically on page 1)
    page = doc[0]
    
    # Redact pre-existing dates at point 19
    redact_existing_dates(page)
    
    # Fill checkboxes
    fill_checkboxes(page, data)
    
    # Fill text fields
    fill_text_fields(page, data)
    
    # Get PDF as bytes with compression options
    pdf_bytes = doc.tobytes(
        garbage=4,  # Maximum garbage collection (remove unused objects)
        deflate=True,  # Compress streams
        clean=True,  # Clean and sanitize content streams
    )
    
    doc.close()
    
    # Extract full name for the API response
    full_name = extract_full_name(data)
    
    return pdf_bytes, full_name


def fill_visa_form(template_path: str, data_path: str, output_path: str):
    """
    Main function to fill the visa application form and save to file.
    
    Args:
        template_path: Path to the blank PDF form
        data_path: Path to the JSON file with applicant data
        output_path: Path for the filled PDF output
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Load applicant data
    print(f"Loading applicant data from: {data_path}")
    data = load_applicant_data(data_path)
    
    # Open the PDF template
    print(f"Opening PDF template: {template_path}")
    doc = fitz.open(template_path)
    
    # Get the first page (the form is typically on page 1)
    page = doc[0]
    
    # Redact pre-existing dates at point 19
    print("Redacting pre-filled dates...")
    redact_existing_dates(page)
    
    # Fill checkboxes
    print("Filling checkbox fields...")
    fill_checkboxes(page, data)
    
    # Fill text fields
    print("Filling text fields...")
    fill_text_fields(page, data)
    
    # Save the filled form
    print(f"Saving filled form to: {output_path}")
    doc.save(output_path)
    doc.close()
    
    print("✓ Form filled successfully!")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Fill Lebanon Visa Application Form with data from JSON"
    )
    parser.add_argument(
        "--template",
        "-t",
        default="Visa_Application_Form.pdf",
        help="Path to the blank PDF form template (default: Visa_Application_Form.pdf)",
    )
    parser.add_argument(
        "--data",
        "-d",
        default="visa_applicant_data.json",
        help="Path to JSON file with applicant data (default: visa_applicant_data.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output/filled_visa_form.pdf",
        help="Output path for filled PDF (default: output/filled_visa_form.pdf)",
    )
    
    args = parser.parse_args()
    
    # Get the script's directory for relative paths
    script_dir = Path(__file__).parent
    
    # Resolve paths
    template_path = Path(args.template)
    if not template_path.is_absolute():
        template_path = script_dir / template_path
    
    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = script_dir / data_path
    
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = script_dir / output_path
    
    # Validate inputs
    if not template_path.exists():
        print(f"Error: Template PDF not found: {template_path}")
        exit(1)
    
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}")
        exit(1)
    
    # Fill the form
    fill_visa_form(str(template_path), str(data_path), str(output_path))


if __name__ == "__main__":
    main()

