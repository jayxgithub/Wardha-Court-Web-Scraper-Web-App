from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
import sqlite3
import os
from datetime import datetime
import logging
import requests
from io import BytesIO
import json
import sys
from pathlib import Path

# Add the scraper directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scraper'))

# Try to import the scraper, if it fails, we'll use a fallback
try:
    from fetch_wardha_case_data import WardhaDistrictCourtScraper
    SCRAPER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import scraper: {e}")
    SCRAPER_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database initialization
def init_db():
    """Initialize the SQLite database"""
    os.makedirs('db', exist_ok=True)
    conn = sqlite3.connect('db/court_queries.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT NOT NULL,
            case_number TEXT NOT NULL,
            filing_year INTEGER NOT NULL,
            query_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_response TEXT,
            parsed_data TEXT,
            status TEXT DEFAULT 'success',
            error_message TEXT,
            user_ip TEXT,
            court_name TEXT DEFAULT 'Wardha District Court'
        )
    ''')
    
    # Add new table for tracking court availability
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS court_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            court_name TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT NOT NULL,
            response_time INTEGER,
            last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
            error_details TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Initialize database on startup
init_db()

def test_court_website():
    """Test if the Wardha District Court website is accessible"""
    test_urls = [
        'https://wardha.dcourts.gov.in/',
        'https://wardha.dcourts.gov.in/case-status-search-by-case-number/',
        'https://wardha.dcourts.gov.in/case-status-search-by-case-type/',
        'https://districts.ecourts.gov.in/wardha',
        'https://ecourts.gov.in/',
        'https://services.ecourts.gov.in/ecourtindia_v6/'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for url in test_urls:
        try:
            start_time = datetime.now()
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if response.status_code == 200:
                logger.info(f"Court website accessible at: {url} (Response time: {response_time:.0f}ms)")
                
                # Log the successful connection
                log_court_status('Wardha District Court', url, 'accessible', response_time, None)
                return url
            else:
                log_court_status('Wardha District Court', url, 'error', response_time, f"HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to access {url}: {str(e)}")
            log_court_status('Wardha District Court', url, 'error', 0, str(e))
            continue
    
    logger.error("All Wardha District Court website URLs are inaccessible")
    return None

def log_court_status(court_name, url, status, response_time, error_details):
    """Log court website status to database"""
    try:
        conn = sqlite3.connect('db/court_queries.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO court_status 
            (court_name, url, status, response_time, error_details)
            VALUES (?, ?, ?, ?, ?)
        ''', (court_name, url, status, int(response_time), error_details))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging court status: {str(e)}")

