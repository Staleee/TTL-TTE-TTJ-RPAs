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
from pathlib import Path
from typing import Tuple

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
    ARABIC_ACCOMPANIED_BY_PREFIX,
    VISA_TYPE_LABELS,
    BOTTOM_LABEL_FONT_SIZE,
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
    """Fill all checkbox fields based on data values."""
    
    # NOTE: Fields 12 (Sex), 17 (Marital Status), and 21 (Purpose of Trip)
    # are intentionally left empty per form requirements
    
    # Visa Info
    visa = data.get("visa_info", {})
    
    # Visa Type
    visa_type = visa.get("type", "").lower()
    if visa_type in CHECKBOX_MAPPINGS["visa_type"]:
        checkbox_key = CHECKBOX_MAPPINGS["visa_type"][visa_type]
        if checkbox_key in FIELD_COORDINATES:
            x, y = FIELD_COORDINATES[checkbox_key]
            insert_checkbox(page, x, y)
    
    # Visa Duration - automatically determined by visa type
    # Single/Two Entry = 3 months, Multiple Entry = 6 months
    if visa_type in ("multiple_entry", "multiple"):
        visa_duration = "six_months"
    else:
        visa_duration = "three_months"
    
    if visa_duration in CHECKBOX_MAPPINGS["visa_duration"]:
        checkbox_key = CHECKBOX_MAPPINGS["visa_duration"][visa_duration]
        if checkbox_key in FIELD_COORDINATES:
            x, y = FIELD_COORDINATES[checkbox_key]
            insert_checkbox(page, x, y)


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
        # Reshape the Arabic text for proper rendering
        display_text = reshape_arabic_text(text)
        point = fitz.Point(x, y)
        
        # Try different Arabic font approaches in order of preference
        font_attempts = [
            # 1. Try macOS fonts (for local development)
            {"fontfile": "/System/Library/Fonts/GeezaPro.ttc", "fontname": "GeezaPro"},
            {"fontfile": "/System/Library/Fonts/SFArabic.ttf", "fontname": "SFArabic"},
            # 2. Try common Linux fonts (for Railway/production)
            {"fontfile": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "fontname": "DejaVuSans"},
            {"fontfile": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "fontname": "LiberationSans"},
            {"fontfile": "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf", "fontname": "NotoSansArabic"},
            {"fontfile": "/usr/share/fonts/truetype/freefont/FreeSans.ttf", "fontname": "FreeSans"},
            # 3. Try PyMuPDF built-in fonts
            {"fontname": "figo"},  # Built-in font with good Unicode support
        ]
        
        text_inserted = False
        last_error = None
        
        for font_config in font_attempts:
            try:
                page.insert_text(
                    point,
                    display_text,
                    fontsize=fontsize,
                    color=(0, 0, 0),
                    **font_config
                )
                text_inserted = True
                print(f"✓ Arabic text inserted using: {font_config}")
                break
            except Exception as e:
                last_error = e
                continue
        
        # If all attempts failed, try with base Helvetica (won't render Arabic properly but better than nothing)
        if not text_inserted:
            try:
                print(f"Warning: All preferred fonts failed, using fallback. Last error: {last_error}")
                page.insert_text(
                    point,
                    display_text,
                    fontname="helv",
                    fontsize=fontsize,
                    color=(0, 0, 0),
                )
                print("⚠ Arabic text inserted with Helvetica (may not render correctly)")
            except Exception as e:
                print(f"Error: Failed to insert Arabic text: {e}")


def fill_text_fields(page, data: dict):
    """Fill all text fields based on data values."""
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
    
    # Auto-translate accompany_name to Arabic for the accompanied_by field
    accompany_name = get_nested_value(data, "accompany_name")
    if accompany_name and "accompanied_by_arabic" in FIELD_COORDINATES:
        translated_name = translate_to_arabic(accompany_name)
        arabic_text = ARABIC_ACCOMPANIED_BY_PREFIX + translated_name
        x, y = FIELD_COORDINATES["accompanied_by_arabic"]
        insert_arabic_text(page, x, y, arabic_text, fontsize=BOTTOM_LABEL_FONT_SIZE)
    
    # Add visa type pricing label on the left side
    visa_type = get_nested_value(data, "visa_info.type")
    if visa_type and "visa_type_label" in FIELD_COORDINATES:
        visa_type_lower = visa_type.lower()
        if visa_type_lower in VISA_TYPE_LABELS:
            label_text = VISA_TYPE_LABELS[visa_type_lower]
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

