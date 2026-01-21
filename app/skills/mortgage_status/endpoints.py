"""
Mortgage Status Skill - FastAPI Endpoints

Webhook endpoints for Journey Bank mortgage status demo.
"""

from fastapi import APIRouter
from typing import Dict, Optional
import logging

from app.vapi_utils import extract_vapi_args
from app.skills.mortgage_status.salesforce_client import get_salesforce_client
from app.skills.mortgage_status.email_client import get_email_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mortgage_status"])

# In-memory session storage for demo (stores verification state per call)
# In production, this would be in Redis or database
_session_state: Dict[str, Dict] = {}


def get_session_state(vapi_call_id: str) -> Dict:
    """Get or create session state for a call"""
    if vapi_call_id not in _session_state:
        _session_state[vapi_call_id] = {
            "broker_verified": False,
            "broker_name": None,
            "broker_email": None,
            "current_application": None,
            "verification_attempts": 0
        }
    return _session_state[vapi_call_id]


@router.post("/api/v1/skills/mortgage-status/verify-broker-code")
async def verify_broker_code(request: dict):
    """
    Verify the broker's authentication code (PIN).

    This is the first security step after initial phone authentication.
    Demonstrates bank-grade security for the demo.
    """
    try:
        tool_call_id, args = extract_vapi_args(request)

        # Extract call ID
        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = args.get("vapi_call_id", tool_call_id)

        broker_code = args.get("broker_code", "").strip()

        logger.info(f"Verifying broker code. Call: {vapi_call_id}, Code: {'*' * len(broker_code)}")

        # Get session state
        session = get_session_state(vapi_call_id)
        session["verification_attempts"] += 1

        # Check max attempts
        if session["verification_attempts"] > 3:
            logger.warning(f"Max verification attempts exceeded for call {vapi_call_id}")
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "verified": False,
                        "locked": True,
                        "message": "Too many incorrect attempts. For security, please hang up and call back to try again."
                    }
                }]
            }

        # Verify with Salesforce client (uses mock in demo)
        sf_client = get_salesforce_client()
        result = sf_client.verify_broker_code(broker_code)

        if result["verified"]:
            # Store in session
            session["broker_verified"] = True
            session["broker_name"] = result.get("broker_name")
            session["broker_email"] = result.get("broker_email")

            logger.info(f"Broker verified successfully: {session['broker_name']}")

            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "verified": True,
                        "broker_name": session["broker_name"],
                        "message": "Authentication code verified. How can I help you today?"
                    }
                }]
            }
        else:
            attempts_remaining = 3 - session["verification_attempts"]
            logger.warning(f"Invalid broker code. Attempts remaining: {attempts_remaining}")

            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "verified": False,
                        "attempts_remaining": attempts_remaining,
                        "message": f"That code wasn't correct. You have {attempts_remaining} more attempt{'s' if attempts_remaining > 1 else ''}. Please try again."
                    }
                }]
            }

    except Exception as e:
        logger.error(f"Error in verify_broker_code: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "verified": False,
                    "error": str(e),
                    "message": "I had trouble verifying your code. Please try again."
                }
            }]
        }


@router.post("/api/v1/skills/mortgage-status/lookup-application")
async def lookup_application(request: dict):
    """
    Find a mortgage application by surname and street address.
    """
    try:
        tool_call_id, args = extract_vapi_args(request)

        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = args.get("vapi_call_id", tool_call_id)

        applicant_surname = args.get("applicant_surname", "").strip()
        street_address = args.get("street_address", "").strip()

        logger.info(f"Looking up application. Call: {vapi_call_id}, Surname: {applicant_surname}, Street: {street_address}")

        # Check broker is verified
        session = get_session_state(vapi_call_id)
        if not session.get("broker_verified"):
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "found": False,
                        "error": "not_verified",
                        "message": "I need to verify your authentication code first. Could you please provide your Broker Authentication Code?"
                    }
                }]
            }

        # Search for application
        sf_client = get_salesforce_client()
        application = sf_client.find_application(applicant_surname, street_address)

        if application:
            # Store in session for subsequent calls
            session["current_application"] = application

            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "found": True,
                        "application_id": application["id"],
                        "applicant_name": application["applicant_full_name"],
                        "property_address": application["property_address"],
                        "loan_amount": application["loan_amount_formatted"],
                        "message": f"I found the application for {application['applicant_full_name']} at {application['property_address']}. Is this the one you're looking for?"
                    }
                }]
            }
        else:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "found": False,
                        "message": f"I couldn't find an application for {applicant_surname} at {street_address}. Could you double-check the surname and street address?"
                    }
                }]
            }

    except Exception as e:
        logger.error(f"Error in lookup_application: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "found": False,
                    "error": str(e),
                    "message": "I had trouble searching for that application. Please try again."
                }
            }]
        }


