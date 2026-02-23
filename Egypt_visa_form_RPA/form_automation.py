"""
Selenium-based form automation for Egypt visa application
"""

import json
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from data_models import VisaApplication


class EgyptVisaFormAutomation:
    """Automates filling Egypt visa application form"""
    
    def __init__(self, config_path: Path):
        """Initialize automation with config file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for automation"""
        logger = logging.getLogger('EgyptVisaAutomation')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_handler = logging.FileHandler(
            log_dir / f'automation_{timestamp}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        self.logger.info("Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        
        # Headless mode (force headless in production/Railway environment)
        import os
        if self.config['browser']['headless'] or os.environ.get('RAILWAY_ENVIRONMENT'):
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
        
        # Window size
        window_size = self.config['browser']['window_size']
        chrome_options.add_argument(f"--window-size={window_size['width']},{window_size['height']}")
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Set download directory for PDFs
        output_dir = str(Path(self.config['output']['pdf_directory']).absolute())
        prefs = {
            'download.default_directory': output_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'plugins.always_open_pdf_externally': True,
            'printing.print_preview_sticky_settings.appState': json.dumps({
                'recentDestinations': [{
                    'id': 'Save as PDF',
                    'origin': 'local',
                    'account': ''
                }],
                'selectedDestinationId': 'Save as PDF',
                'version': 2,
                'isHeaderFooterEnabled': False,
                'marginsType': 0,  # Default margins
                'scaling': 100,
                'scalingType': 3,
                'scalingTypePdf': 3
            }),
            'savefile.default_directory': output_dir,
            'profile.default_content_settings.popups': 0,
            'profile.default_content_setting_values.automatic_downloads': 1
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Initialize driver - try multiple methods
        # List of paths to try (Windows uses chromedriver.exe)
        project_root = Path(__file__).parent
        chromedriver_name = 'chromedriver.exe' if sys.platform == 'win32' else 'chromedriver'
        common_paths = [
            project_root / 'bin' / chromedriver_name,  # Project bin directory
            project_root / 'bin' / 'chromedriver',     # Linux/Mac in Docker
            Path('/usr/local/bin/chromedriver'),
            Path('/opt/homebrew/bin/chromedriver'),
            Path('/usr/bin/chromedriver'),
        ]
        
        driver_found = False
        
        # Method 1: Try each path
        for path in common_paths:
            if Path(path).exists():
                try:
                    service = Service(executable_path=str(path))
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.logger.info(f"Using ChromeDriver from: {path}")
                    driver_found = True
                    break
                except Exception as e:
                    self.logger.warning(f"Failed to use ChromeDriver at {path}: {e}")
                    continue
        
        # Method 2: Try system PATH (no explicit path)
        if not driver_found:
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.logger.info("Using ChromeDriver from system PATH")
                driver_found = True
            except Exception as e:
                self.logger.warning(f"System ChromeDriver not found: {e}")
        
        if not driver_found:
            raise Exception(
                "\n\nChrome Driver not found!\n\n"
                "To install ChromeDriver:\n"
                "  1. Run: python3 install_chromedriver.py\n"
                "  OR manually:\n"
                "  2. Download from: https://googlechromelabs.github.io/chrome-for-testing/\n"
                "  3. Extract and place in: " + str(project_root / 'bin' / chromedriver_name) + "\n"
                + ("  4. On Linux/Mac: chmod +x " + str(project_root / 'bin' / chromedriver_name) + "\n\n" if chromedriver_name == 'chromedriver' else "\n")
                + "See SETUP_INSTRUCTIONS.md for more details."
            )
        
        # Set timeouts
        self.driver.implicitly_wait(self.config['browser']['implicit_wait'])
        self.driver.set_page_load_timeout(self.config['browser']['page_load_timeout'])
        
        # Initialize WebDriverWait
        self.wait = WebDriverWait(
            self.driver,
            self.config['timeouts']['element_wait']
        )
        
        self.logger.info("WebDriver setup complete")
    
    def navigate_to_form(self):
        """Navigate to the visa application form"""
        url = self.config['url']
        self.logger.info(f"Navigating to {url}")
        self.driver.get(url)
        time.sleep(2)  # Allow page to fully load
        self.logger.info("Page loaded successfully")
    
    def fill_text_field(self, field_name: str, value: str, required: bool = True):
        """Fill a text input field"""
        if not value and not required:
            return
        
        try:
            selector = self.config['form_selectors'][field_name]
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            element.clear()
            element.send_keys(value)
            self.logger.debug(f"Filled {field_name}: {value}")
        except Exception as e:
            self.logger.error(f"Error filling {field_name}: {e}")
            raise
    
    def fill_textarea_field(self, field_name: str, value: str, required: bool = True):
        """Fill a textarea field"""
        self.fill_text_field(field_name, value, required)
    
    def select_dropdown(self, field_name: str, value: str, mapping_key: Optional[str] = None):
        """Select value from dropdown"""
        try:
            selector = self.config['form_selectors'][field_name]
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # Use mapping if provided
            if mapping_key and mapping_key in self.config:
                mapped_value = self.config[mapping_key].get(value, value)
            else:
                mapped_value = value
            
            select = Select(element)
            select.select_by_visible_text(mapped_value)
            self.logger.debug(f"Selected {field_name}: {mapped_value}")
        except Exception as e:
            self.logger.error(f"Error selecting {field_name}: {e}")
            raise
    
    def fill_date_field(self, field_name: str, date_value: str):
        """Fill a date field (handles hidden inputs with JavaScript)"""
        try:
            date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%Y-%m-%d')
            
            selector = self.config['form_selectors'][field_name]
            element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            # Check if element is hidden - use JavaScript if so
            if element.get_attribute('type') == 'hidden':
                # Use JavaScript to set the value
                self.driver.execute_script(
                    f"arguments[0].value = '{formatted_date}';", 
                    element
                )
                self.logger.debug(f"Filled hidden date {field_name} using JavaScript: {formatted_date}")
            else:
                # Regular text input
                element.clear()
                element.send_keys(formatted_date)
                self.logger.debug(f"Filled {field_name}: {formatted_date}")
                
        except ValueError as e:
            self.logger.error(f"Invalid date format for {field_name}: {date_value}")
            raise
        except Exception as e:
            self.logger.error(f"Error filling date field {field_name}: {e}")
            raise
    
    def fill_date_dropdowns(self, base_field_name: str, date_value: str):
        """Fill date using separate month/day/year dropdowns"""
        try:
            date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            
            # Month mapping (English month names)
            months = {
                1: "يناير / January",
                2: "فبراير / February",
                3: "مارس / March",
                4: "أبريل / April",
                5: "مايو / May",
                6: "يونيو / June",
                7: "يوليو / July",
                8: "أغسطس / August",
                9: "سبتمبر / September",
                10: "أكتوبر / October",
                11: "نوفمبر / November",
                12: "ديسمبر / December"
            }
            
            # Fill month
            month_selector = self.config['form_selectors'][f'{base_field_name}_month']
            month_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, month_selector))
            )
            month_select = Select(month_element)
            month_select.select_by_visible_text(months[date_obj.month])
            self.logger.debug(f"Selected month: {months[date_obj.month]}")
            
            # Fill day
            day_selector = self.config['form_selectors'][f'{base_field_name}_day']
            day_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, day_selector))
            )
            day_select = Select(day_element)
            day_select.select_by_visible_text(str(date_obj.day))
            self.logger.debug(f"Selected day: {date_obj.day}")
            
            # Fill year
            year_selector = self.config['form_selectors'][f'{base_field_name}_year']
            year_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, year_selector))
            )
            year_select = Select(year_element)
            year_select.select_by_visible_text(str(date_obj.year))
            self.logger.debug(f"Selected year: {date_obj.year}")
            
        except ValueError as e:
            self.logger.error(f"Invalid date format for {base_field_name}: {date_value}")
            raise
        except Exception as e:
            self.logger.error(f"Error filling date dropdowns for {base_field_name}: {e}")
            raise
    
    def fill_passport_date(self, field_name: str, date_value: str):
        """Fill passport dates using dropdowns (they reuse birthday selector names)"""
        try:
            date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            
            # Month mapping
            months = {
                1: "يناير / January",
                2: "فبراير / February",
                3: "مارس / March",
                4: "أبريل / April",
                5: "مايو / May",
                6: "يونيو / June",
                7: "يوليو / July",
                8: "أغسطس / August",
                9: "سبتمبر / September",
                10: "أكتوبر / October",
                11: "نوفمبر / November",
                12: "ديسمبر / December"
            }
            
            # Get all dropdowns with name birthday[month], birthday[day], birthday[year]
            # We need to use the correct index based on which date we're filling
            # issued_on uses index 1 (second set), expires_on uses index 2 (third set)
            
            if field_name == 'issued_on':
                dropdown_index = 1  # Second set of dropdowns
            elif field_name == 'expires_on':
                dropdown_index = 2  # Third set of dropdowns
            else:
                dropdown_index = 0
            
            # Find all month dropdowns
            month_elements = self.driver.find_elements(By.CSS_SELECTOR, "select[name='birthday[month]']")
            if len(month_elements) > dropdown_index:
                month_select = Select(month_elements[dropdown_index])
                month_select.select_by_visible_text(months[date_obj.month])
                self.logger.debug(f"Selected {field_name} month: {months[date_obj.month]}")
            
            # Find all day dropdowns
            day_elements = self.driver.find_elements(By.CSS_SELECTOR, "select[name='birthday[day]']")
            if len(day_elements) > dropdown_index:
                day_select = Select(day_elements[dropdown_index])
                day_select.select_by_visible_text(str(date_obj.day))
                self.logger.debug(f"Selected {field_name} day: {date_obj.day}")
            
            # Find all year dropdowns
            year_elements = self.driver.find_elements(By.CSS_SELECTOR, "select[name='birthday[year]']")
            if len(year_elements) > dropdown_index:
                year_select = Select(year_elements[dropdown_index])
                year_select.select_by_visible_text(str(date_obj.year))
                self.logger.debug(f"Selected {field_name} year: {date_obj.year}")
            
        except ValueError as e:
            self.logger.error(f"Invalid date format for {field_name}: {date_value}")
            raise
        except Exception as e:
            self.logger.error(f"Error filling passport date {field_name}: {e}")
            raise
    
    def fill_arrival_date(self, date_value: str):
        """Fill arrival date using dropdowns (4th set of birthday dropdowns)"""
        try:
            date_obj = datetime.strptime(date_value, '%Y-%m-%d')
            
            # Month mapping
            months = {
                1: "يناير / January",
                2: "فبراير / February",
                3: "مارس / March",
                4: "أبريل / April",
                5: "مايو / May",
                6: "يونيو / June",
                7: "يوليو / July",
                8: "أغسطس / August",
                9: "سبتمبر / September",
                10: "أكتوبر / October",
                11: "نوفمبر / November",
                12: "ديسمبر / December"
            }
            
            dropdown_index = 3  # Fourth set of dropdowns (0-based index)
            
            # Find all month dropdowns
            month_elements = self.driver.find_elements(By.CSS_SELECTOR, "select[name='birthday[month]']")
            if len(month_elements) > dropdown_index:
                month_select = Select(month_elements[dropdown_index])
                month_select.select_by_visible_text(months[date_obj.month])
                self.logger.debug(f"Selected arrival month: {months[date_obj.month]}")
            
            # Find all day dropdowns
            day_elements = self.driver.find_elements(By.CSS_SELECTOR, "select[name='birthday[day]']")
            if len(day_elements) > dropdown_index:
                day_select = Select(day_elements[dropdown_index])
                day_select.select_by_visible_text(str(date_obj.day))
                self.logger.debug(f"Selected arrival day: {date_obj.day}")
            
            # Find all year dropdowns
            year_elements = self.driver.find_elements(By.CSS_SELECTOR, "select[name='birthday[year]']")
            if len(year_elements) > dropdown_index:
                year_select = Select(year_elements[dropdown_index])
                year_select.select_by_visible_text(str(date_obj.year))
                self.logger.debug(f"Selected arrival year: {date_obj.year}")
            
        except ValueError as e:
            self.logger.error(f"Invalid date format for arrival date: {date_value}")
            raise
        except Exception as e:
            self.logger.error(f"Error filling arrival date: {e}")
            raise
    
    def take_screenshot(self, name: str):
        """Take a screenshot"""
        screenshot_dir = Path(self.config['output']['screenshot_directory'])
        screenshot_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = screenshot_dir / f"{name}_{timestamp}.png"
        self.driver.save_screenshot(str(filepath))
        self.logger.info(f"Screenshot saved: {filepath}")
        return filepath
    
    def quit(self):
        """Close the browser and cleanup"""
        if self.driver:
            self.logger.info("Closing browser...")
            self.driver.quit()
            self.driver = None


