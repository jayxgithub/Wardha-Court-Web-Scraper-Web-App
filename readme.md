# Wardha District Court - Case Data Fetcher

A comprehensive web application for searching and retrieving case information from Wardha District Court, Maharashtra. This system provides an intuitive interface to search cases, view details, and download court documents.

## 🏛️ Court Information

**Target Court:** District and Sessions Court, Wardha, Maharashtra  
**Website:** https://wardha.dcourts.gov.in/  
**eCourts Integration:** Part of National Judicial Data Grid  
**Jurisdiction:** Wardha District, Maharashtra State  

## 🚀 Features

### Core Functionality
- **Case Search**: Search cases by case type, number, and filing year
- **Case Details**: Display comprehensive case information including parties, dates, status
- **Document Access**: Download court orders and judgments (when available)
- **Real-time Data**: Fetch live data from official court website
- **Fallback System**: Demo data when court website is inaccessible

### Advanced Features
- **Multi-strategy Search**: Multiple search approaches for better success rate
- **CAPTCHA Detection**: Automatic detection and handling of CAPTCHA requirements
- **Connection Testing**: Built-in connectivity testing for court website
- **Analytics Dashboard**: System usage statistics and analytics
- **Responsive Design**: Mobile-friendly interface
- **Print Support**: Optimized printing of case details

### Case Types Supported
- **Criminal Cases**: Sessions, Appeals, Bail Applications, NDPS, etc.
- **Civil Cases**: Suits, Appeals, Execution petitions, etc.
- **Family Court**: Marriage, Divorce, Maintenance, Custody
- **Special Acts**: POCSO, SC/ST Act, Domestic Violence, RTI Appeals
- **Revenue**: Land revenue matters
- **Labour**: Industrial disputes

## 🛠️ Technology Stack

- **Backend**: Python 3.8+ with Flask framework
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **Web Scraping**: BeautifulSoup4, Requests with retry logic
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Styling**: Custom CSS with responsive design
- **Icons**: Font Awesome 6.0

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/wardha-court-fetcher.git
cd wardha-court-fetcher
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file in the project root:

```env
# Application Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
PORT=5000

# Database Configuration (optional)
DATABASE_URL=sqlite:///db/court_queries.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=app.log

# Court Website Configuration
COURT_BASE_URL=https://wardha.dcourts.gov.in
REQUEST_TIMEOUT=30
MAX_RETRIES=3

# Development Settings (set to True for development)
FLASK_ENV=production
FLASK_DEBUG=False
```

### 5. Initialize Database

```bash
python -c "from app import init_db; init_db()"
```

### 6. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 📁 Project Structure

```
wardha-court-fetcher/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                  # This file
├── .env                       # Environment variables (create this)
├── .gitignore                 # Git ignore file
├── scraper/
│   └── fetch_wardha_case_data.py  # Court website scraper
├── templates/
│   ├── index.html             # Search form template
│   ├── result.html            # Case details template
│   └── dashboard.html         # Analytics dashboard
├── static/
│   ├── style.css              # Application styles
│   └── js/
│       └── app.js             # Client-side JavaScript
├── db/
│   └── court_queries.db       # SQLite database (auto-created)
├── tests/
│   ├── test_app.py            # Application tests
│   └── test_scraper.py        # Scraper tests
└── docs/
    ├── API.md                 # API documentation
    └── DEPLOYMENT.md          # Deployment guide
```

## 🔍 Usage Guide

### Basic Case Search

1. **Open the Application**: Navigate to `http://localhost:5000`
2. **Select Case Type**: Choose from the dropdown (e.g., "Civil Suit", "Criminal Case")
3. **Enter Case Number**: Input the case number (e.g., "123" or "123/2024")
4. **Select Filing Year**: Enter the year when case was filed
5. **Click Search**: Submit the form to retrieve case information

### Example Searches

- **Civil Suit**: Type: "Civil Suit", Number: "45", Year: "2023"
- **Criminal Case**: Type: "Sessions Case", Number: "78", Year: "2024"
- **Marriage Petition**: Type: "Marriage Petition", Number: "12", Year: "2022"

### Advanced Features

- **Connection Test**: Click "Test Connection" to verify court website accessibility
- **Dashboard**: Visit `/dashboard` for system analytics
- **Print**: Use browser's print function or the print button for hard copies

## 🔐 CAPTCHA Strategy

### Current Approach
The system automatically detects CAPTCHA requirements on the court website and provides appropriate user feedback.

### Detection Methods
- Image-based CAPTCHA detection (`img[src*="captcha"]`)
- reCAPTCHA detection (Google reCAPTCHA elements)
- Text-based CAPTCHA detection in form fields
- JavaScript-based CAPTCHA detection

### Handling Strategy
1. **Automatic Detection**: System scans for CAPTCHA elements
2. **User Notification**: Inform users when CAPTCHA is required
3. **Graceful Fallback**: Provide demo data when CAPTCHA blocks access
4. **Manual Override**: Instructions for manual verification

### Future Enhancements
- Integration with CAPTCHA solving services (2captcha, Anti-Captcha)
- Manual CAPTCHA input field for users
- Automated CAPTCHA bypass techniques (where legally permissible)

## 📊 API Endpoints

### Public Endpoints

- `GET /` - Main search form
- `POST /search` - Submit case search
- `GET /dashboard` - Analytics dashboard
- `GET /download_pdf?url=<pdf_url>&filename=<name>` - Download court documents

### API Endpoints

- `GET /api/case_types` - Get available case types
- `GET /api/test_connection` - Test court website connectivity
- `GET /api/stats` - Get system statistics
- `GET /health` - Health check endpoint

## 🗄️ Database Schema

### Queries Table
```sql
CREATE TABLE queries (
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
);
```

### Court Status Table
```sql
CREATE TABLE court_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_name TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL,
    response_time INTEGER,
    last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_details TEXT
);
```

## 🧪 Testing

### Run Unit Tests

```bash
python -m pytest tests/ -v
```

### Test Coverage

```bash
pip install coverage
coverage run -m pytest tests/
coverage report
coverage html  # Generate HTML report
```

### Manual Testing

1. **Basic Functionality**: Test case search with various inputs
2. **Error Handling**: Test with invalid case numbers/years
3. **Connection Issues**: Test with court website down
4. **PDF Downloads**: Test document download functionality
5. **Responsive Design**: Test on mobile devices

## 🚀 Deployment

### Local Development

```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### Production Deployment

#### Option 1: Docker (Recommended)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t wardha-court-fetcher .
docker run -p 5000:5000 -e SECRET_KEY=your-secret-key wardha-court-fetcher
```

#### Option 2: Traditional Server

1. **Install Production WSGI Server**:
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
   ```

3. **Configure Reverse Proxy** (Nginx/Apache):
   ```nginx
   server {
       listen 80;