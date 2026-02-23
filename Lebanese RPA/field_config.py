"""
Field configuration for Lebanon Visa Application Form
Contains coordinates (x, y) for each form field based on PDF page dimensions.
PDF Page size: 612 x 792 points (US Letter)

Coordinates extracted from PDF analysis.
"""

# Font settings
FONT_NAME = "helv"  # Helvetica
FONT_SIZE = 9
CHECKBOX_CHAR = "X"
CHECKBOX_FONT_SIZE = 10
BOTTOM_LABEL_FONT_SIZE = 14  # 1.5x larger for visa type label and accompanied by text

# Field coordinates: (x, y) where y is from top of page
# Based on actual PDF text extraction analysis

FIELD_COORDINATES = {
    # ===== SECTION 1: FULL NAME =====
    # 01- Full Name (as Per Passport)
    # First: label at x=67.4, y=135.0 (bottom=143.8)
    "first_name": (67, 154),
    # Middle: label at x=198.1, y=135.9 (bottom=143.6)
    "middle_name": (198, 154),
    # Last: label at x=323.3, y=135.3 (bottom=144.0)
    "last_name": (323, 154),
    
    # ===== SECTION 2-4: BIRTH INFO & CONTACT =====
    # 02- Place of Birth: label at x=72.6, y=158.3 (bottom=167.1)
    "place_of_birth": (72, 178),
    # 03- Date of Birth (Day/Month/Year): label at x=198.3, y=158.3
    "dob": (198, 188),
    # 04- Mobile #: label at x=328.6, y=158.3 (bottom=167.1)
    "mobile": (328, 178),
    
    # ===== SECTION 5-7: NATIONALITY & EMAIL =====
    # 05- Present Nationality: label at x=72.6, y=190.9 (bottom=199.7)
    "present_nationality": (72, 210),
    # 06- Nationality of Origin: label at x=198.3, y=190.9 (bottom=199.7)
    "nationality_of_origin": (198, 210),
    # 07- Email Address: label at x=328.6, y=190.9 (bottom=199.7)
    "email": (328, 210),
    
    # ===== SECTION 8-10: PASSPORT INFO =====
    # 08- Passport Number: label at x=72.6, y=219.3 (bottom=228.0)
    "passport_number": (72, 238),
    # 09- Issuing Country: label at x=198.3, y=219.3 (bottom=228.0)
    "issuing_country": (198, 238),
    # 10- Expiration Date: label at x=328.6, y=219.3 (bottom=228.0)
    "passport_expiry": (328, 248),
    
    # ===== SECTION 11-13: ADDRESS & SEX =====
    # 11. Address in UAE: label at x=72.6, y=250.7 (bottom=259.5)
    "uae_address": (72, 270),
    # 12. Sex checkboxes: "F" at end of "12. Sex:  F" label, "M" at x=403.3
    "checkbox_female": (380, 259),
    "checkbox_male": (415, 259),
    # 13. Home Phone: label at x=459.0, y=250.7 (bottom=259.5)
    "home_phone": (459, 270),
    
    # ===== SECTION 14-15: VISA REFUSAL & TITLE =====
    # 14. Have you ever been refused... ends at y=296.7
    "visa_refusal_details": (72, 307),
    # 15. Title (Job position): label at x=328.6, y=278.8 (bottom=287.6)
    "job_title": (328, 298),
    
    # ===== SECTION 16: UAE RESIDENCY =====
    # 16. Date of expiration of residency in UAE: label at x=328.6, y=304.0 (bottom=312.8)
    "uae_residency_expiry": (328, 323),
    
    # ===== SECTION 17: MARITAL STATUS CHECKBOXES =====
    # Single: text at x=377.4, y=339.3 (bottom=348.0) - checkbox before text
    "checkbox_single": (364, 347),
    # Married: text at x=370.7, y=358.0 (bottom=366.8)
    "checkbox_married": (357, 366),
    # Divorced: text at x=448.0, y=340.0 (bottom=348.8)
    "checkbox_divorced": (435, 348),
    # Widowed: text at x=446.0, y=358.0 (bottom=366.8)
    "checkbox_widowed": (433, 366),
    
    # ===== SECTION 18-19: PREVIOUS VISITS & TRIP DURATION =====
    # 18. Have you ever been in Lebanon before: ends at y=392.0
    "lebanon_previous_visits": (72, 402),
    # 19. Duration of Immediate Trip: dates shown at y=383.1 (bottom=393.2)
    "trip_start_date": (328, 393),
    "trip_end_date": (420, 393),
    
    # ===== SECTION 20: CRIMINAL RECORD =====
    # 20. Criminal offence question: ends around y=449.6
    "criminal_record_details": (72, 460),
    
    # ===== SECTION 21: PURPOSE OF TRIP CHECKBOXES =====
    # Business: text at x=352.7, y=407.2 (bottom=416.0)
    "checkbox_business": (339, 415),
    # Education: text at x=352.7, y=416.3 (bottom=425.1)
    "checkbox_education": (339, 424),
    # Tourism: text at x=350.7, y=425.4 (bottom=434.2)
    "checkbox_tourism": (337, 433),
    # Family Visit: text at x=350.7, y=434.8 (bottom=443.6)
    "checkbox_family_visit": (337, 443),
    # Official: text at x=350.7, y=443.9 (bottom=452.7)
    "checkbox_official": (337, 452),
    # Other (specify): text at x=350.7, y=452.1 (bottom=460.8)
    "checkbox_other_purpose": (337, 460),
    "other_purpose_text": (430, 460),
    
    # ===== SECTION 22-23: CONTACT & ACCOMMODATION =====
    # 22. Contact Person info: label at x=72.6, y=462.9 (bottom=471.6)
    "contact_person": (72, 482),
    # 23. Address of stay in Lebanon: label at x=72.6, y=488.1 (bottom=496.8)
    "lebanon_address": (72, 507),
    
    # ===== SECTION 24-25: TRAVEL DATES =====
    # 24. Expected Date of Arrival: label at x=72.6, y=514.9 (bottom=523.7)
    "arrival_date": (72, 544),
    # 25. Expected Date of Departure: label at x=328.6, y=514.9 (bottom=523.7)
    "departure_date": (328, 544),
    
    # ===== SECTION 26: VISA TYPE CHECKBOXES =====
    # Single Entry: text at x=80.7, y=566.8 (bottom=577.9) - checkbox before text
    "checkbox_single_entry": (68, 577),
    # Two Entry: text at x=80.7, y=588.6 (bottom=599.8)
    "checkbox_two_entry": (68, 599),
    # Multiple Entry: text at x=80.7, y=609.5 (bottom=620.7)
    "checkbox_multiple_entry": (68, 620),
    
    # Duration checkboxes - placed at CENTER of actual checkbox boxes
    # Row 1: 15 days box center=(274.2, 571.5), One Month box center=(356.3, 571.0)
    "checkbox_15_days": (272, 575),
    "checkbox_one_month": (354, 575),
    # Row 2: Three Months box center=(274.5, 580.7), Six Months box center=(356.3, 580.1)
    "checkbox_three_months": (271, 584),
    "checkbox_six_months": (353, 583),
    
    # ===== SIGNATURE SECTION =====
    # Date: label at x=275.3, y=635.7 (bottom=644.4)
    "signature_date": (295, 644),
    
    # ===== ARABIC ACCOMPANIMENT TEXT =====
    # Bottom right of page - "ﺑﻤﺮاﻓﻘﺔ" + Arabic name
    "accompanied_by_arabic": (450, 750),
    
    # ===== VISA TYPE PRICING LABEL =====
    # Bottom left of page - same y-level as accompanied_by_arabic
    "visa_type_label": (72, 750),
}