class VisaFormFiller:
    """High-level form filler using automation engine"""
    
    def __init__(self, automation: EgyptVisaFormAutomation):
        self.auto = automation
        self.logger = automation.logger
    
    def fill_personal_info(self, app: VisaApplication):
        """Fill personal information section"""
        self.logger.info("Filling personal information...")
        
        self.auto.fill_text_field('first_name', app.first_name)
        self.auto.fill_text_field('middle_name', app.middle_name)
        self.auto.fill_text_field('family_name', app.family_name)
        self.auto.fill_date_dropdowns('date_of_birth', app.date_of_birth)
        self.auto.fill_text_field('place_of_birth', app.place_of_birth)
        self.auto.select_dropdown('sex', app.sex, 'sex_mapping')
        self.auto.select_dropdown('marital_status', app.marital_status, 'marital_status_mapping')
    
    def fill_nationality(self, app: VisaApplication):
        """Fill nationality information"""
        self.logger.info("Filling nationality information...")
        
        self.auto.fill_text_field('present_nationality', app.present_nationality)
        self.auto.fill_text_field('nationality_of_origin', app.nationality_of_origin)
    
    def fill_occupation(self, app: VisaApplication):
        """Fill occupation information"""
        self.logger.info("Filling occupation...")
        
        self.auto.fill_text_field('occupation_arabic', app.occupation_arabic)
    
    def fill_passport(self, app: VisaApplication):
        """Fill passport information"""
        self.logger.info("Filling passport information...")
        
        self.auto.fill_text_field('passport_number', app.passport_number)
        self.auto.fill_text_field('passport_type', app.passport_type)
        self.auto.fill_text_field('issued_at', app.issued_at)
        # Passport dates use dropdowns (not hidden fields)
        # Note: The form might reuse the same selectors, we'll need to target them differently
        self.logger.info("Filling passport issued date...")
        self.auto.fill_passport_date('issued_on', app.issued_on)
        self.logger.info("Filling passport expiry date...")
        self.auto.fill_passport_date('expires_on', app.expires_on)
    
    def fill_addresses(self, app: VisaApplication):
        """Fill address information"""
        self.logger.info("Filling addresses...")
        
        self.auto.fill_text_field('permanent_address', app.permanent_address)
        self.auto.fill_text_field('present_address', app.present_address)
    
    def fill_visa_details(self, app: VisaApplication):
        """Fill visa-specific information"""
        self.logger.info("Filling visa details...")
        
        self.auto.select_dropdown('visa_type', app.visa_type, 'visa_type_mapping')
        self.auto.fill_text_field('duration_of_stay', app.duration_of_stay)
        # Date of arrival also uses dropdowns (4th set)
        self.logger.info("Filling arrival date...")
        self.auto.fill_arrival_date(app.date_of_arrival)
        self.auto.fill_text_field('purpose_of_visit', app.purpose_of_visit)
        self.auto.fill_text_field('address_in_egypt', app.address_in_egypt)
        self.auto.fill_text_field('port_of_entry', app.port_of_entry)
    
    def fill_contact(self, app: VisaApplication):
        """Fill contact information"""
        self.logger.info("Filling contact information...")
        
        self.auto.fill_text_field('phone_number', app.phone_number)
    
    def fill_relatives(self, app: VisaApplication):
        """Fill relatives/friends in Egypt"""
        self.logger.info(f"Filling {len(app.relatives)} relative(s)...")
        
        for idx, relative in enumerate(app.relatives):
            if idx == 0:
                # First relative uses default fields
                self.auto.fill_text_field('relative_name', relative.full_name)
                self.auto.fill_text_field('relative_address', relative.address)
            else:
                # Additional relatives - click "Add another person" button
                try:
                    add_button_selector = self.auto.config['form_selectors']['add_relative_button']
                    add_button = self.auto.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, add_button_selector))
                    )
                    add_button.click()
                    time.sleep(1)  # Wait for new fields to appear
                    
                    # Fill the new fields (implementation depends on form structure)
                    # This might need adjustment based on actual form behavior
                    self.logger.warning("Multiple relatives feature needs form-specific implementation")
                except Exception as e:
                    self.logger.warning(f"Could not add relative {idx + 1}: {e}")
    
    def fill_complete_form(self, app: VisaApplication):
        """Fill the complete application form"""
        self.logger.info("Starting form fill process...")
        
        try:
            self.fill_personal_info(app)
            self.fill_nationality(app)
            self.fill_occupation(app)
            self.fill_passport(app)
            self.fill_addresses(app)
            self.fill_visa_details(app)
            self.fill_contact(app)
            self.fill_relatives(app)
            
            self.logger.info("Form filled successfully!")
            self.auto.take_screenshot("form_completed")
            
        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            self.auto.take_screenshot("form_error")
            raise


if __name__ == "__main__":
    # Test the automation
    config_path = Path(__file__).parent / "config" / "config.json"
    sample_data = Path(__file__).parent / "data" / "sample_application.json"
    
    automation = EgyptVisaFormAutomation(config_path)
    
    try:
        automation.setup_driver()
        automation.navigate_to_form()
        
        # Load and validate application
        app = VisaApplication.from_json_file(sample_data)
        is_valid, errors = app.validate()
        
        if not is_valid:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            # Fill the form
            filler = VisaFormFiller(automation)
            filler.fill_complete_form(app)
            
            # Wait to see the result
            input("Press Enter to close browser...")
    
    finally:
        automation.quit()

