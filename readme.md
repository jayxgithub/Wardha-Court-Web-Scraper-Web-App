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
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

#### Option 3: Cloud Platforms

**Heroku Deployment**:
```bash
# Install Heroku CLI and login
heroku create wardha-court-fetcher
git push heroku main
heroku config:set SECRET_KEY=your-secret-key
```

**Railway/Render Deployment**:
- Connect GitHub repository
- Set environment variables
- Deploy automatically

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Flask secret key for sessions | - | Yes |
| `DEBUG` | Enable debug mode | `False` | No |
| `PORT` | Application port | `5000` | No |
| `DATABASE_URL` | Database connection string | SQLite local | No |
| `COURT_BASE_URL` | Wardha court website URL | Auto-detected | No |
| `REQUEST_TIMEOUT` | HTTP request timeout (seconds) | `30` | No |
| `MAX_RETRIES` | Maximum retry attempts | `3` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Customization Options

1. **Case Types**: Modify case types in `get_case_types()` function
2. **Court URLs**: Update search URLs in scraper configuration
3. **Styling**: Customize CSS in `static/style.css`
4. **Database**: Switch to PostgreSQL by updating `DATABASE_URL`

## 📈 Monitoring & Analytics

### Built-in Dashboard
- Access at `/dashboard`
- Query statistics and trends
- System health monitoring
- Popular case types analysis

### Logging
- Application logs stored in `app.log`
- Database query logging
- Error tracking and debugging
- Performance monitoring

### Health Checks
- Endpoint: `/health`
- Court website connectivity status
- Database connection status
- System resource usage

## 🔒 Security Considerations

### Data Protection
- No sensitive personal data stored permanently
- Query logging for system monitoring only
- Secure session management
- Input validation and sanitization

### Rate Limiting
- Built-in request delays to respect court website
- Retry logic with exponential backoff
- Connection pooling for efficiency

### Legal Compliance
- Only accesses publicly available information
- Respects court website terms of service
- No automated bulk scraping
- Educational and reference purposes only

## 🐛 Troubleshooting

### Common Issues

#### Court Website Not Accessible
```
Error: Wardha District Court website is currently not accessible
```
**Solution**: 
1. Check internet connection
2. Verify court website is online
3. Use "Test Connection" feature
4. System will fall back to demo data

#### Case Not Found
```
Error: Case [Type] [Number]/[Year] not found
```
**Solution**:
1. Verify case details (type, number, year)
2. Check if case exists in court database
3. Try different case type variations
4. Contact court directly for verification

#### PDF Download Failed
```
Error: Failed to download PDF
```
**Solution**:
1. Check if PDF link is valid
2. Verify court website accessibility
3. Try downloading directly from court website
4. Contact court for physical copies

#### Database Errors
```
Error: Unable to log query
```
**Solution**:
1. Check database file permissions
2. Ensure sufficient disk space
3. Restart application
4. Check database integrity

### Debug Mode

Enable debug mode for detailed error information:

```bash
export FLASK_DEBUG=True
export FLASK_ENV=development
python app.py
```

## 📚 Additional Resources

### Official Documentation
- [Wardha District Court Website](https://wardha.dcourts.gov.in/)
- [eCourts Portal](https://ecourts.gov.in/)
- [National Judicial Data Grid](https://njdg.ecourts.gov.in/)

### Related Projects
- [eCourts Services](https://services.ecourts.gov.in/)
- [District Courts Portal](https://districts.ecourts.gov.in/)

### Legal Disclaimer
This application is an **unofficial** tool created for educational and reference purposes. It is not affiliated with, endorsed by, or connected to Wardha District Court or the Government of Maharashtra. 

**Important Notes**:
- Always verify information with official court sources
- This tool should not be used as the sole basis for legal decisions
- Case information may not be real-time or complete
- For official documentation, contact the court directly

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test thoroughly
4. Commit changes: `git commit -m "Add feature"`
5. Push to branch: `git push origin feature-name`
6. Create a Pull Request

### Contribution Guidelines

- Follow PEP 8 Python coding standards
- Add unit tests for new features
- Update documentation for changes
- Test across different case types
- Ensure mobile responsiveness

### Areas for Contribution

- Additional court integrations
- Improved CAPTCHA handling
- Enhanced data parsing
- Mobile app development
- Performance optimizations
- Accessibility improvements

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Wardha District Court Case Search System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📞 Support & Contact

### Issues and Bugs
- Report issues on GitHub Issues page
- Provide detailed error messages and steps to reproduce
- Include system information and browser details

### Feature Requests
- Submit feature requests via GitHub Issues
- Describe the use case and expected behavior
- Consider contributing the feature yourself

### General Questions
- Check existing documentation first
- Search closed issues for similar questions
- Create new issue with "question" label

---

## 🎯 Demo Video Script

### Recording Guidelines (≤ 5 minutes)

**Scene 1: Introduction (30 seconds)**
```
"Welcome to the Wardha District Court Case Search System. 
This application allows you to search and retrieve case information 
from the District and Sessions Court in Wardha, Maharashtra."
```

**Scene 2: Basic Search (90 seconds)**
```
"Let me demonstrate a basic case search:
1. Select case type - I'll choose 'Civil Suit'
2. Enter case number - let's use '123'  
3. Enter filing year - 2024
4. Click 'Search Case'

The system now connects to the court website and retrieves the case information."
```

**Scene 3: Results Display (60 seconds)**
```
"Here we can see the case details including:
- Case title and court information
- Party details (petitioner and respondent)
- Important dates like filing date and next hearing
- Case status and current stage
- Available orders and judgments"
```

**Scene 4: Advanced Features (60 seconds)**
```
"The system includes several advanced features:
- Connection testing to verify court website accessibility
- PDF download functionality for court documents
- Print-friendly case details
- Analytics dashboard showing usage statistics"
```

**Scene 5: Error Handling (30 seconds)**
```
"When the court website is unavailable, the system gracefully
falls back to demo data and clearly indicates this to users,
ensuring continuity of service."
```

**Scene 6: Conclusion (30 seconds)**
```
"This system demonstrates robust web scraping, user-friendly design,
and comprehensive error handling for accessing public court records
from Wardha District Court."
```

---

**Built with ❤️ for the legal community and citizens of Wardha District, Maharashtra**

*For educational and reference purposes only. Always verify with official court sources.*