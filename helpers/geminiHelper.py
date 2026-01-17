"""
Gemini Helper - Integration with Google Gemini API for data extraction
"""

from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel
from helpers.envHelper import settings
from helpers.loggerHelper import get_logger

logger = get_logger(__name__)


GEMINI_MODEL = "gemini-2.5-flash"


# Pydantic models for response schema - Frontend compatible
class Professional(BaseModel):
    """Professional or key team member information"""

    name: str
    role: str
    is_available: bool = True


class BusinessHours(BaseModel):
    """Business hours for each day of the week - simple string format"""

    monday: str = ""
    tuesday: str = ""
    wednesday: str = ""
    thursday: str = ""
    friday: str = ""
    saturday: str = ""
    sunday: str = ""


class BusinessData(BaseModel):
    """Extracted business data - generalized structure"""

    name: str = ""
    phoneNumber: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pincode: str = ""
    website: str = ""
    email: str = ""
    businessHours: BusinessHours = BusinessHours()
    is_24_7: bool = False
    holidayClosures: str = ""
    professionals: List[Professional] = []
    manager: str = ""
    operationsLead: str = ""
    servicesOffered: List[str] = []
    servicesNotOffered: str = ""
    specialties: List[str] = []


def get_gemini_client() -> genai.Client:
    """
    Get initialized Gemini client

    Returns:
        Configured Gemini client

    Raises:
        ValueError: If GEMINI_API_KEY is not set
    """
    api_key = settings.gemini_api_key
    if not api_key:
        raise ValueError(
            "Gemini API key is required. Set GEMINI_API_KEY environment variable."
        )
    return genai.Client(api_key=api_key)


async def extract_business_data(
    pages_data: List[Dict[str, str]], client: Optional[genai.Client] = None
) -> BusinessData:
    """
    Extract structured business data from crawled pages using Gemini.

    Args:
        pages_data: List of dicts with 'url' and 'content' keys
        client: Optional pre-initialized Gemini client

    Returns:
        BusinessData model with extracted business information
    """
    if client is None:
        client = get_gemini_client()

    # Prepare content for Gemini
    combined_content = _prepare_content_for_extraction(pages_data)

    # Create extraction prompt
    prompt = _build_extraction_prompt()

    try:
        # Call Gemini API with response schema (asynchronously)
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"{prompt}\n\n{combined_content}",
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=BusinessData,  # Use Pydantic model for response schema
                thinking_config=types.ThinkingConfig(
                    thinking_budget=0
                ),  # Disable thinking
            ),
        )

        # Use parsed response - Gemini automatically validates against schema
        extracted_data: BusinessData = response.parsed
        return extracted_data

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        # Return empty BusinessData model on error
        return BusinessData()


def _prepare_content_for_extraction(pages_data: List[Dict[str, str]]) -> str:
    """
    Prepare crawled page content for extraction.

    Args:
        pages_data: List of dicts with 'url' and 'content' keys

    Returns:
        Combined formatted content string
    """
    # Limit content to avoid token limits (roughly 800k characters for Gemini 2.0)
    max_chars_per_page = 50000
    max_total_chars = 500000

    formatted_pages = []
    total_chars = 0

    for page in pages_data:
        url = page.get("url", "Unknown URL")
        content = page.get("content", "")

        # Skip empty pages
        if not content.strip():
            continue

        # Truncate very long pages
        if len(content) > max_chars_per_page:
            content = content[:max_chars_per_page] + "\n...[content truncated]"

        page_text = f"--- PAGE: {url} ---\n{content}\n\n"

        # Check if adding this page would exceed total limit
        if total_chars + len(page_text) > max_total_chars:
            break

        formatted_pages.append(page_text)
        total_chars += len(page_text)

    return "".join(formatted_pages)