# Mapping of data values to checkbox fields
CHECKBOX_MAPPINGS = {
    "sex": {
        "female": "checkbox_female",
        "male": "checkbox_male",
        "f": "checkbox_female",
        "m": "checkbox_male"
    },
    "marital_status": {
        "single": "checkbox_single",
        "married": "checkbox_married",
        "divorced": "checkbox_divorced",
        "widowed": "checkbox_widowed"
    },
    "purpose_of_trip": {
        "business": "checkbox_business",
        "education": "checkbox_education",
        "tourism": "checkbox_tourism",
        "family_visit": "checkbox_family_visit",
        "family visit": "checkbox_family_visit",
        "official": "checkbox_official",
        "other": "checkbox_other_purpose"
    },
    "visa_type": {
        "single_entry": "checkbox_single_entry",
        "single": "checkbox_single_entry",
        "two_entry": "checkbox_two_entry",
        "double": "checkbox_two_entry",
        "multiple_entry": "checkbox_multiple_entry",
        "multiple": "checkbox_multiple_entry"
    },
    "visa_duration": {
        "15_days": "checkbox_15_days",
        "15 days": "checkbox_15_days",
        "one_month": "checkbox_one_month",
        "1_month": "checkbox_one_month",
        "1 month": "checkbox_one_month",
        "three_months": "checkbox_three_months",
        "3_months": "checkbox_three_months",
        "3 months": "checkbox_three_months",
        "six_months": "checkbox_six_months",
        "6_months": "checkbox_six_months",
        "6 months": "checkbox_six_months"
    }
}

# Text field mappings from JSON path to coordinate key
TEXT_FIELD_MAPPINGS = {
    "personal_info.first_name": "first_name",
    "personal_info.middle_name": "middle_name",
    "personal_info.last_name": "last_name",
    "personal_info.place_of_birth": "place_of_birth",
    "personal_info.date_of_birth": "dob",
    "personal_info.mobile": "mobile",
    "personal_info.present_nationality": "present_nationality",
    "personal_info.nationality_of_origin": "nationality_of_origin",
    # "personal_info.email": "email",  # Left empty per form requirements
    # "personal_info.home_phone": "home_phone",  # Left empty per form requirements
    "passport_info.passport_number": "passport_number",
    "passport_info.issuing_country": "issuing_country",
    "passport_info.expiry_date": "passport_expiry",
    "residence_info.uae_address": "uae_address",
    "residence_info.uae_residency_expiry": "uae_residency_expiry",
    # "employment_info.job_title": "job_title",  # Left empty per form requirements
    "travel_history.visa_refusal_details": "visa_refusal_details",
    "travel_history.lebanon_previous_visits": "lebanon_previous_visits",
    "travel_history.criminal_record_details": "criminal_record_details",
    "trip_info.other_purpose": "other_purpose_text",
    "accommodation_info.contact_person": "contact_person",
    "accommodation_info.lebanon_address": "lebanon_address",
}

# Arabic text prefix for accompaniment
ARABIC_ACCOMPANIED_BY_PREFIX = "ﺑﻤﺮاﻓﻘﺔ  "

# Visa type pricing labels
VISA_TYPE_LABELS = {
    "single_entry": "Single Entry 3M AED 325 ",
    "single": "Single Entry 3M AED 325 ",
    "two_entry": "Two Entry 3M AED 465 ",
    "double": "Two Entry 3M AED 465 ",
    "multiple_entry": "Multiple Entry 6M AED 645 ",
    "multiple": "Multiple Entry 6M AED   645 ",
}

