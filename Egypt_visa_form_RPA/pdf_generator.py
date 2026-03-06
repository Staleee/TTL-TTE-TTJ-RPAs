"""
PDF generation and export functionality for Egypt visa forms
"""

import time
import json
import base64
from pathlib import Path
from datetime import datetime
import logging
import platform

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# For PNG to PDF conversion
import img2pdf
from PIL import Image

# Optional QR verification dependencies (cv2 can fail with numpy 2.x)
QR_VERIFICATION_AVAILABLE = False
try:
    import cv2
    import numpy as np
    from pyzbar.pyzbar import decode as decode_qr
    QR_VERIFICATION_AVAILABLE = True
except Exception:
    # QR verification disabled if cv2/pyzbar missing or numpy incompatible
    pass


class PDFGenerator:
    """Handles PDF generation from completed visa forms"""
    
    def __init__(self, driver, config: dict, logger: logging.Logger):
        self.driver = driver
        self.config = config
        self.logger = logger
        self.output_dir = Path(config['output']['pdf_directory'])
        self.output_dir.mkdir(exist_ok=True)
        
        # QR settings from config
        self.qr_settings = config.get('qr_settings', {
            'wait_timeout': 30,
            'verification_enabled': True,
            'network_idle_timeout': 15,
            'poll_interval': 1.5,
            'max_retries': 3
        })
    
    def detect_network_idle(self, timeout: int = None) -> bool:
        """
        Wait for network to be idle (no pending AJAX/XHR requests)
        
        Args:
            timeout: Maximum seconds to wait (uses config default if None)
        
        Returns:
            True if network became idle, False if timeout
        """
        if timeout is None:
            timeout = self.qr_settings['network_idle_timeout']
        
        self.logger.info(f"Waiting for network idle (timeout: {timeout}s)...")
        
        start_time = time.time()
        poll_interval = 0.5
        
        while time.time() - start_time < timeout:
            try:
                # Check if there are any pending XHR/fetch requests
                is_idle = self.driver.execute_script("""
                    // Check if there are pending XHR requests
                    if (typeof window.activeXHRCount !== 'undefined') {
                        return window.activeXHRCount === 0;
                    }
                    
                    // Alternative: Check performance entries for incomplete requests
                    const resources = window.performance.getEntriesByType('resource');
                    const pendingRequests = resources.filter(r => {
                        return r.initiatorType === 'xmlhttprequest' && !r.responseEnd;
                    });
                    
                    // Also check for ongoing fetch requests
                    if (typeof window.activeFetchCount !== 'undefined') {
                        return pendingRequests.length === 0 && window.activeFetchCount === 0;
                    }
                    
                    return pendingRequests.length === 0;
                """)
                
                if is_idle:
                    elapsed = time.time() - start_time
                    self.logger.info(f"✓ Network idle detected after {elapsed:.1f}s")
                    return True
                
                time.sleep(poll_interval)
                
            except Exception as e:
                self.logger.warning(f"Error checking network status: {e}")
                # If we can't check, assume it's idle after a reasonable wait
                if time.time() - start_time > timeout / 2:
                    return True
        
        self.logger.warning(f"Network idle timeout after {timeout}s")
        return False
    
    def get_qr_image_info(self) -> dict:
        """
        Get information about QR code image on the page
        
        Returns:
            Dict with QR image details (src, id, timestamp, etc.) or None
        """
        try:
            # Look for QR code images
            qr_images = self.driver.find_elements(By.CSS_SELECTOR, 
                "img[src*='qr'], img[alt*='QR'], img[alt*='qr'], img.qr-code, #qrcode img, .qr-code img")
            
            if not qr_images:
                # Try to find any img inside elements with 'qr' in class/id
                qr_containers = self.driver.find_elements(By.XPATH, 
                    "//*[contains(@class, 'qr') or contains(@id, 'qr')]//img")
                if qr_containers:
                    qr_images = qr_containers
            
            if not qr_images:
                # Last resort: find all images and filter by size (QR codes are usually square)
                all_images = self.driver.find_elements(By.TAG_NAME, "img")
                qr_images = [img for img in all_images if img.is_displayed() and 
                           abs(img.size['width'] - img.size['height']) < 50 and 
                           img.size['width'] > 100]
            
            if qr_images:
                # Get the first visible QR image
                for img in qr_images:
                    if img.is_displayed():
                        info = {
                            'src': img.get_attribute('src'),
                            'id': img.get_attribute('id'),
                            'class': img.get_attribute('class'),
                            'width': img.size['width'],
                            'height': img.size['height'],
                            'alt': img.get_attribute('alt'),
                            'element': img
                        }
                        self.logger.debug(f"QR image found: {info['src'][:100] if info['src'] else 'No src'}...")
                        return info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting QR image info: {e}")
            return None
    
    def wait_for_qr_update(self, initial_qr_info: dict = None, timeout: int = None) -> bool:
        """
        Wait for QR code to be updated/regenerated after form submission
        
        Args:
            initial_qr_info: QR info before submission (to detect changes)
            timeout: Maximum seconds to wait
        
        Returns:
            True if QR was updated, False if timeout or error
        """
        if timeout is None:
            timeout = self.qr_settings['wait_timeout']
        
        poll_interval = self.qr_settings['poll_interval']
        
        self.logger.info(f"Waiting for QR code update (timeout: {timeout}s)...")
        
        start_time = time.time()
        initial_src = initial_qr_info['src'] if initial_qr_info else None
        
        while time.time() - start_time < timeout:
            try:
                current_qr_info = self.get_qr_image_info()
                
                if current_qr_info:
                    current_src = current_qr_info['src']
                    
                    # Check if QR source changed
                    if initial_src and current_src and current_src != initial_src:
                        elapsed = time.time() - start_time
                        self.logger.info(f"✓ QR code updated after {elapsed:.1f}s")
                        self.logger.debug(f"  Old src: {initial_src[:80]}...")
                        self.logger.debug(f"  New src: {current_src[:80]}...")
                        return True
                    
                    # If we don't have initial info, wait a bit then accept current QR
                    if not initial_src and time.time() - start_time > 3:
                        self.logger.info("QR code detected (no baseline for comparison)")
                        return True
                
                time.sleep(poll_interval)
                
            except Exception as e:
                self.logger.warning(f"Error checking QR update: {e}")
                time.sleep(poll_interval)
        
        elapsed = time.time() - start_time
        self.logger.warning(f"QR update timeout after {elapsed:.1f}s")
        return False
    
    def decode_qr_code(self, screenshot_path: Path = None) -> dict:
        """
        Decode QR code from screenshot to verify data
        
        Args:
            screenshot_path: Path to screenshot, or None to capture current page
        
        Returns:
            Dict with decoded data and status
        """
        if not self.qr_settings['verification_enabled']:
            return {'verified': False, 'reason': 'Verification disabled in config'}
        
        if not QR_VERIFICATION_AVAILABLE:
            return {'verified': False, 'reason': 'QR verification libraries not available (pyzbar/opencv not installed)'}
        
        try:
            # Capture screenshot if not provided
            if not screenshot_path:
                temp_screenshot = self.output_dir / f"temp_qr_verify_{int(time.time())}.png"
                self.driver.save_screenshot(str(temp_screenshot))
                screenshot_path = temp_screenshot
            else:
                temp_screenshot = None
            
            # Read image
            img = cv2.imread(str(screenshot_path))
            if img is None:
                return {'verified': False, 'error': 'Could not read screenshot'}
            
            # Decode QR codes
            decoded_objects = decode_qr(img)
            
            if decoded_objects:
                qr_data = []
                for obj in decoded_objects:
                    try:
                        data = obj.data.decode('utf-8')
                        qr_data.append({
                            'type': obj.type,
                            'data': data,
                            'rect': obj.rect
                        })
                        self.logger.info(f"✓ QR decoded: {data[:100]}..." if len(data) > 100 else f"✓ QR decoded: {data}")
                    except Exception as e:
                        self.logger.warning(f"Could not decode QR data: {e}")
                
                # Clean up temp screenshot
                if temp_screenshot and temp_screenshot.exists():
                    temp_screenshot.unlink()
                
                return {
                    'verified': True,
                    'qr_count': len(qr_data),
                    'qr_data': qr_data
                }
            else:
                self.logger.warning("⚠ No QR codes found in screenshot")
                
                # Clean up temp screenshot
                if temp_screenshot and temp_screenshot.exists():
                    temp_screenshot.unlink()
                
                return {'verified': False, 'reason': 'No QR codes detected in image'}
        
        except Exception as e:
            self.logger.error(f"Error decoding QR code: {e}")
            return {'verified': False, 'error': str(e)}
    
    def click_create_and_print_button(self):
        """Click the 'Create and print form' button and wait for QR code generation with intelligent detection"""
        self.logger.info("Looking for create and print button...")
        
        try:
            # Wait for the form to be ready
            time.sleep(1)
            
            # PHASE 1: Get initial QR state (before submission)
            self.logger.info("📸 Capturing initial page state...")
            initial_qr_info = self.get_qr_image_info()
            if initial_qr_info:
                self.logger.info(f"Initial QR detected: {initial_qr_info['src'][:80] if initial_qr_info['src'] else 'No src'}...")
            else:
                self.logger.info("No QR code on page yet (expected before submission)")
            
            initial_url = self.driver.current_url
            self.logger.debug(f"Initial URL: {initial_url}")
            
            # Take diagnostic screenshot before submission
            try:
                screenshot_dir = Path(self.config['output']['screenshot_directory'])
                screenshot_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                before_submit_path = screenshot_dir / f"before_submit_{timestamp}.png"
                self.driver.save_screenshot(str(before_submit_path))
                self.logger.debug(f"Screenshot saved: {before_submit_path}")
            except Exception as e:
                self.logger.warning(f"Could not save before-submit screenshot: {e}")
            
            # PHASE 2: Find and click submit button
            possible_selectors = [
                "button[type='submit']",
                "button:contains('أنشاء و طباعة النموذج')",
                "button:contains('Create and print')",
                ".btn-primary",
                "button.create-print"
            ]
            
            button = None
            for selector in possible_selectors:
                try:
                    if ':contains' in selector:
                        # Use XPath for text-based search
                        xpath = f"//button[contains(text(), 'أنشاء و طباعة النموذج') or contains(text(), 'Create and print')]"
                        button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if button and button.is_displayed():
                        self.logger.info(f"✓ Submit button found with selector: {selector}")
                        break
                except:
                    continue
            
            if not button:
                self.logger.error("❌ Create and print button not found")
                return False
            
            # Scroll into view and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.5)
            
            click_time = time.time()
            button.click()
            self.logger.info("✓ Create and print button clicked")
            
            # PHASE 3: Wait for network activity to complete
            self.logger.info("⏳ Waiting for form submission to complete...")
            network_idle = self.detect_network_idle()
            
            if network_idle:
                self.logger.info("✓ Network activity completed")
            else:
                self.logger.warning("⚠ Network idle timeout - proceeding anyway")
            
            # PHASE 4: Wait for QR code to be generated/updated
            self.logger.info("⏳ Waiting for QR code generation...")
            qr_updated = self.wait_for_qr_update(initial_qr_info)
            
            # Additional wait after QR appears to ensure it's fully rendered
            if qr_updated:
                self.logger.info("⏳ Allowing extra time for QR rendering...")
                time.sleep(1.5)
            else:
                # If update detection failed, use fallback timing
                self.logger.warning("⚠ QR update detection inconclusive - using fallback wait")
                time.sleep(2.5)
            
            # PHASE 5: Verify QR code presence and optionally decode
            final_qr_info = self.get_qr_image_info()
            qr_found = False
            
            if final_qr_info:
                self.logger.info(f"✓ Final QR code detected on page")
                self.logger.info(f"  Size: {final_qr_info['width']}x{final_qr_info['height']}")
                self.logger.info(f"  Src: {final_qr_info['src'][:100] if final_qr_info['src'] else 'N/A'}...")
                qr_found = True
                
                # Verify QR contains data (if enabled and libraries available)
                if self.qr_settings['verification_enabled']:
                    if QR_VERIFICATION_AVAILABLE:
                        self.logger.info("🔍 Verifying QR code data...")
                        verification_result = self.decode_qr_code()
                        
                        if verification_result.get('verified'):
                            qr_count = verification_result.get('qr_count', 0)
                            self.logger.info(f"✅ QR code verified - {qr_count} QR code(s) decoded successfully")
                            
                            # Log decoded data (truncated for security)
                            for idx, qr in enumerate(verification_result.get('qr_data', [])):
                                data_preview = qr['data'][:150] + ('...' if len(qr['data']) > 150 else '')
                                self.logger.info(f"  QR {idx+1} type: {qr['type']}, data length: {len(qr['data'])} chars")
                                self.logger.debug(f"  QR {idx+1} data preview: {data_preview}")
                        else:
                            reason = verification_result.get('reason', verification_result.get('error', 'Unknown'))
                            self.logger.info(f"ℹ️  QR verification skipped: {reason}")
                            # Don't fail - QR might still be valid but verification failed
                    else:
                        self.logger.info("ℹ️  QR verification skipped (pyzbar/opencv not installed - see INSTALL_NEW_DEPENDENCIES.md)")
            else:
                self.logger.warning("⚠ QR code not detected after submission")
            
            # PHASE 6: Take diagnostic screenshot after submission
            try:
                after_submit_path = screenshot_dir / f"after_submit_{timestamp}.png"
                self.driver.save_screenshot(str(after_submit_path))
                self.logger.debug(f"Screenshot saved: {after_submit_path}")
            except Exception as e:
                self.logger.warning(f"Could not save after-submit screenshot: {e}")
            
            # Check if URL changed
            final_url = self.driver.current_url
            if final_url != initial_url:
                self.logger.info(f"✓ URL changed after submission")
                self.logger.debug(f"  From: {initial_url}")
                self.logger.debug(f"  To: {final_url}")
            
            total_wait_time = time.time() - click_time
            self.logger.info(f"✓ Form submission complete (total wait: {total_wait_time:.1f}s)")
            
            # Store whether QR was found for PDF generation method selection
            self.driver.qr_detected = qr_found
            
            return True
        
        except Exception as e:
            self.logger.error(f"❌ Error in form submission process: {e}", exc_info=True)
            return False
    
    def generate_pdf_via_print(self, filename: str) -> Path:
        """
        Generate PDF using browser's print functionality - captures all pages including QR
        """
        self.logger.info(f"Generating PDF: {filename}")
        
        try:
            pdf_path = self.output_dir / filename
            
            # Extra wait to ensure QR code and all content is fully rendered
            self.logger.info("Waiting for complete form rendering (including QR code)...")
            time.sleep(2)
            
            # Scroll to top to ensure proper rendering
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
            
            # Use Chrome DevTools Protocol to print to PDF with optimized settings
            # Settings optimized to capture full page width and high-quality QR codes
            result = self.driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,  # Include backgrounds and colors
                "landscape": False,       # Portrait orientation
                "paperWidth": 8.27,      # A4 width in inches
                "paperHeight": 11.69,    # A4 height in inches  
                "marginTop": 0.4,        # Small margins to prevent chopping
                "marginBottom": 0.4,
                "marginLeft": 0.4,
                "marginRight": 0.4,
                "preferCSSPageSize": False,  # Don't use CSS page size (can cause issues)
                "displayHeaderFooter": False,
                "scale": 1.0,            # 100% scale for clarity
                "transferMode": "ReturnAsBase64",
                "generateTaggedPDF": False,
                "generateDocumentOutline": False
            })
            
            # Decode the base64 PDF data
            pdf_data = base64.b64decode(result['data'])
            
            # Write to file
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            
            # Check if PDF was created successfully
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                self.logger.info(f"✓ PDF saved successfully: {pdf_path} ({pdf_path.stat().st_size / 1024:.1f} KB)")
                return pdf_path
            else:
                raise Exception("PDF file is empty or not created")
        
        except Exception as e:
            self.logger.error(f"Error generating PDF: {e}")
            
            # Fallback: try screenshot method
            self.logger.info("Attempting fallback screenshot method...")
            return self._generate_screenshot_fallback(filename)
    
    def _generate_screenshot_fallback(self, filename: str) -> Path:
        """
        Fallback method: capture all pages and convert to multi-page PDF
        """
        try:
            # Look for multiple pages/sections in the generated form
            # The form might be split into multiple divs/sections
            self.logger.info("Capturing multi-page form...")
            
            # Scroll to top first
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Get all form pages/sections
            pages = []
            
            # Try to find page breaks or form sections
            page_elements = self.driver.find_elements(By.CSS_SELECTOR, ".page, .form-page, [class*='page']")
            
            if not page_elements:
                # No explicit pages found, capture the whole form in sections
                # Get total height
                total_height = self.driver.execute_script(
                    "return Math.max( document.body.scrollHeight, document.body.offsetHeight, "
                    "document.documentElement.clientHeight, document.documentElement.scrollHeight, "
                    "document.documentElement.offsetHeight );"
                )
                
                # A4 height at 1200px width is approximately 1697px
                # Capture in A4-sized chunks to simulate pages
                page_height = 1697
                num_pages = (total_height // page_height) + 1
                
                self.logger.info(f"Capturing {num_pages} page(s) from form (total height: {total_height}px)")
                
                for page_num in range(num_pages):
                    # Scroll to the page
                    scroll_y = page_num * page_height
                    self.driver.execute_script(f"window.scrollTo(0, {scroll_y});")
                    time.sleep(0.5)
                    
                    # Set window to capture this section
                    self.driver.set_window_size(1200, min(page_height, total_height - scroll_y))
                    time.sleep(0.5)
                    
                    # Take screenshot
                    page_filename = f"page_{page_num + 1}.png"
                    page_path = self.output_dir / page_filename
                    self.driver.save_screenshot(str(page_path))
                    pages.append(page_path)
                    self.logger.info(f"✓ Captured page {page_num + 1}/{num_pages}")
            else:
                # Capture each explicit page element
                self.logger.info(f"Found {len(page_elements)} form pages")
                for idx, page_elem in enumerate(page_elements):
                    # Scroll element into view
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", page_elem)
                    time.sleep(0.5)
                    
                    # Take screenshot
                    page_filename = f"page_{idx + 1}.png"
                    page_path = self.output_dir / page_filename
                    self.driver.save_screenshot(str(page_path))
                    pages.append(page_path)
                    self.logger.info(f"✓ Captured page {idx + 1}/{len(page_elements)}")
            
            # Convert all pages to a single multi-page PDF
            pdf_path = self.output_dir / filename
            
            try:
                # Read all page images
                page_data = []
                for page_path in pages:
                    with open(page_path, 'rb') as f:
                        page_data.append(f.read())
                
                # Convert all pages to PDF
                pdf_bytes = img2pdf.convert(page_data)
                
                # Write PDF
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_bytes)
                
                self.logger.info(f"✓ Created {len(pages)}-page PDF: {pdf_path}")
                
                # Clean up temporary PNG files
                for page_path in pages:
                    page_path.unlink()
                self.logger.debug(f"Cleaned up {len(pages)} temporary PNG file(s)")
                
                return pdf_path
                
            except Exception as conv_error:
                self.logger.error(f"Error converting pages to PDF: {conv_error}")
                # Keep the PNG files if conversion fails
                self.logger.info(f"Keeping {len(pages)} PNG file(s)")
                return pages[0] if pages else None
        
        except Exception as e:
            self.logger.error(f"Multi-page capture failed: {e}")
            raise
    
    def wait_for_print_dialog(self, timeout: int = 10):
        """Wait for print dialog or print preview to appear"""
        try:
            # Check if a new window/tab opened (print preview)
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.window_handles) > 1
            )
            self.logger.info("Print dialog/preview detected")
            return True
        except TimeoutException:
            self.logger.warning("Print dialog did not appear within timeout")
            return False
    
    def click_print_button_in_preview(self):
        """Click the print button (طباعة النموذج) to open Chrome print preview"""
        try:
            self.logger.info("Looking for print button (طباعة النموذج)...")
            
            # Wait a moment for the button to appear after form generation
            time.sleep(2)
            
            # Exact selector based on user's HTML: <button class="print-btn cus-btn d-print-none">
            print_button_selectors = [
                "button.print-btn.cus-btn.d-print-none",
                "button.print-btn.cus-btn",
                "button.print-btn",
                ".print-btn",
                "//button[contains(@class, 'print-btn') and contains(text(), 'طباعة')]",
                "//button[contains(text(), 'طباعة النموذج')]"
            ]
            
            for selector in print_button_selectors:
                try:
                    if selector.startswith('//'):
                        # XPath selector
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        # CSS selector
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Check if found and visible
                    if button and button.is_displayed():
                        self.logger.info(f"✓ Found print button with selector: {selector}")
                        
                        # Scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", button)
                        time.sleep(0.5)
                        
                        # Click using JavaScript for reliability
                        self.driver.execute_script("arguments[0].click();", button)
                        self.logger.info("✓ Print button clicked - Chrome print preview should open")
                        
                        return True
                        
                except Exception as e:
                    self.logger.debug(f"Selector '{selector}' failed: {str(e)[:100]}")
                    continue
            
            self.logger.warning("⚠️  Print button not found with any selector")
            return False
        
        except Exception as e:
            self.logger.error(f"Error clicking print button: {e}")
            return False
    
    def _click_save_in_print_preview(self, filename: str) -> bool:
        """
        Click the Save button in Chrome's print preview dialog
        
        Args:
            filename: PDF filename (for keyboard shortcut fallback)
        
        Returns:
            True if save was triggered, False otherwise
        """
        try:
            self.logger.info("Looking for Save button in Chrome print preview...")
            
            # Wait for print preview to fully load
            time.sleep(2)
            
            # Chrome print preview Save button selectors
            save_button_selectors = [
                "//cr-button[@class='action-button' and contains(text(), 'Save')]",
                "//button[contains(text(), 'Save')]",
                "cr-button.action-button",
                "#sidebar button.action-button",
                "print-preview-button-strip cr-button.action-button",
                "//cr-button[contains(@class, 'action-button')]"
            ]
            
            for selector in save_button_selectors:
                try:
                    if selector.startswith('//'):
                        # XPath selector
                        save_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        # CSS selector  
                        save_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if save_button:
                        # Get button text to confirm it's the Save button
                        button_text = save_button.text.strip()
                        self.logger.info(f"Found button with text: '{button_text}'")
                        
                        if 'save' in button_text.lower():
                            self.logger.info(f"✓ Found Save button with selector: {selector}")
                            
                            # Click the Save button
                            try:
                                save_button.click()
                                self.logger.info("✓ Save button clicked successfully")
                            except:
                                # Try JavaScript click
                                self.driver.execute_script("arguments[0].click();", save_button)
                                self.logger.info("✓ Save button clicked (JavaScript)")
                            
                            return True
                            
                except Exception as e:
                    self.logger.debug(f"Save button selector '{selector}' failed: {str(e)[:100]}")
                    continue
            
            # Fallback: use keyboard shortcut (Enter key to save)
            self.logger.info("Save button not found - using Enter key shortcut...")
            actions = ActionChains(self.driver)
            actions.send_keys(Keys.RETURN).perform()
            self.logger.info("✓ Pressed Enter to save")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error clicking Save button: {e}")
            return False
    
    def save_form_as_pdf(self, filename: str, click_print: bool = True) -> Path:
        """
        Complete workflow to save the filled form as PDF using native print
        
        Args:
            filename: Output PDF filename
            click_print: Whether to click the print button to trigger Chrome print preview
        
        Returns:
            Path to the saved PDF file
        """
        self.logger.info("Starting PDF save workflow (using native print method)...")
        
        # Check if a new window opened (form preview with QR code)
        original_window = self.driver.current_window_handle
        all_windows = self.driver.window_handles
        
        if len(all_windows) > 1:
            # Switch to the new window (the one with the generated form + QR)
            for window in all_windows:
                if window != original_window:
                    self.driver.switch_to.window(window)
                    self.logger.info("✓ Switched to new window with generated form")
                    break
            time.sleep(2)  # Let the new window fully load
        else:
            self.logger.info("Form displayed in same window")
        
        # IMPORTANT: Skip print button to avoid popup, use CDP directly for best quality
        # The print button triggers Chrome's native print dialog which can't be automated reliably
        # CDP gives us full control and better rendering
        self.logger.info("ℹ️  Using optimized CDP method (avoids popup, better quality)")
        time.sleep(2)
        
        # Generate PDF directly using CDP with optimized settings
        pdf_path = self.generate_pdf_via_print(filename)
        
        # Switch back to original window
        try:
            if self.driver.current_window_handle != original_window:
                self.driver.switch_to.window(original_window)
        except:
            pass
        
        return pdf_path


def create_pdf_from_filled_form(automation, application, click_create_button: bool = True) -> Path:
    """
    Convenience function to generate PDF from a filled form
    
    Args:
        automation: EgyptVisaFormAutomation instance
        application: VisaApplication instance
        click_create_button: Whether to click the create/print button
    
    Returns:
        Path to generated PDF
    """
    pdf_gen = PDFGenerator(
        automation.driver,
        automation.config,
        automation.logger
    )
    
    # Click create and print button
    if click_create_button:
        success = pdf_gen.click_create_and_print_button()
        if not success:
            automation.logger.warning("Could not click create button, attempting PDF generation anyway")
    
    # Generate filename
    filename = application.get_output_filename()
    
    # Save as PDF (click_print=True to click the second print button)
    pdf_path = pdf_gen.save_form_as_pdf(filename, click_print=True)
    
    return pdf_path


if __name__ == "__main__":
    print("PDF Generator module - use via form_automation.py")