def _build_extraction_prompt() -> str:
    """
    Build the extraction prompt for Gemini.

    Returns:
        Structured prompt string
    """
    return """You are a data extraction specialist. Extract structured information about a business from the provided website content.

Extract all available information about the business. The data will be validated against a strict schema and sent directly to a frontend form.

IMPORTANT: Return data in this exact structure - it will populate a form with ZERO transformation.

INSTRUCTIONS:
1. name: Extract the full business name (string)
   - If none found, return empty string ""

2. phoneNumbers: Extract ALL phone numbers as a comma-separated string
   - Format: "(555) 123-4567, (555) 123-4568" or "(555) 123-4567"
   - If multiple numbers, separate with comma and space
   - If none found, return empty string ""

3. address: Extract the primary street address only (string)
   - Format: "123 Oak Street" (street number and name only)
   - If none found, return empty string ""

4. city: Extract the city name (string)
   - If none found, return empty string ""

5. state: Extract the state name or abbreviation (string)
   - If none found, return empty string ""

6. pincode: Extract the ZIP/postal code (string)
   - If none found, return empty string ""

7. website: Extract the business's website URL (string)
   - If none found, return empty string ""

8. email: Extract the primary email address (string)
   - If none found, return empty string ""

9. businessHours: Extract business hours as a simple object with day keys
   - Format: Simple strings like "8:00 AM - 6:00 PM", "Closed", or "24/7"
   - Structure:
     {
       "monday": "8:00 AM - 6:00 PM",
       "tuesday": "8:00 AM - 6:00 PM",
       "wednesday": "8:00 AM - 6:00 PM",
       "thursday": "8:00 AM - 6:00 PM",
       "friday": "8:00 AM - 6:00 PM",
       "saturday": "9:00 AM - 2:00 PM",
       "sunday": "Closed"
     }
   - If hours not found for a day, use empty string ""
   - If business is 24/7, still populate hours (frontend will handle is_24_7 flag)

10. is_24_7: Set to true if business operates 24/7, otherwise false (boolean)
    - Default: false

11. holidayClosures: Extract information about holiday closures (string)
    - Format: "Closed for Thanksgiving. Limited hours on Christmas Eve."
    - If none found, return empty string ""

12. professionals: Extract key team members or professionals as an array of objects
    - Structure: {"name": "Full Name", "role": "Title/Role", "is_available": true/false}
    - is_available defaults to true if not specified
    - If none found, return empty array []

13. manager: Extract the manager or business owner's name (string)
    - If none found, return empty string ""

14. operationsLead: Extract the operations lead or technical head's name (string)
    - If none found, return empty string ""

15. servicesOffered: Extract ALL services offered as an array of strings
      - IMPORTANT: Map extracted services to the following STANDARD LIST if possible.
    - If a service on the website matches a standard service (even if named slightly differently), use the STANDARD NAME.
    - If it does not match any, use the name found on the website.
    - STANDARD SERVICE LIST:
      [
        "Wellness & Preventive Exams",
        "Puppy & Kitten Care Programs",
        "Vaccinations & Titers",
        "Flea, Tick & Heartworm Prevention",
        "Microchipping",
        "Senior Pet Wellness",
        "Nutrition & Diet Counseling",
        "Sick Pet Examinations",
        "Pain Management",
        "Internal Medicine Consults",
        "Anal Gland Expression",
        "In-House Laboratory",
        "Radiology (X-rays)",
        "Ultrasound",
        "Allergy Testing",
        "Cytology (Ear, Skin)",
        "Urinalysis/Fecal Exam",
        "Cardiac & Respiratory Diagnostics",
        "Spay/Neuter Surgery",
        "Soft Tissue Surgery",
        "Orthopedic Surgery",
        "Dental Cleaning & Extractions",
        "Dermatology",
        "Ophthalmology",
        "Oncology",
        "Behavioral Counseling",
        "Urgent Care Appointments",
        "Emergency Stabilization",
        "IV Fluid Therapy",
        "Post-Surgical Recovery Monitoring",
        "Isolation & Infectious Disease Care",
        "Quality of Life/Euthanasia Consult",
        "Hospice & Palliative Care",
        "Humane Euthanasia Services",
        "Laser Therapy",
        "Acupuncture",
        "Physical Therapy / Rehabilitation",
        "Homeopathy",
        "Medication Refill Pick-up",
        "Prescription Diet Pick-up"
      ]
    - Format: ["Standard Name 1", "Standard Name 2", "Other Found Name"]
    - If none found, return empty array []

16. servicesNotOffered: Extract services explicitly NOT offered (string)
    - Format: "Boarding, Grooming, Delivery"
    - Comma-separated if multiple
    - If none found, return empty string ""

17. specialties: Extract business specialties, categories, or focus areas as an array of strings
    - Format: ["Category 1", "Category 2"]
    - If none found, return empty array []

EMPTY VALUES STRATEGY:
- Arrays: Use empty array [] if no data found
- Strings: Use empty string "" if no data found
- Booleans: Use false as default (except for professionals.is_available which defaults to true)
- businessHours object: Return full structure with empty strings for each day if no data found

Only include information explicitly stated on the website.
Be thorough and accurate.

Website content:"""
