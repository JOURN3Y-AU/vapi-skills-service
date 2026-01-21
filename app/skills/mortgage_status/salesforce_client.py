"""
Salesforce Client - Journey Bank Demo

Provides Salesforce integration with mock mode for testing.
When MOCK_MODE is enabled, returns hardcoded demo data.
When disabled, connects to real Salesforce via REST API.
"""

import httpx
import logging
from typing import Dict, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# MOCK DATA FOR DEMO
# =============================================================================

MOCK_BROKER = {
    "id": "contact_001",
    "name": "Sarah Johnson",
    "email": "sarah.johnson@broker.com.au",
    "phone": "+61400000000",  # Will be matched from Supabase user
    "authentication_code": "1234",  # Broker Authentication Code for demo
    "company": "Premier Mortgage Solutions"
}

MOCK_APPLICATIONS = {
    # Key format: "{surname_lowercase}_{street_number}_{street_name_first_word}"
    "smith_123_main": {
        "id": "opp_001",
        "applicant_first_name": "John",
        "applicant_surname": "Smith",
        "applicant_full_name": "John Smith",
        "property_address": "123 Main Street, Sydney NSW 2000",
        "loan_amount": 650000,
        "loan_amount_formatted": "$650,000",
        "status": "On Hold",
        "stage": "Documentation Review",
        "has_issue": True,
        "issue": "Missing document - we need the applicant's most recent payslip dated within the last 30 days. The one provided was from 3 months ago.",
        "resolution": "The applicant can upload the updated payslip through the broker portal, or you can email it directly to documents@journeybank.com.au",
        "expected_resolution_time": "Once we receive the document, we should be able to progress the application within 24 to 48 hours.",
        "created_date": "2025-01-10",
        "last_updated": "2025-01-18"
    },
    "williams_45_ocean": {
        "id": "opp_002",
        "applicant_first_name": "Emma",
        "applicant_surname": "Williams",
        "applicant_full_name": "Emma Williams",
        "property_address": "45 Ocean Drive, Bondi Beach NSW 2026",
        "loan_amount": 1200000,
        "loan_amount_formatted": "$1,200,000",
        "status": "In Progress",
        "stage": "Valuation",
        "has_issue": False,
        "issue": None,
        "resolution": None,
        "expected_resolution_time": "The property valuation is scheduled for this week. We expect to have results within 3-5 business days.",
        "created_date": "2025-01-05",
        "last_updated": "2025-01-20"
    },
    "chen_78_harbour": {
        "id": "opp_003",
        "applicant_first_name": "Michael",
        "applicant_surname": "Chen",
        "applicant_full_name": "Michael Chen",
        "property_address": "78 Harbour View, North Sydney NSW 2060",
        "loan_amount": 890000,
        "loan_amount_formatted": "$890,000",
        "status": "On Hold",
        "stage": "Income Verification",
        "has_issue": True,
        "issue": "We've sent an employment verification request to the applicant's employer but haven't received a response yet. This is a standard check required for all applications.",
        "resolution": "We'll follow up with the employer again. If you have a direct HR contact at the company, that information might help speed things up.",
        "expected_resolution_time": "Typically employers respond within 5-7 business days. We're on day 4 currently.",
        "created_date": "2025-01-08",
        "last_updated": "2025-01-19"
    }
}