@router.post("/api/v1/skills/mortgage-status/get-status")
async def get_application_status(request: dict):
    """
    Get detailed status and any issues for a mortgage application.
    """
    try:
        tool_call_id, args = extract_vapi_args(request)

        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = args.get("vapi_call_id", tool_call_id)

        application_id = args.get("application_id", "").strip()

        logger.info(f"Getting application status. Call: {vapi_call_id}, App: {application_id}")

        # Get session
        session = get_session_state(vapi_call_id)
        if not session.get("broker_verified"):
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "error": "not_verified",
                        "message": "I need to verify your authentication code first."
                    }
                }]
            }

        # Get status from Salesforce
        sf_client = get_salesforce_client()
        status = sf_client.get_application_status(application_id)

        if status:
            # Update session with current application details
            session["current_application"] = status

            result = {
                "success": True,
                "application_id": status["id"],
                "applicant_name": status["applicant_name"],
                "property_address": status["property_address"],
                "loan_amount": status["loan_amount"],
                "status": status["status"],
                "stage": status["stage"],
                "has_issue": status["has_issue"],
                "last_updated": status["last_updated"]
            }

            # Add issue details if present
            if status["has_issue"]:
                result["issue"] = status["issue"]
                result["resolution"] = status["resolution"]
                result["expected_resolution_time"] = status["expected_resolution_time"]
                result["message"] = f"The application is currently {status['status']} at the {status['stage']} stage. {status['issue']}"
            else:
                result["expected_resolution_time"] = status["expected_resolution_time"]
                result["message"] = f"The application is {status['status']} at the {status['stage']} stage. {status['expected_resolution_time']}"

            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": result
                }]
            }
        else:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "message": "I couldn't retrieve the status for that application. Let me try looking it up again."
                    }
                }]
            }

    except Exception as e:
        logger.error(f"Error in get_application_status: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "success": False,
                    "error": str(e),
                    "message": "I had trouble getting the application status. Please try again."
                }
            }]
        }


@router.post("/api/v1/skills/mortgage-status/send-email")
async def send_status_email(request: dict):
    """
    Send an email summary of the application status to the broker.
    """
    try:
        tool_call_id, args = extract_vapi_args(request)

        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = args.get("vapi_call_id", tool_call_id)

        application_id = args.get("application_id", "").strip()
        confirmed_email = args.get("confirmed_email", "").strip()

        logger.info(f"Sending status email. Call: {vapi_call_id}, App: {application_id}, Email: {confirmed_email}")

        # Get session
        session = get_session_state(vapi_call_id)
        if not session.get("broker_verified"):
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "error": "not_verified",
                        "message": "I need to verify your authentication code first."
                    }
                }]
            }

        # Get application details
        sf_client = get_salesforce_client()
        app_status = session.get("current_application") or sf_client.get_application_status(application_id)

        if not app_status:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "message": "I couldn't find the application details to include in the email."
                    }
                }]
            }

        # Get broker info
        broker_name = session.get("broker_name") or sf_client.get_broker_info().get("name", "Broker")

        # Send email
        email_client = get_email_client()
        result = await email_client.send_status_email(
            to_email=confirmed_email,
            broker_name=broker_name,
            applicant_name=app_status["applicant_name"],
            property_address=app_status["property_address"],
            loan_amount=app_status["loan_amount"],
            status=app_status["status"],
            stage=app_status["stage"],
            has_issue=app_status["has_issue"],
            issue=app_status.get("issue"),
            resolution=app_status.get("resolution"),
            expected_resolution_time=app_status.get("expected_resolution_time")
        )

        if result["success"]:
            logger.info(f"Email sent successfully to {confirmed_email}")
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": True,
                        "email_sent_to": confirmed_email,
                        "message": f"I've sent the email to {confirmed_email} with all the application details."
                    }
                }]
            }
        else:
            logger.error(f"Failed to send email: {result.get('error')}")
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "error": result.get("error"),
                        "message": "I had trouble sending the email. Would you like me to try again?"
                    }
                }]
            }

    except Exception as e:
        logger.error(f"Error in send_status_email: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "success": False,
                    "error": str(e),
                    "message": "I had trouble sending the email. Please try again."
                }
            }]
        }


@router.post("/api/v1/skills/mortgage-status/get-broker-email")
async def get_broker_email(request: dict):
    """
    Get the broker's email address on file (for confirmation).
    """
    try:
        tool_call_id, args = extract_vapi_args(request)

        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = args.get("vapi_call_id", tool_call_id)

        logger.info(f"Getting broker email. Call: {vapi_call_id}")

        # Get session
        session = get_session_state(vapi_call_id)

        # Get email from session or Salesforce
        broker_email = session.get("broker_email")
        if not broker_email:
            sf_client = get_salesforce_client()
            broker_email = sf_client.get_broker_email()

        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "success": True,
                    "broker_email": broker_email,
                    "message": f"I have your email address as {broker_email}."
                }
            }]
        }

    except Exception as e:
        logger.error(f"Error in get_broker_email: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "success": False,
                    "error": str(e),
                    "message": "I couldn't retrieve your email address."
                }
            }]
        }
