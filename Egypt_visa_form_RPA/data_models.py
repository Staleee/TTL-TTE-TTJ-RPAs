"""
Data models and validation for Egypt visa application form
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class Relative:
    """Model for relative/friend in Egypt"""
    
    def __init__(self, full_name: str, address: str):
        self.full_name = full_name
        self.address = address
    
    def validate(self) -> bool:
        """Validate relative data"""
        return bool(self.full_name and self.address)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create Relative from dictionary"""
        return cls(
            full_name=data.get('full_name', ''),
            address=data.get('address', '')
        )


class VisaApplication:
    """Model for complete visa application"""
    
    def __init__(self, data: dict):
        self.data = data
        
        # Personal info
        personal = data.get('personal_info', {})
        self.first_name = personal.get('first_name', '')
        self.middle_name = personal.get('middle_name', '')
        self.family_name = personal.get('family_name', '')
        self.date_of_birth = personal.get('date_of_birth', '')
        self.place_of_birth = personal.get('place_of_birth', '')
        self.sex = personal.get('sex', '')
        self.marital_status = personal.get('marital_status', '')
        
        # Nationality
        nationality = data.get('nationality', {})
        self.present_nationality = nationality.get('present_nationality', '')
        self.nationality_of_origin = nationality.get('nationality_of_origin', '')
        
        # Occupation
        occupation = data.get('occupation', {})
        self.occupation_arabic = occupation.get('occupation_arabic', '')
        
        # Passport
        passport = data.get('passport', {})
        self.passport_number = passport.get('passport_number', '')
        self.passport_type = passport.get('passport_type', '')
        self.issued_at = passport.get('issued_at', '')
        self.issued_on = passport.get('issued_on', '')
        self.expires_on = passport.get('expires_on', '')
        
        # Addresses
        addresses = data.get('addresses', {})
        self.permanent_address = addresses.get('permanent_address', '')
        self.present_address = addresses.get('present_address', '')
        
        # Visa details
        visa = data.get('visa_details', {})
        self.visa_type = visa.get('visa_type', '')
        self.duration_of_stay = visa.get('duration_of_stay', '')
        self.date_of_arrival = visa.get('date_of_arrival', '')
        self.purpose_of_visit = visa.get('purpose_of_visit', '')
        self.address_in_egypt = visa.get('address_in_egypt', '')
        self.port_of_entry = visa.get('port_of_entry', '')
        
        # Contact
        contact = data.get('contact', {})
        self.phone_number = contact.get('phone_number', '')
        
        # Relatives in Egypt
        relatives_data = data.get('relatives_in_egypt', [])
        self.relatives = [Relative.from_dict(r) for r in relatives_data]
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the visa application data
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Required personal fields
        if not self.first_name:
            errors.append("First name is required")
        if not self.middle_name:
            errors.append("Middle name is required")
        if not self.family_name:
            errors.append("Family name is required")
        if not self.date_of_birth:
            errors.append("Date of birth is required")
        if not self.place_of_birth:
            errors.append("Place of birth is required")
        if not self.sex:
            errors.append("Sex is required")
        if not self.marital_status:
            errors.append("Marital status is required")
        
        # Validate sex value
        if self.sex and self.sex not in ['Male', 'Female']:
            errors.append(f"Invalid sex value: {self.sex}. Must be 'Male' or 'Female'")
        
        # Validate marital status
        valid_marital = ['Single', 'Married', 'Widow', 'Widower']
        if self.marital_status and self.marital_status not in valid_marital:
            errors.append(f"Invalid marital status: {self.marital_status}")
        
        # Required nationality fields
        if not self.present_nationality:
            errors.append("Present nationality is required")
        if not self.nationality_of_origin:
            errors.append("Nationality of origin is required")
        
        # Required occupation
        if not self.occupation_arabic:
            errors.append("Occupation (in Arabic) is required")
        
        # Required passport fields
        if not self.passport_number:
            errors.append("Passport number is required")
        if not self.passport_type:
            errors.append("Passport type is required")
        if not self.issued_at:
            errors.append("Passport issued at is required")
        if not self.issued_on:
            errors.append("Passport issued on date is required")
        if not self.expires_on:
            errors.append("Passport expires on date is required")
        
        # Validate dates
        if self.date_of_birth:
            if not self._validate_date(self.date_of_birth):
                errors.append(f"Invalid date of birth format: {self.date_of_birth}")
        if self.issued_on:
            if not self._validate_date(self.issued_on):
                errors.append(f"Invalid passport issued date format: {self.issued_on}")
        if self.expires_on:
            if not self._validate_date(self.expires_on):
                errors.append(f"Invalid passport expiry date format: {self.expires_on}")
        if self.date_of_arrival:
            if not self._validate_date(self.date_of_arrival):
                errors.append(f"Invalid arrival date format: {self.date_of_arrival}")
        
        # Required address fields
        if not self.permanent_address:
            errors.append("Permanent address is required")
        if not self.present_address:
            errors.append("Present address is required")
        
        # Required visa fields
        if not self.visa_type:
            errors.append("Visa type is required")
        if self.visa_type and self.visa_type not in ['Single', 'Multiple']:
            errors.append(f"Invalid visa type: {self.visa_type}. Must be 'Single' or 'Multiple'")
        if not self.duration_of_stay:
            errors.append("Duration of stay is required")
        if not self.date_of_arrival:
            errors.append("Date of arrival is required")
        if not self.purpose_of_visit:
            errors.append("Purpose of visit is required")
        if not self.address_in_egypt:
            errors.append("Address in Egypt is required")
        if not self.port_of_entry:
            errors.append("Port of entry is required")
        
        # Required contact
        if not self.phone_number:
            errors.append("Phone number is required")
        
        # Validate relatives
        for idx, relative in enumerate(self.relatives):
            if not relative.validate():
                errors.append(f"Relative {idx + 1} has incomplete information")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def get_output_filename(self) -> str:
        """Generate output filename for the PDF"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{self.first_name}_{self.family_name}_{timestamp}.pdf"
    
    @classmethod
    def from_json_file(cls, filepath: Path):
        """Load visa application from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)


def load_applications_from_directory(directory: Path) -> List[VisaApplication]:
    """
    Load all JSON application files from a directory
    """
    applications = []
    json_files = list(directory.glob('*.json'))
    
    for json_file in json_files:
        try:
            app = VisaApplication.from_json_file(json_file)
            applications.append(app)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    return applications


if __name__ == "__main__":
    # Test with sample data
    sample_file = Path(__file__).parent / "data" / "sample_application.json"
    if sample_file.exists():
        app = VisaApplication.from_json_file(sample_file)
        is_valid, errors = app.validate()
        
        if is_valid:
            print("✓ Sample application is valid")
            print(f"Output filename: {app.get_output_filename()}")
        else:
            print("✗ Validation errors:")
            for error in errors:
                print(f"  - {error}")
    else:
        print(f"Sample file not found: {sample_file}")