@app.route('/')
def index():
    """Main page with the search form"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_case():
    """Handle case search requests for Wardha District Court"""
    try:
        # Get form data
        case_type = request.form.get('case_type', '').strip()
        case_number = request.form.get('case_number', '').strip()
        filing_year = request.form.get('filing_year', '').strip()
        
        # Get user IP for logging
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # Validate input
        if not all([case_type, case_number, filing_year]):
            error_msg = 'All fields are required'
            log_query(case_type, case_number, filing_year, None, None, 'validation_error', error_msg, user_ip)
            return render_template('index.html', error=error_msg)
        
        try:
            filing_year = int(filing_year)
            current_year = datetime.now().year
            if filing_year < 1950 or filing_year > current_year:
                raise ValueError(f"Year must be between 1950 and {current_year}")
        except ValueError as e:
            error_msg = f'Please enter a valid filing year (1950-{datetime.now().year})'
            log_query(case_type, case_number, filing_year, None, None, 'validation_error', error_msg, user_ip)
            return render_template('index.html', error=error_msg)
        
        # Validate case number (should be numeric for most court systems)
        if not case_number.replace('/', '').replace('-', '').isdigit():
            error_msg = 'Case number should contain only numbers, dashes, and slashes'
            log_query(case_type, case_number, filing_year, None, None, 'validation_error', error_msg, user_ip)
            return render_template('index.html', error=error_msg)
        
        logger.info(f"Processing search request for Wardha District Court: {case_type} {case_number}/{filing_year} from IP: {user_ip}")
        
        # Test court website accessibility first
        accessible_url = test_court_website()
        case_data = None
        raw_response = None
        status = 'success'
        error_message = None
        
        if SCRAPER_AVAILABLE and accessible_url:
            try:
                scraper = WardhaDistrictCourtScraper()
                logger.info(f"Fetching case data using Wardha scraper: {case_type} {case_number}/{filing_year}")
                case_data = scraper.fetch_case_data(case_type, case_number, filing_year)
                raw_response = getattr(scraper, 'last_raw_response', None)
                
                # Check if scraper returned an error
                if case_data and case_data.get('error'):
                    logger.warning(f"Scraper error: {case_data.get('error')}")
                    status = 'scraper_error'
                    error_message = case_data.get('error')
                    
                    # If it's a connection error, fall back to mock data
                    if any(keyword in str(case_data.get('error')).lower() 
                           for keyword in ['404', 'connect', 'timeout', 'network', 'maintenance']):
                        case_data = create_mock_case_data(case_type, case_number, filing_year)
                        case_data['warning'] = 'Unable to fetch live data from Wardha District Court website. Showing demo data for reference. Please try again later or check the court website directly.'
                        status = 'fallback_success'
                        error_message = 'Fallback to demo data due to website connectivity issues'
                
            except Exception as scraper_error:
                logger.error(f"Scraper exception: {str(scraper_error)}")
                status = 'scraper_exception'
                error_message = str(scraper_error)
                # Fall back to mock data
                case_data = create_mock_case_data(case_type, case_number, filing_year)
                case_data['warning'] = f'Error fetching live data: {str(scraper_error)}. Showing demo data for reference.'
                raw_response = f"Scraper error: {str(scraper_error)}"
        
        else:
            # Fallback: Create mock data
            logger.info(f"Using fallback data for Wardha District Court: {case_type} {case_number}/{filing_year}")
            case_data = create_mock_case_data(case_type, case_number, filing_year)
            case_data['warning'] = 'Wardha District Court website is currently not accessible. Showing demo data for reference.'
            raw_response = "Fallback response - Wardha District Court website not accessible or scraper not available"
            status = 'fallback_success'
            error_message = 'Website not accessible'
        
        # Ensure case_data is valid
        if not case_data:
            case_data = create_mock_case_data(case_type, case_number, filing_year)
            case_data['error'] = f'Case {case_type} {case_number}/{filing_year} not found in Wardha District Court'
            case_data['message'] = 'Please verify the case details and try again.'
            status = 'not_found'
            error_message = 'Case not found'
        
        # Log the query
        log_query(case_type, case_number, filing_year, 
                 raw_response, json.dumps(case_data, default=str), status, error_message, user_ip)
        
        return render_template('result.html', 
                             case_data=case_data,
                             case_type=case_type,
                             case_number=case_number,
                             filing_year=filing_year)
    
    except Exception as e:
        logger.error(f"Unexpected error in search_case: {str(e)}", exc_info=True)
        error_msg = 'An unexpected error occurred. Please try again.'
        log_query(case_type if 'case_type' in locals() else '', 
                 case_number if 'case_number' in locals() else '', 
                 filing_year if 'filing_year' in locals() else '', 
                 None, None, 'system_error', str(e), 
                 request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown')))
        return render_template('index.html', error=error_msg)

@app.route('/download_pdf')
def download_pdf():
    """Download PDF from Wardha District Court website"""
    try:
        pdf_url = request.args.get('url')
        filename = request.args.get('filename', 'wardha_court_document.pdf')
        
        if not pdf_url:
            logger.warning("PDF download attempted without URL")
            return jsonify({'error': 'PDF URL is required'}), 400
        
        logger.info(f"Attempting to download PDF from Wardha District Court: {pdf_url}")
        
        # Clean filename to prevent path traversal
        filename = os.path.basename(filename)
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Fetch PDF content with better error handling
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,*/*',
            'Referer': 'https://wardha.dcourts.gov.in/'
        }
        
        try:
            response = requests.get(pdf_url, headers=headers, timeout=30, verify=False, stream=True)
            response.raise_for_status()
            
            # Check if response is actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            content_length = int(response.headers.get('content-length', 0))
            
            if 'pdf' not in content_type and content_length < 1000:
                logger.warning(f"Invalid PDF response: content-type={content_type}, length={content_length}")
                return jsonify({'error': 'Invalid PDF or file not found on Wardha District Court website'}), 404
            
            # Read content
            pdf_content = response.content
            
            if len(pdf_content) < 100:  # Very small file, likely an error page
                logger.warning(f"PDF content too small: {len(pdf_content)} bytes")
                return jsonify({'error': 'PDF file appears to be corrupted or unavailable'}), 404
            
            logger.info(f"Successfully downloaded PDF from Wardha District Court: {len(pdf_content)} bytes")
            
            # Return PDF as file download
            return send_file(
                BytesIO(pdf_content),
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error downloading PDF from {pdf_url}: {str(e)}")
            return jsonify({'error': f'Failed to download PDF: Unable to access Wardha District Court website'}), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in download_pdf: {str(e)}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred while downloading PDF'}), 500

@app.route('/api/case_types')
def get_case_types():
    """API endpoint to get available case types for Wardha District Court"""
    case_types = [
        # Criminal Cases
        {'value': 'Criminal Case', 'label': 'Criminal Case - General Criminal Matter'},
        {'value': 'Sessions Case', 'label': 'Sessions Case - Sessions Trial'},
        {'value': 'Cr. Misc.', 'label': 'Cr. Misc. - Criminal Miscellaneous'},
        {'value': 'Cr. Appeal', 'label': 'Cr. Appeal - Criminal Appeal'},
        {'value': 'Bail Application', 'label': 'Bail Application - Bail Matter'},
        {'value': 'Cr. Revision', 'label': 'Cr. Revision - Criminal Revision'},
        {'value': 'Anticipatory Bail', 'label': 'Anticipatory Bail - Pre-Arrest Bail'},
        
        # Civil Cases
        {'value': 'Civil Suit', 'label': 'Civil Suit - Civil Matter'},
        {'value': 'Title Suit', 'label': 'Title Suit - Property Title'},
        {'value': 'Money Suit', 'label': 'Money Suit - Recovery of Money'},
        {'value': 'Civil Appeal', 'label': 'Civil Appeal - Appeal from Civil Court'},
        {'value': 'Civil Misc.', 'label': 'Civil Misc. - Civil Miscellaneous'},
        {'value': 'Execution', 'label': 'Execution - Execution Petition'},
        {'value': 'Partition Suit', 'label': 'Partition Suit - Property Partition'},
        
        # Special Cases
        {'value': 'Marriage Petition', 'label': 'Marriage Petition - Matrimonial Matter'},
        {'value': 'Motor Accident', 'label': 'Motor Accident - MACT Case'},
        {'value': 'Land Revenue', 'label': 'Land Revenue - Revenue Matter'},
        {'value': 'Labour Case', 'label': 'Labour Case - Industrial Dispute'},
        {'value': 'Consumer Case', 'label': 'Consumer Case - Consumer Complaint'},
        {'value': 'Misc. Application', 'label': 'Misc. Application - Miscellaneous Application'},
        
        # Family Court Cases
        {'value': 'Divorce Petition', 'label': 'Divorce Petition - Divorce Matter'},
        {'value': 'Maintenance', 'label': 'Maintenance - Maintenance Application'},
        {'value': 'Custody', 'label': 'Custody - Child Custody'},
        {'value': 'Adoption', 'label': 'Adoption - Adoption Petition'},
        
        # Juvenile Cases
        {'value': 'JJ Act', 'label': 'JJ Act - Juvenile Justice Act'},
        {'value': 'POCSO', 'label': 'POCSO - Protection of Children from Sexual Offences'},
        
        # Other Special Acts
        {'value': 'NDPS', 'label': 'NDPS - Narcotic Drugs and Psychotropic Substances'},
        {'value': 'SC/ST Act', 'label': 'SC/ST Act - Scheduled Castes and Scheduled Tribes Act'},
        {'value': 'Domestic Violence', 'label': 'Domestic Violence - Protection of Women from DV Act'},
        {'value': 'RTI Appeal', 'label': 'RTI Appeal - Right to Information Appeal'}
    ]
    return jsonify(case_types)

@app.route('/api/test_connection')
def test_connection():
    """API endpoint to test Wardha District Court website connection"""
    accessible_url = test_court_website()
    if accessible_url:
        return jsonify({
            'status': 'success',
            'accessible_url': accessible_url,
            'message': 'Wardha District Court website is accessible',
            'scraper_available': SCRAPER_AVAILABLE,
            'court': 'Wardha District Court'
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Wardha District Court website is not accessible',
            'scraper_available': SCRAPER_AVAILABLE,
            'court': 'Wardha District Court'
        }), 503

@app.route('/api/stats')
def get_stats():
    """API endpoint to get query statistics"""
    try:
        conn = sqlite3.connect('db/court_queries.db')
        cursor = conn.cursor()
        
        # Get total queries
        cursor.execute('SELECT COUNT(*) FROM queries')
        total_queries = cursor.fetchone()[0]
        
        # Get queries by status
        cursor.execute('SELECT status, COUNT(*) FROM queries GROUP BY status')
        status_counts = dict(cursor.fetchall())
        
        # Get recent queries
        cursor.execute('''
            SELECT case_type, case_number, filing_year, query_timestamp, status 
            FROM queries 
            ORDER BY query_timestamp DESC 
            LIMIT 10
        ''')
        recent_queries = cursor.fetchall()
        
        # Get court status history
        cursor.execute('''
            SELECT url, status, response_time, last_checked, error_details
            FROM court_status 
            ORDER BY last_checked DESC 
            LIMIT 5
        ''')
        court_status_history = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'total_queries': total_queries,
            'status_counts': status_counts,
            'recent_queries': recent_queries,
            'court_status_history': court_status_history,
            'court': 'Wardha District Court'
        })
    
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Unable to fetch statistics'}), 500

def create_mock_case_data(case_type, case_number, filing_year):
    """Create mock case data for Wardha District Court when scraper is not available"""
    mock_data = {
        'case_title': f"{case_type} {case_number}/{filing_year}",
        'court_name': 'District and Sessions Court, Wardha',
        'parties': {
            'petitioner': [f"Demo Petitioner for case {case_number}", "Additional Petitioner (if applicable)"],
            'respondent': [f"Demo Respondent for case {case_number}", "State of Maharashtra", "District Collector, Wardha"]
        },
        'filing_date': f"{filing_year}-03-15",
        'next_hearing_date': "2024-12-20",
        'status': "Pending for final hearing",
        'stage': "Evidence stage",
        'judge': "Shri/Smt. [Judge Name], District Judge, Wardha",
        'orders': [
            {
                'date': f"{filing_year}-04-01",
                'description': "Notice issued to respondents - Returnable on {next_date}",
                'pdf_link': None
            },
            {
                'date': f"{filing_year}-05-15",
                'description': "Interim order passed - Status quo to be maintained",
                'pdf_link': None
            },
            {
                'date': f"{filing_year}-08-22",
                'description': "Written statement filed by respondent - Evidence to commence",
                'pdf_link': None
            },
            {
                'date': f"{int(filing_year)+1}-01-10",
                'description': "Evidence of petitioner recorded - Cross-examination pending",
                'pdf_link': None
            }
        ],
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'note': 'This is demo data for Wardha District Court testing purposes. Live data could not be fetched from the court website.',
        'court_details': {
            'address': 'District and Sessions Court, Sewagram Road, Wardha - 442001, Maharashtra',
            'phone': '07152-244033',
            'email': 'wardha.court@ecourts.gov.in'
        }
    }
    
    # Add some variation based on case type
    if 'criminal' in case_type.lower() or 'cr.' in case_type.lower():
        mock_data['parties']['petitioner'] = [f"State of Maharashtra"]
        mock_data['parties']['respondent'] = [f"Accused in case {case_number}", "Surety (if any)"]
        mock_data['status'] = "Pending for charge framing"
        mock_data['stage'] = "Pre-trial stage"
    elif 'civil' in case_type.lower():
        mock_data['parties']['petitioner'] = [f"Plaintiff in case {case_number}"]
        mock_data['parties']['respondent'] = [f"Defendant in case {case_number}"]
        mock_data['status'] = "Written statement stage"
        mock_data['stage'] = "Pleadings stage"
    elif 'marriage' in case_type.lower() or 'divorce' in case_type.lower():
        mock_data['parties']['petitioner'] = [f"Petitioner spouse in case {case_number}"]
        mock_data['parties']['respondent'] = [f"Respondent spouse in case {case_number}"]
        mock_data['status'] = "Counseling stage"
        mock_data['stage'] = "Mediation/Counseling"
    elif 'motor' in case_type.lower() or 'mact' in case_type.lower():
        mock_data['parties']['petitioner'] = [f"Claimant in case {case_number}"]
        mock_data['parties']['respondent'] = [f"Owner of Vehicle", "Driver", "Insurance Company"]
        mock_data['status'] = "Evidence stage"
        mock_data['stage'] = "Assessment of compensation"
    
    return mock_data

def log_query(case_type, case_number, filing_year, raw_response, parsed_data, status, error_message=None, user_ip=None):
    """Log query details to database"""
    try:
        conn = sqlite3.connect('db/court_queries.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO queries 
            (case_type, case_number, filing_year, raw_response, parsed_data, status, error_message, user_ip, court_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (case_type, case_number, filing_year, raw_response, parsed_data, status, error_message, user_ip, 'Wardha District Court'))
        
        conn.commit()
        conn.close()
        logger.info(f"Query logged successfully for Wardha District Court: {case_type} {case_number}/{filing_year} - Status: {status}")
    
    except Exception as e:
        logger.error(f"Error logging query: {str(e)}")

@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return render_template('index.html', error="Internal server error. Please try again."), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return render_template('index.html', error="An unexpected error occurred. Please try again."), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'scraper_available': SCRAPER_AVAILABLE,
        'court': 'Wardha District Court',
        'version': '1.0.0'
    })

# Dashboard endpoint for analytics
@app.route('/dashboard')
def dashboard():
    """Simple dashboard showing system statistics"""
    try:
        conn = sqlite3.connect('db/court_queries.db')
        cursor = conn.cursor()
        
        # Get comprehensive stats
        cursor.execute('SELECT COUNT(*) FROM queries')
        total_queries = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM queries 
            GROUP BY status 
            ORDER BY COUNT(*) DESC
        ''')
        status_stats = cursor.fetchall()
        
        cursor.execute('''
            SELECT case_type, COUNT(*) 
            FROM queries 
            GROUP BY case_type 
            ORDER BY COUNT(*) DESC 
            LIMIT 10
        ''')
        case_type_stats = cursor.fetchall()
        
        cursor.execute('''
            SELECT DATE(query_timestamp) as date, COUNT(*) 
            FROM queries 
            WHERE query_timestamp >= date('now', '-7 days')
            GROUP BY DATE(query_timestamp) 
            ORDER BY date DESC
        ''')
        daily_stats = cursor.fetchall()
        
        conn.close()
        
        stats = {
            'total_queries': total_queries,
            'status_stats': status_stats,
            'case_type_stats': case_type_stats,
            'daily_stats': daily_stats,
            'court': 'Wardha District Court'
        }
        
        return render_template('dashboard.html', stats=stats)
        
    except Exception as e:
        logger.error(f"Error in dashboard: {str(e)}")
        return render_template('index.html', error="Dashboard temporarily unavailable"), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Wardha District Court Data Fetcher on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Scraper available: {SCRAPER_AVAILABLE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)