---
description: Repository Information Overview
alwaysApply: true
---

# Veterinary Clinic Scraper API Information

## Summary
A FastAPI-based web scraping service that extracts structured data from veterinary clinic websites using Crawl4AI for web crawling and Google Gemini AI for intelligent data extraction. The application provides RESTful API endpoints to crawl websites with configurable depth and page limits, returning structured clinic information including contact details, business hours, and services.

## Structure
- **main.py**: Application entry point with FastAPI configuration, CORS middleware, and async event loop setup for Windows compatibility
- **routes/**: API route handlers
  - `scraper.py`: Web scraping endpoints with URL validation and data extraction logic
  - `hello.py`: Health check endpoint
- **helpers/**: Core utility modules
  - `scraperHelper.py`: Crawl4AI integration for deep website crawling
  - `geminiHelper.py`: Google Gemini AI client for structured data extraction
  - `envHelper.py`: Pydantic-based environment configuration management
  - `loggerHelper.py`: Centralized logging configuration
- **venv/**: Python virtual environment (git-ignored)

## Language & Runtime
**Language**: Python  
**Version**: 3.13.7  
**Framework**: FastAPI >=0.118.3  
**Package Manager**: pip  
**ASGI Server**: Uvicorn >=0.37.0

## Dependencies
**Main Dependencies**:
- `fastapi>=0.118.3` - Modern web framework for building APIs
- `uvicorn[standard]>=0.37.0` - ASGI server with standard extras
- `crawl4ai>=0.4.0` - Async web crawler with Playwright integration
- `google-genai>=0.2.0` - Google Gemini AI SDK for data extraction
- `pydantic>=2.0.0` - Data validation and settings management
- `pydantic-settings>=2.0.0` - Environment variable configuration
- `python-dotenv>=1.1.1` - .env file loading

## Build & Installation
```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY

# Run the server
python main.py
```

**Server Configuration** (via .env):
- `HOST`: Server bind address (default: 0.0.0.0)
- `PORT`: Server port (default: 8080)
- `GEMINI_API_KEY`: Google Gemini API key (required)

**Special Notes**:
- Windows compatibility: Uses `WindowsProactorEventLoopPolicy` for asyncio/Playwright support
- Configuration is type-validated at startup using Pydantic BaseSettings
- Automatic .env file loading with case-insensitive environment variable matching

## API Endpoints
**Health Check**:
- `GET /` - Basic health check endpoint

**Scraper**:
- `POST /v1/scraper/crawl` - Crawl website and extract clinic data
  - Parameters: `url` (required), `max_depth` (1-10, default: 1), `max_pages` (1-200, default: 10)
  - Returns structured clinic data: name, phone, address, email, business hours, services

**Hello**:
- `GET /v1/hello` - Simple hello endpoint for testing
