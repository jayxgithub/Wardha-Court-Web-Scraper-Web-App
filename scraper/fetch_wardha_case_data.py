import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from urllib.parse import urljoin, urlparse, quote
import json
from datetime import datetime
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Disable SSL warnings for court websites with certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class WardhaDistrictCourtScraper:
    """Enhanced scraper for Wardha District Court case data with improved error handling"""
    
    def __init__(self):
        self.base_url = "https://wardha.dcourts.gov.in"
        # Alternative URLs for Wardha District Court
        self.search_urls = [
            f"{self.base_url}/case-status-search-by-case-number/",
            f"{self.base_url}/case-status-search-by-case-type/",
            f"{self.base_url}/case-status/",
            "https://districts.ecourts.gov.in/wardha/case-status",
            "https://districts.ecourts.gov.in/wardha",
            "https://services.ecourts.gov.in/ecourtindia_v6/",
            "https://ecourts.gov.in/ecourts_home/static/district_court.php?state_cd=27&dist_cd=664",
            f"{self.base_url}/",
            # Backup eCourts URLs
            "https://hcservices.ecourts.gov.in/hcservices/Client/",
            "https://njdg.ecourts.gov.in/njdgnew/index.php"
        ]
        
        # Initialize session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.last_raw_response = None
        self.working_url = None
        self.debug_info = {}
        
        # Set up session with comprehensive headers for Indian court websites
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        })
    
    def _find_working_url(self):
        """Find a working URL from the list of possible Wardha District Court URLs"""
        if self.working_url:
            return self.working_url
            
        self.debug_info['tested_urls'] = []
        
        for url in self.search_urls:
            try:
                logger.info(f"Testing Wardha District Court URL: {url}")
                response = self.session.get(url, timeout=15, verify=False)
                
                url_test_info = {
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'content_type': response.headers.get('content-type', ''),
                    'success': response.status_code == 200,
                    'final_url': response.url
                }
                
                if response.status_code == 200:
                    # Additional checks for valid court website
                    content_lower = response.text.lower()
                    valid_indicators = [
                        'case', 'court', 'wardha', 'district', 'ecourts', 
                        'case status', 'case number', 'filing', 'petitioner',
                        'maharashtra', 'judicial', 'search'
                    ]
                    
                    valid_count = sum(1 for indicator in valid_indicators if indicator in content_lower)
                    
                    if (len(response.content) > 1000 and 
                        'html' in response.headers.get('content-type', '').lower() and
                        valid_count >= 3):
                        
                        logger.info(f"Working Wardha District Court URL found: {url}")
                        self.working_url = url
                        url_test_info['selected'] = True
                        url_test_info['valid_indicators'] = valid_count
                        self.debug_info['tested_urls'].append(url_test_info)
                        return url
                    else:
                        url_test_info['reason'] = f'Content validation failed - indicators: {valid_count}/10'
                
                self.debug_info['tested_urls'].append(url_test_info)
                    
            except Exception as e:
                logger.warning(f"Wardha District Court URL {url} failed: {str(e)}")
                self.debug_info['tested_urls'].append({
                    'url': url,
                    'error': str(e),
                    'success': False
                })
                continue
        
        logger.error("No working Wardha District Court URL found")
        return None
    
    def fetch_case_data(self, case_type, case_number, filing_year):
        """
        Fetch case data from Wardha District Court website with comprehensive error handling
        """
        try:
            logger.info(f"Starting case data fetch for Wardha District Court: {case_type} {case_number}/{filing_year}")
            
            # Reset debug info
            self.debug_info = {
                'case_type': case_type,
                'case_number': case_number,
                'filing_year': filing_year,
                'timestamp': datetime.now().isoformat(),
                'steps': [],
                'court': 'Wardha District Court'
            }
            
            # Find a working URL
            working_url = self._find_working_url()
            if not working_url:
                return {
                    'error': 'Wardha District Court website is currently not accessible',
                    'details': 'Unable to connect to Wardha District Court website. Please try again later.',
                    'debug_info': self.debug_info
                }
            
            self.debug_info['working_url'] = working_url
            self.debug_info['steps'].append('Found working Wardha District Court URL')
            
            # Load the search page
            try:
                logger.info(f"Loading Wardha District Court search page: {working_url}")
                search_page = self.session.get(working_url, timeout=20, verify=False)
                search_page.raise_for_status()
                
                self.debug_info['steps'].append('Successfully loaded search page')
                self.debug_info['search_page_info'] = {
                    'status_code': search_page.status_code,
                    'content_length': len(search_page.content),
                    'content_type': search_page.headers.get('content-type', ''),
                    'final_url': search_page.url
                }
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    return {
                        'error': f'Wardha District Court case status page not found',
                        'details': f'The URL {working_url} returned a 404 error. The website structure may have changed.',
                        'debug_info': self.debug_info
                    }
                else:
                    return {
                        'error': f'HTTP Error {e.response.status_code}',
                        'details': f'Unable to access Wardha District Court website: {str(e)}',
                        'debug_info': self.debug_info
                    }
            except requests.exceptions.RequestException as e:
                return {
                    'error': 'Network error accessing Wardha District Court website',
                    'details': str(e),
                    'debug_info': self.debug_info
                }
            
            # Parse the search page
            soup = BeautifulSoup(search_page.content, 'html.parser')
            self._analyze_page_structure(soup)
            
            # Check if the page requires CAPTCHA
            captcha_info = self._check_captcha(soup)
            if captcha_info['has_captcha']:
                return {
                    'error': 'CAPTCHA verification required',
                    'details': 'The Wardha District Court website requires CAPTCHA verification for case search.',
                    'captcha_info': captcha_info,
                    'debug_info': self.debug_info
                }
            
            # Extract form data and prepare search requests
            form_data = self._prepare_form_data(soup, case_type, case_number, filing_year)
            
            if not form_data:
                return {
                    'error': 'Unable to find search form on Wardha District Court website',
                    'details': 'The website structure may have changed or the search functionality is not available.',
                    'debug_info': self.debug_info
                }
            
            # Submit search requests with different strategies
            case_data = self._attempt_search_submissions(working_url, form_data, case_type, case_number, filing_year)
            
            if case_data and not case_data.get('error'):
                case_data['debug_info'] = self.debug_info
                case_data['court_name'] = 'District and Sessions Court, Wardha'
                return case_data
            
            # If all strategies failed, return a structured error
            return case_data or {
                'error': f'Case {case_type} {case_number}/{filing_year} not found',
                'details': 'The case was not found in the Wardha District Court database. Please verify the case details.',
                'debug_info': self.debug_info
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in fetch_case_data: {str(e)}", exc_info=True)
            return {
                'error': 'An unexpected error occurred while fetching case data from Wardha District Court',
                'details': str(e),
                'debug_info': self.debug_info
            }
    
    def _check_captcha(self, soup):
        """Check if the page has CAPTCHA requirements"""
        captcha_info = {
            'has_captcha': False,
            'captcha_type': None,
            'captcha_elements': []
        }
        
        # Look for common CAPTCHA indicators
        captcha_indicators = [
            {'selector': 'img[src*="captcha"]', 'type': 'image'},
            {'selector': 'input[name*="captcha"]', 'type': 'input'},
            {'selector': 'div.captcha', 'type': 'div'},
            {'selector': '.g-recaptcha', 'type': 'recaptcha'},
            {'selector': 'iframe[src*="recaptcha"]', 'type': 'recaptcha_iframe'},
            {'selector': 'script[src*="recaptcha"]', 'type': 'recaptcha_script'},
            {'selector': 'input[placeholder*="captcha"]', 'type': 'input_placeholder'}
        ]
        
        for indicator in captcha_indicators:
            elements = soup.select(indicator['selector'])
            if elements:
                captcha_info['has_captcha'] = True
                captcha_info['captcha_type'] = indicator['type']
                captcha_info['captcha_elements'].append({
                    'type': indicator['type'],
                    'count': len(elements),
                    'selector': indicator['selector']
                })
        
        # Check for CAPTCHA in page text
        page_text = soup.get_text().lower()
        if any(word in page_text for word in ['captcha', 'verification code', 'security code']):
            captcha_info['has_captcha'] = True
            if not captcha_info['captcha_type']:
                captcha_info['captcha_type'] = 'text_based'
        
        return captcha_info
    
    def _analyze_page_structure(self, soup):
        """Analyze the Wardha District Court page structure to understand the form layout"""
        forms = soup.find_all('form')
        self.debug_info['page_analysis'] = {
            'forms_found': len(forms),
            'form_details': [],
            'page_title': soup.title.string if soup.title else 'No title',
            'page_language': soup.get('lang', 'not specified')
        }
        
        for i, form in enumerate(forms):
            form_info = {
                'form_index': i,
                'action': form.get('action', ''),
                'method': form.get('method', 'GET').upper(),
                'inputs': [],
                'selects': [],
                'buttons': [],
                'form_id': form.get('id', ''),
                'form_class': form.get('class', [])
            }
            
            # Analyze inputs
            for inp in form.find_all('input'):
                input_info = {
                    'name': inp.get('name'),
                    'type': inp.get('type', 'text'),
                    'value': inp.get('value', ''),
                    'id': inp.get('id'),
                    'placeholder': inp.get('placeholder', ''),
                    'class': inp.get('class', []),
                    'required': inp.has_attr('required')
                }
                form_info['inputs'].append(input_info)
            
            # Analyze selects (dropdowns)
            for sel in form.find_all('select'):
                options = []
                for opt in sel.find_all('option'):
                    options.append({
                        'value': opt.get('value', ''),
                        'text': opt.get_text(strip=True),
                        'selected': opt.has_attr('selected')
                    })
                
                select_info = {
                    'name': sel.get('name'),
                    'id': sel.get('id'),
                    'class': sel.get('class', []),
                    'options_count': len(options),
                    'sample_options': options[:10],  # First 10 options
                    'required': sel.has_attr('required')
                }
                form_info['selects'].append(select_info)
            
            # Analyze buttons
            for btn in form.find_all(['button', 'input']):
                if btn.name == 'input' and btn.get('type') not in ['button', 'submit', 'reset']:
                    continue
                form_info['buttons'].append({
                    'type': btn.get('type', 'button'),
                    'name': btn.get('name'),
                    'value': btn.get('value', ''),
                    'text': btn.get_text(strip=True),
                    'class': btn.get('class', [])
                })
            
            self.debug_info['page_analysis']['form_details'].append(form_info)
    
    def _prepare_form_data(self, soup, case_type, case_number, filing_year):
        """Prepare form data for submission with multiple strategies for Wardha District Court"""
        
        # Extract viewstate and other hidden fields (common in Indian government websites)
        hidden_fields = self._extract_hidden_fields(soup)
        self.debug_info['hidden_fields_extracted'] = list(hidden_fields.keys())
        
        # Common field name variations for District Courts in Maharashtra
        form_variations = [
            # Strategy 1: Most common eCourts field names
            {
                'case_type': case_type,
                'case_no': case_number,
                'case_year': str(filing_year),
                'submit': 'Submit',
                'court_code': 'wardha'
            },
            # Strategy 2: Alternative naming conventions
            {
                'casetype': case_type,
                'caseno': case_number,
                'caseyear': str(filing_year),
                'Submit': 'Search',
                'district': 'Wardha'
            },
            # Strategy 3: Detailed form fields
            {
                'txtCaseType': case_type,
                'txtCaseNo': case_number,
                'txtYear': str(filing_year),
                'btnSearch': 'Search',
                'ddlDistrict': 'Wardha'
            },
            # Strategy 4: Dropdown-based approach
            {
                'ddlCaseType': case_type,
                'txtCaseNumber': case_number,
                'ddlYear': str(filing_year),
                'Button1': 'Submit',
                'ddlCourt': 'District Court Wardha'
            },
            # Strategy 5: Maharashtra-specific patterns
            {
                'case_type_name': case_type,
                'case_number': case_number,
                'filing_year': str(filing_year),
                'search_button': 'Get Case Status',
                'state_code': '27',  # Maharashtra state code
                'district_code': '664'  # Wardha district code
            },
            # Strategy 6: Simple form approach
            {
                'type': case_type,
                'number': case_number,
                'year': str(filing_year),
                'action': 'search'
            },
            # Strategy 7: API-style parameters
            {
                'caseType': case_type,
                'caseNumber': case_number,
                'filingYear': str(filing_year),
                'searchType': 'case_number',
                'format': 'html'
            }
        ]
        
        # Add hidden fields to each variation
        enhanced_variations = []
        for variation in form_variations:
            enhanced_variation = variation.copy()
            enhanced_variation.update(hidden_fields)
            enhanced_variations.append(enhanced_variation)
        
        self.debug_info['form_strategies'] = len(enhanced_variations)
        return enhanced_variations
    
    def _extract_hidden_fields(self, soup):
        """Extract hidden form fields including ASP.NET viewstate and other tokens"""
        hidden_fields = {}
        
        # Common hidden fields in Indian government websites
        hidden_field_names = [
            '__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION',
            '__EVENTTARGET', '__EVENTARGUMENT', '__LASTFOCUS',
            '__VIEWSTATEENCRYPTED', '__PREVIOUSPAGE', '__SCROLLPOSITIONX',
            '__SCROLLPOSITIONY', 'javax.faces.ViewState', 'authenticity_token',
            'csrf_token', '_token', 'session_id', 'form_token'
        ]
        
        # Extract by name
        for field_name in hidden_field_names:
            element = soup.find('input', {'name': field_name, 'type': 'hidden'})
            if element and element.get('value'):
                hidden_fields[field_name] = element.get('value')
                logger.debug(f"Found hidden field {field_name}: {element.get('value')[:50]}...")
        
        # Extract all hidden inputs
        all_hidden = soup.find_all('input', {'type': 'hidden'})
        for hidden in all_hidden:
            name = hidden.get('name')
            value = hidden.get('value', '')
            if name and name not in hidden_fields:
                hidden_fields[name] = value
        
        return hidden_fields
    
    def _attempt_search_submissions(self, working_url, form_data_list, case_type, case_number, filing_year):
        """Attempt form submission with different strategies for Wardha District Court"""
        
        self.debug_info['submission_attempts'] = []
        
        for idx, form_data in enumerate(form_data_list):
            attempt_info = {
                'strategy': idx + 1,
                'form_fields': list(form_data.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
            try:
                logger.info(f"Attempting Wardha District Court search submission {idx+1}/{len(form_data_list)}")
                
                # Try different submission methods
                methods_to_try = [
                    {'method': 'POST', 'endpoint': ''},
                    {'method': 'POST', 'endpoint': '/case-status-result'},
                    {'method': 'POST', 'endpoint': '/search'},
                    {'method': 'GET', 'endpoint': ''},
                    {'method': 'GET', 'endpoint': '/case-status'}
                ]
                
                for method_info in methods_to_try:
                    try:
                        url = working_url + method_info['endpoint']
                        response = self._submit_form(url, form_data, method=method_info['method'])
                        
                        if response and response.status_code == 200:
                            attempt_info['method'] = method_info['method']
                            attempt_info['endpoint'] = method_info['endpoint']
                            attempt_info['response_info'] = {
                                'status_code': response.status_code,
                                'content_length': len(response.content),
                                'final_url': response.url,
                                'content_type': response.headers.get('content-type', '')
                            }
                            
                            # Parse the response
                            case_data = self._parse_response(response, case_type, case_number, filing_year)
                            
                            if case_data and not case_data.get('error'):
                                attempt_info['result'] = 'success'
                                self.debug_info['submission_attempts'].append(attempt_info)
                                return case_data
                            else:
                                attempt_info['parse_result'] = case_data.get('error') if case_data else 'No valid data parsed'
                                break  # Try next strategy
                    except Exception as method_error:
                        logger.debug(f"Method {method_info['method']} failed: {str(method_error)}")
                        continue
                
                attempt_info['result'] = 'failed'
                
            except Exception as e:
                logger.warning(f"Wardha District Court submission strategy {idx+1} failed: {str(e)}")
                attempt_info['result'] = 'exception'
                attempt_info['error'] = str(e)
                
            finally:
                self.debug_info['submission_attempts'].append(attempt_info)
                time.sleep(2)  # Rate limiting for court website
        
        # All strategies failed
        return {
            'error': f'Case {case_type} {case_number}/{filing_year} not found in Wardha District Court',
            'details': 'Tried multiple search strategies but could not find the case. Please verify case details.',
            'strategies_attempted': len(form_data_list)
        }
    
    def _submit_form(self, url, form_data, method='POST'):
        """Submit form to Wardha District Court with proper error handling"""
        try:
            # Add referer header for better acceptance
            headers = self.session.headers.copy()
            headers['Referer'] = self.base_url
            
            if method.upper() == 'POST':
                response = self.session.post(
                    url,
                    data=form_data,
                    headers=headers,
                    timeout=30,
                    verify=False,
                    allow_redirects=True
                )
            else:
                response = self.session.get(
                    url,
                    params=form_data,
                    headers=headers,
                    timeout=30,
                    verify=False,
                    allow_redirects=True
                )
            
            if response.status_code == 200:
                self.last_raw_response = response.text
                return response
            else:
                logger.warning(f"Wardha District Court form submission returned status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error submitting form to Wardha District Court: {str(e)}")
            return None
    
    def _parse_response(self, response, case_type, case_number, filing_year):
        """Parse the response from Wardha District Court website"""
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for common error messages in Marathi and English
            page_text = soup.get_text().lower()
            error_indicators = [
                'no record found', 'record not found', 'invalid case',
                'case not found', 'no data available', 'no records found',
                'invalid input', 'please enter valid', 'not exist',
                'error occurred', 'invalid case number', 'case does not exist',
                'रेकॉर्ड आढळला नाही', 'केस सापडला नाही', 'अवैध केस',
                'कोणताही डेटा उपलब्ध नाही', 'कृपया वैध माहिती टाका'
            ]
            
            for error_msg in error_indicators:
                if error_msg in page_text:
                    return {
                        'error': f'Case {case_type} {case_number}/{filing_year} not found in Wardha District Court',
                        'message': 'Case not found in court database. Please verify case details.',
                        'found_error_indicator': error_msg
                    }
            
            # Try to extract case information
            case_data = self._extract_case_info(soup, case_type, case_number, filing_year)
            
            # If we found meaningful data, return it
            if self._is_valid_case_data(case_data):
                return case_data
            
            # Try alternative parsing methods
            alternative_data = self._alternative_parsing(soup, page_text, case_type, case_number, filing_year)
            if alternative_data:
                return alternative_data
            
            # If no data found, return error
            return {
                'error': f'Case {case_type} {case_number}/{filing_year} not found in Wardha District Court',
                'message': 'No case information could be extracted from the response.',
                'response_length': len(response.content)
            }
            
        except Exception as e:
            logger.error(f"Error parsing Wardha District Court response: {str(e)}")
            return {
                'error': 'Error parsing Wardha District Court website response',
                'details': str(e)
            }
    
    def _extract_case_info(self, soup, case_type, case_number, filing_year):
        """Extract case information from parsed HTML for Wardha District Court"""
        case_data = {
            'case_title': f"{case_type} {case_number}/{filing_year}",
            'court_name': 'District and Sessions Court, Wardha',
            'parties': {'petitioner': [], 'respondent': []},
            'filing_date': None,
            'next_hearing_date': None,
            'status': None,
            'stage': None,
            'judge': None,
            'orders': [],
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Look for tables containing case information (common in eCourts)
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if not value:
                        continue
                    
                    # Parse different fields based on labels (English and Marathi)
                    if any(keyword in label for keyword in ['petitioner', 'applicant', 'plaintiff', 'अर्जदार', 'फिर्यादी']):
                        if value not in case_data['parties']['petitioner']:
                            case_data['parties']['petitioner'].append(value)
                    elif any(keyword in label for keyword in ['respondent', 'defendant', 'प्रतिवादी', 'बचावपक्ष']):
                        if value not in case_data['parties']['respondent']:
                            case_data['parties']['respondent'].append(value)
                    elif any(keyword in label for keyword in ['filing', 'दाखल', 'date']) and 'date' in label:
                        case_data['filing_date'] = self._parse_date(value)
                    elif any(keyword in label for keyword in ['next', 'hearing', 'list', 'सुनावणी', 'पुढील']):
                        if 'date' in label:
                            case_data['next_hearing_date'] = self._parse_date(value)
                    elif any(keyword in label for keyword in ['status', 'stage', 'स्थिती', 'टप्पा']):
                        if 'status' in label:
                            case_data['status'] = value
                        else:
                            case_data['stage'] = value
                    elif any(keyword in label for keyword in ['judge', 'न्यायाधीश', 'न्यायमूर्ती']):
                        case_data['judge'] = value
                    elif any(keyword in label for keyword in ['current', 'present', 'सध्याचा']):
                        if not case_data['status']:
                            case_data['status'] = value
        
        # Look for orders and judgments
        case_data['orders'] = self._extract_orders(soup)
        
        # Look for case title in headers
        for header in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            header_text = header.get_text(strip=True)
            if (case_number in header_text and str(filing_year) in header_text) or 'wardha' in header_text.lower():
                case_data['case_title'] = header_text
                break
        
        # Look for additional case details in div elements
        for div in soup.find_all('div', class_=['case-details', 'case-info', 'result', 'case-data']):
            div_text = div.get_text()
            if case_number in div_text and str(filing_year) in div_text:
                # Extract additional information from structured divs
                self._extract_from_structured_div(div, case_data)
        
        return case_data
    
    def _extract_from_structured_div(self, div, case_data):
        """Extract information from structured div elements"""
        # Look for labeled information within the div
        labels = div.find_all(['label', 'span', 'strong', 'b'])
        for label in labels:
            label_text = label.get_text(strip=True).lower()
            
            # Try to find the corresponding value
            next_sibling = label.next_sibling
            if next_sibling:
                value = next_sibling.strip() if isinstance(next_sibling, str) else next_sibling.get_text(strip=True)
                
                if value and any(keyword in label_text for keyword in ['petitioner', 'applicant']):
                    if value not in case_data['parties']['petitioner']:
                        case_data['parties']['petitioner'].append(value)
                elif value and any(keyword in label_text for keyword in ['respondent', 'defendant']):
                    if value not in case_data['parties']['respondent']:
                        case_data['parties']['respondent'].append(value)
    
    def _is_valid_case_data(self, case_data):
        """Check if extracted case data is meaningful for Wardha District Court"""
        if not case_data:
            return False
        
        # Check if we have at least some meaningful information
        has_parties = (case_data.get('parties', {}).get('petitioner') or 
                      case_data.get('parties', {}).get('respondent'))
        has_dates = (case_data.get('filing_date') or 
                    case_data.get('next_hearing_date'))
        has_status = case_data.get('status') or case_data.get('stage')
        has_orders = case_data.get('orders')
        has_judge = case_data.get('judge')
        
        return bool(has_parties or has_dates or has_status or has_orders or has_judge)
    
    def _alternative_parsing(self, soup, page_text, case_type, case_number, filing_year):
        """Alternative parsing method for different Wardha District Court page structures"""
        
        # If the page contains the case number and year, it might be a valid response
        if (case_number in page_text and str(filing_year) in page_text and 
            len(page_text.strip()) > 500):
            
            # Extract any meaningful patterns
            patterns_found = {}
            
            # Look for date patterns (DD-MM-YYYY, DD/MM/YYYY formats common in India)
            date_patterns = [
                r'\b\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4}\b',
                r'\b\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2}\b'
            ]
            dates = []
            for pattern in date_patterns:
                dates.extend(re.findall(pattern, page_text))
            if dates:
                patterns_found['dates'] = list(set(dates))[:5]  # First 5 unique dates
            
            # Look for common legal terms in English and Marathi
            legal_terms = [
                'petitioner', 'respondent', 'plaintiff', 'defendant', 'hearing', 
                'order', 'judgment', 'court', 'case', 'filing', 'status',
                'अर्जदार', 'प्रतिवादी', 'सुनावणी', 'आदेश', 'न्यायालय', 'केस'
            ]
            found_terms = [term for term in legal_terms if term in page_text.lower()]
            if found_terms:
                patterns_found['legal_terms'] = found_terms
            
            # Look for Maharashtra-specific terms
            maharashtra_terms = ['wardha', 'maharashtra', 'district court', 'जिल्हा न्यायालय']
            found_mh_terms = [term for term in maharashtra_terms if term in page_text.lower()]
            if found_mh_terms:
                patterns_found['maharashtra_terms'] = found_mh_terms
            
            if patterns_found:
                return {
                    'case_title': f"{case_type} {case_number}/{filing_year}",
                    'court_name': 'District and Sessions Court, Wardha',
                    'parties': {
                        'petitioner': ['Case information available - please check court website directly'],
                        'respondent': ['Detailed parsing required - manual verification recommended']
                    },
                    'filing_date': f"{filing_year}-01-01",  # Placeholder
                    'next_hearing_date': None,
                    'status': "Case found but requires detailed parsing",
                    'stage': "Information extraction in progress",
                    'orders': [],
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'note': 'Partial information extracted from Wardha District Court. Please verify details on court website.',
                    'patterns_found': patterns_found
                }
        
        return None
    
    def _extract_orders(self, soup):
        """Extract order/judgment information and PDF links for Wardha District Court"""
        orders = []
        
        # Look for PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf', re.I))
        
        for link in pdf_links:
            href = link.get('href')
            if href:
                # Make absolute URL
                if not href.startswith('http'):
                    href = urljoin(self.base_url, href)
                
                link_text = link.get_text(strip=True)
                if not link_text:
                    link_text = 'Wardha District Court Document'
                
                order = {
                    'description': link_text,
                    'pdf_link': href,
                    'date': None,
                    'court': 'Wardha District Court'
                }
                
                # Try to extract date from link text or surrounding content
                date_patterns = [
                    r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})',
                    r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})'
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, link_text)
                    if date_match:
                        order['date'] = self._parse_date(date_match.group(1))
                        break
                
                if not order['date']:
                    # Look for date in parent elements
                    parent = link.parent
                    if parent:
                        parent_text = parent.get_text()
                        for pattern in date_patterns:
                            date_match = re.search(pattern, parent_text)
                            if date_match:
                                order['date'] = self._parse_date(date_match.group(1))
                                break
                
                orders.append(order)
        
        # Look for order information in tables
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    first_cell = cells[0].get_text(strip=True).lower()
                    if any(keyword in first_cell for keyword in ['order', 'judgment', 'date', 'आदेश', 'निर्णय']):
                        order_text = ' '.join([cell.get_text(strip=True) for cell in cells])
                        
                        # Check if this row contains meaningful order information
                        if (len(order_text) > 20 and 
                            not any(order['description'] == order_text for order in orders) and
                            any(keyword in order_text.lower() for keyword in ['order', 'judgment', 'hearing', 'notice'])):
                            
                            order = {
                                'description': order_text,
                                'pdf_link': None,
                                'date': None,
                                'court': 'Wardha District Court'
                            }
                            
                            # Try to extract date
                            for pattern in [r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})', r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})']:
                                date_match = re.search(pattern, order_text)
                                if date_match:
                                    order['date'] = self._parse_date(date_match.group(1))
                                    break
                            
                            orders.append(order)
        
        # Look for order lists or divs
        order_containers = soup.find_all(['div', 'ul', 'ol'], class_=re.compile(r'order|judgment|hearing', re.I))
        for container in order_containers:
            items = container.find_all(['li', 'p', 'div'])
            for item in items:
                item_text = item.get_text(strip=True)
                if (len(item_text) > 15 and 
                    any(keyword in item_text.lower() for keyword in ['order', 'hearing', 'notice', 'judgment'])):
                    
                    order = {
                        'description': item_text,
                        'pdf_link': None,
                        'date': None,
                        'court': 'Wardha District Court'
                    }
                    
                    # Look for PDF link within the item
                    pdf_link = item.find('a', href=re.compile(r'\.pdf', re.I))
                    if pdf_link:
                        href = pdf_link.get('href')
                        if not href.startswith('http'):
                            href = urljoin(self.base_url, href)
                        order['pdf_link'] = href
                    
                    # Extract date
                    for pattern in [r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})', r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})']:
                        date_match = re.search(pattern, item_text)
                        if date_match:
                            order['date'] = self._parse_date(date_match.group(1))
                            break
                    
                    if not any(existing_order['description'] == order['description'] for existing_order in orders):
                        orders.append(order)
        
        return orders[:10]  # Limit to 10 most relevant orders
    
    def _parse_date(self, date_str):
        """Parse date string into standard format (handles Indian date formats)"""
        if not date_str or not date_str.strip():
            return None
        
        date_str = date_str.strip()
        
        # Common date formats used in Indian courts
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d',
            '%d-%m-%y', '%d/%m/%y', '%y-%m-%d', '%y/%m/%d',
            '%d.%m.%Y', '%d.%m.%y', '%Y.%m.%d',
            '%d %m %Y', '%d %m %y', '%Y %m %d',
            '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
            '%B %d %Y', '%b %d %Y',
            # Marathi month names (if needed)
            '%d-%m-%Y', '%d/%m/%Y'  # Fallback to standard formats
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # Ensure the year is reasonable
                if 1950 <= parsed_date.year <= 2030:
                    return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try to extract date components manually
        date_numbers = re.findall(r'\d+', date_str)
        if len(date_numbers) >= 3:
            try:
                # Assume DD-MM-YYYY or DD/MM/YYYY format (common in India)
                day, month, year = int(date_numbers[0]), int(date_numbers[1]), int(date_numbers[2])
                
                # Handle 2-digit years
                if year < 100:
                    if year < 30:  # Assume 2000s
                        year += 2000
                    else:  # Assume 1900s
                        year += 1900
                
                # Validate ranges
                if 1 <= day <= 31 and 1 <= month <= 12 and 1950 <= year <= 2030:
                    return f"{year:04d}-{month:02d}-{day:02d}"
            except ValueError:
                pass
        
        # If no format matches, return original string
        logger.debug(f"Could not parse date from Wardha District Court: {date_str}")
        return date_str
    
    def test_connection(self):
        """Test connection to Wardha District Court website and return detailed information"""
        working_url = self._find_working_url()
        
        result = {
            'status': 'success' if working_url else 'error',
            'working_url': working_url,
            'debug_info': self.debug_info,
            'timestamp': datetime.now().isoformat(),
            'court': 'Wardha District Court'
        }
        
        if working_url:
            result['message'] = 'Wardha District Court website is accessible'
            
            # Try to get additional information about the search page
            try:
                response = self.session.get(working_url, timeout=15, verify=False)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                forms = soup.find_all('form')
                result['search_forms_found'] = len(forms)
                
                # Check for CAPTCHA
                captcha_info = self._check_captcha(soup)
                result['captcha_required'] = captcha_info['has_captcha']
                result['captcha_type'] = captcha_info['captcha_type']
                
                if forms and not captcha_info['has_captcha']:
                    result['search_capability'] = 'available'
                elif forms and captcha_info['has_captcha']:
                    result['search_capability'] = 'available_with_captcha'
                else:
                    result['search_capability'] = 'forms_not_found'
                
                # Check page language
                page_text = soup.get_text().lower()
                if any(hindi_word in page_text for hindi_word in ['न्यायालय', 'केस', 'सुनावणी', 'आदेश']):
                    result['page_language'] = 'bilingual'
                else:
                    result['page_language'] = 'english'
                    
            except Exception as e:
                result['search_capability'] = f'error_testing: {str(e)}'
                
        else:
            result['message'] = 'Wardha District Court website is not accessible'
            result['tested_urls'] = self.search_urls
            
        return result
    
    def get_supported_case_types(self):
        """Get list of supported case types from Wardha District Court website"""
        try:
            working_url = self._find_working_url()
            if not working_url:
                return []
            
            response = self.session.get(working_url, timeout=15, verify=False)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            case_types = []
            
            # Look for case type dropdowns
            case_type_selects = soup.find_all('select', {'name': re.compile(r'case.*type|type.*case', re.I)})
            
            for select in case_type_selects:
                options = select.find_all('option')
                for option in options:
                    value = option.get('value', '').strip()
                    text = option.get_text(strip=True)
                    if value and value != '0' and text.lower() not in ['select', 'choose', 'निवडा']:
                        case_types.append({
                            'value': value,
                            'label': text,
                            'source': 'website_dropdown'
                        })
            
            return case_types[:30]  # Limit to 30 types
            
        except Exception as e:
            logger.error(f"Error getting case types from Wardha District Court: {str(e)}")
            return []