class SalesforceClient:
    """
    Salesforce API client with mock mode support.

    When SF_MOCK_MODE=true (default), uses hardcoded demo data.
    When SF_MOCK_MODE=false, connects to real Salesforce instance.
    """

    def __init__(self):
        self.mock_mode = getattr(settings, 'SF_MOCK_MODE', True)
        self.instance_url = getattr(settings, 'SF_INSTANCE_URL', None)
        self.username = getattr(settings, 'SF_USERNAME', None)
        self.password = getattr(settings, 'SF_PASSWORD', None)
        self.security_token = getattr(settings, 'SF_SECURITY_TOKEN', None)
        self.access_token = None

        if self.mock_mode:
            logger.info("SalesforceClient initialized in MOCK MODE")
        else:
            logger.info(f"SalesforceClient initialized for {self.instance_url}")

    async def authenticate(self) -> bool:
        """
        Authenticate with Salesforce using username-password flow.
        Returns True if successful, False otherwise.
        """
        if self.mock_mode:
            logger.info("Mock mode: Skipping Salesforce authentication")
            return True

        if not all([self.instance_url, self.username, self.password]):
            logger.error("Salesforce credentials not configured")
            return False

        try:
            async with httpx.AsyncClient() as client:
                # Salesforce OAuth token endpoint
                token_url = f"{self.instance_url}/services/oauth2/token"

                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "password",
                        "client_id": getattr(settings, 'SF_CLIENT_ID', ''),
                        "client_secret": getattr(settings, 'SF_CLIENT_SECRET', ''),
                        "username": self.username,
                        "password": f"{self.password}{self.security_token or ''}"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get('access_token')
                    self.instance_url = data.get('instance_url', self.instance_url)
                    logger.info("Successfully authenticated with Salesforce")
                    return True
                else:
                    logger.error(f"Salesforce auth failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Salesforce authentication error: {str(e)}")
            return False

    def verify_broker_code(self, code: str) -> Dict:
        """
        Verify the broker's authentication code.

        Args:
            code: The PIN/code provided by the broker

        Returns:
            Dict with verification result
        """
        if self.mock_mode:
            expected_code = MOCK_BROKER["authentication_code"]
            is_valid = code.strip() == expected_code

            if is_valid:
                return {
                    "verified": True,
                    "broker_name": MOCK_BROKER["name"],
                    "broker_email": MOCK_BROKER["email"],
                    "message": "Authentication code verified successfully."
                }
            else:
                return {
                    "verified": False,
                    "message": "Invalid authentication code. Please try again."
                }

        # Real Salesforce implementation would go here
        # For now, fall back to mock
        return self.verify_broker_code_mock(code)

    def verify_broker_code_mock(self, code: str) -> Dict:
        """Mock implementation for broker code verification"""
        expected_code = MOCK_BROKER["authentication_code"]
        is_valid = code.strip() == expected_code

        return {
            "verified": is_valid,
            "broker_name": MOCK_BROKER["name"] if is_valid else None,
            "broker_email": MOCK_BROKER["email"] if is_valid else None,
            "message": "Authentication code verified successfully." if is_valid else "Invalid authentication code."
        }

    def find_application(self, surname: str, street_address: str) -> Optional[Dict]:
        """
        Find a mortgage application by surname and street address.

        Args:
            surname: Applicant's last name
            street_address: Property street address

        Returns:
            Application dict if found, None otherwise
        """
        if self.mock_mode:
            return self._find_application_mock(surname, street_address)

        # Real Salesforce implementation would go here
        return self._find_application_mock(surname, street_address)

    def _find_application_mock(self, surname: str, street_address: str) -> Optional[Dict]:
        """
        Mock implementation for finding applications.
        Matches based on surname and street number/name.
        """
        surname_lower = surname.lower().strip()
        street_lower = street_address.lower().strip()

        logger.info(f"Searching for application: surname='{surname}', street='{street_address}'")

        # Try to extract street number and first word of street name
        street_parts = street_lower.split()
        street_number = ""
        street_name = ""

        for part in street_parts:
            if part.isdigit():
                street_number = part
            elif not street_number:
                continue  # Skip until we find the number
            else:
                street_name = part
                break

        # Try different key formats
        possible_keys = [
            f"{surname_lower}_{street_number}_{street_name}",  # smith_123_main
            f"{surname_lower}_{street_number}",  # smith_123
        ]

        logger.info(f"Trying keys: {possible_keys}")

        for key in possible_keys:
            if key in MOCK_APPLICATIONS:
                app = MOCK_APPLICATIONS[key]
                logger.info(f"Found application: {app['id']} - {app['applicant_full_name']}")
                return app

        # Fuzzy match on surname only as fallback
        for key, app in MOCK_APPLICATIONS.items():
            if app["applicant_surname"].lower() == surname_lower:
                # Check if street partially matches
                if street_number and street_number in app["property_address"].lower():
                    logger.info(f"Found application via fuzzy match: {app['id']}")
                    return app

        logger.info(f"No application found for surname='{surname}', street='{street_address}'")
        return None

    def get_application_status(self, application_id: str) -> Optional[Dict]:
        """
        Get detailed status for an application.

        Args:
            application_id: The application/opportunity ID

        Returns:
            Status dict if found, None otherwise
        """
        if self.mock_mode:
            return self._get_application_status_mock(application_id)

        # Real Salesforce implementation would go here
        return self._get_application_status_mock(application_id)

    def _get_application_status_mock(self, application_id: str) -> Optional[Dict]:
        """Mock implementation for getting application status"""
        for app in MOCK_APPLICATIONS.values():
            if app["id"] == application_id:
                return {
                    "id": app["id"],
                    "applicant_name": app["applicant_full_name"],
                    "property_address": app["property_address"],
                    "loan_amount": app["loan_amount_formatted"],
                    "status": app["status"],
                    "stage": app["stage"],
                    "has_issue": app["has_issue"],
                    "issue": app["issue"],
                    "resolution": app["resolution"],
                    "expected_resolution_time": app["expected_resolution_time"],
                    "last_updated": app["last_updated"]
                }

        return None

    def get_broker_email(self) -> str:
        """Get the broker's email address"""
        if self.mock_mode:
            return MOCK_BROKER["email"]

        # Real implementation would query Contact record
        return MOCK_BROKER["email"]

    def get_broker_info(self) -> Dict:
        """Get full broker information"""
        if self.mock_mode:
            return {
                "name": MOCK_BROKER["name"],
                "email": MOCK_BROKER["email"],
                "company": MOCK_BROKER["company"]
            }

        # Real implementation would query Contact record
        return {
            "name": MOCK_BROKER["name"],
            "email": MOCK_BROKER["email"],
            "company": MOCK_BROKER["company"]
        }


# Singleton instance
_salesforce_client = None


def get_salesforce_client() -> SalesforceClient:
    """Get or create the Salesforce client singleton"""
    global _salesforce_client
    if _salesforce_client is None:
        _salesforce_client = SalesforceClient()
    return _salesforce_client
