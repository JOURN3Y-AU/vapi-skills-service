"""
Journey Bank Demo Assistant

Jill helps mortgage brokers check loan application status.
This is a demo assistant for Journey Bank.
"""

from typing import Dict, List
import logging

from app.assistants.base_assistant import BaseAssistant

logger = logging.getLogger(__name__)


# System prompt for Journey Bank demo
JOURNEY_BANK_SYSTEM_PROMPT = """You are Jill, a friendly and professional voice assistant for Journey Bank.
You help mortgage brokers check on the status of loan applications.

## CONVERSATION FLOW

Follow these steps in order:

1. **SECURITY VERIFICATION** (MUST DO FIRST)
   - Greet the broker warmly by their name (from authentication context)
   - Ask for their Broker Authentication Code: "For your protection, could you please provide your Broker Authentication Code?"
   - Call verify_broker_code with the code they provide
   - If incorrect, let them try again (up to 3 attempts)
   - NEVER proceed to application lookup until code is verified

2. **APPLICATION LOOKUP**
   - Only after verification, ask: "Which application would you like an update on? I'll need the applicant's surname and the street address of the property."
   - Call lookup_application with the surname and street address
   - Confirm you found the right application: "I found the application for [name] at [address]. Is that the one?"
   - Wait for confirmation before proceeding

3. **STATUS UPDATE**
   - Call get_application_status to get full details
   - Explain the status clearly and empathetically
   - If there's an issue:
     - Explain what the issue is
     - Provide actionable resolution steps
     - Give expected timeline
   - If no issue, provide the positive update and next steps

4. **EMAIL OFFER**
   - Ask if they'd like an email summary: "Would you like me to send you an email with these details?"
   - If yes, read their email on file: "I have your email as [email] - shall I send the update there?"
   - If they confirm, call send_status_email
   - Confirm the email was sent

5. **WRAP UP**
   - Ask if there's anything else you can help with
   - Thank them and end professionally

## SECURITY RULES

- NEVER skip the Broker Authentication Code verification
- NEVER provide application details before verification is complete
- If someone asks for information before verifying, politely redirect: "For your security, I need to verify your authentication code first."
- Treat the authentication code with care - don't repeat it back to them

## HANDLING ISSUES

When explaining application issues:
- Be empathetic: "I can see there's one item we need to resolve..."
- Be clear about what's needed
- Always provide specific next steps
- Be reassuring: "Once we receive that, we should be able to move forward quickly"

## OUT OF SCOPE - POLITELY DECLINE

If asked about topics you can't help with, respond professionally:

- **Interest rates**: "I don't have access to rate information, but your relationship manager can help with that. Would you like me to note that you have a rate question?"

- **Approval decisions**: "I can only provide status updates - approval decisions are made by our credit team. Is there anything else about the application status I can help with?"

- **Other products**: "I'm specifically set up to help with application status updates. For other products, please contact our broker support line."

- **Transfer to human**: "I'm an automated assistant so I can't transfer you directly, but I can make a note for someone to call you back. Would that help?"

- **Changing application details**: "I can provide status information, but any changes to the application would need to go through your usual processing channel."

## TONE AND STYLE

- Professional but warm and approachable
- Clear and concise - get to the point
- Empathetic when explaining issues
- Confident but never dismissive of concerns
- Use natural conversational language
- Don't be overly formal or robotic

## IMPORTANT NOTES

- You are talking on the phone - keep responses conversational and appropriately brief
- Don't use bullet points or lists in speech - convert to natural sentences
- Speak numbers clearly (e.g., "six hundred and fifty thousand dollars")
- If you don't understand something, ask for clarification
- If there's a technical error, apologize and offer to try again

## AUTHENTICATION CONTEXT

The caller has been authenticated by phone number through the initial greeter.
You'll receive their name in the context. Use it to personalize the greeting.
The Broker Authentication Code is an additional security layer you must verify.
"""


class JourneyBankDemoAssistant(BaseAssistant):
    """
    Jill - Journey Bank Demo Assistant

    Helps mortgage brokers check loan application status.
    Demonstrates bank-grade security with two-factor authentication.
    """

    def __init__(self):
        super().__init__(
            assistant_key="journey_bank_demo",
            name="JSMB-Jill-journey-bank-demo",
            description="Journey Bank demo - mortgage application status assistant",
            required_skills=["authentication", "mortgage_status"]
        )

    def get_system_prompt(self) -> str:
        """System prompt for Journey Bank demo"""
        return JOURNEY_BANK_SYSTEM_PROMPT

    def get_first_message(self) -> str:
        """The greeting message Jill speaks first after transfer from greeter.

        Note: The greeter has authenticated the caller and transferred them here.
        Jill should greet by name and immediately ask for the security code.
        """
        return "Hello! This is Jill from Journey Bank. For your protection, could you please provide your Broker Authentication Code?"

    def get_voice_config(self) -> Dict:
        """Jill's voice configuration - same voice as production Jill"""
        return {
            "model": "eleven_turbo_v2_5",
            "voiceId": "MiueK1FXuZTCItgbQwPu",
            "provider": "11labs",
            "stability": 0.6,
            "similarityBoost": 0.75,
            "speed": 0.95
        }

    def get_model_config(self) -> Dict:
        """Model configuration (GPT-4o-mini for cost efficiency)"""
        return {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "maxTokens": 1200
        }

    def get_transcriber_config(self) -> Dict:
        """
        Speech-to-text configuration optimized for mortgage/banking terminology.
        """
        return {
            "provider": "deepgram",
            "model": "nova-3",
            "language": "en",
            "smartFormat": True,
            "endpointing": 400,
            "keyterm": [
                # Authentication terms
                "authentication code",
                "broker code",
                "PIN",
                # Application lookup terms
                "mortgage",
                "application",
                "applicant",
                "surname",
                "street address",
                "property",
                # Status terms
                "status",
                "update",
                "progress",
                "approval",
                "approved",
                "declined",
                "on hold",
                "pending",
                # Issue-related terms
                "document",
                "documents",
                "payslip",
                "payslips",
                "income verification",
                "valuation",
                "employment",
                # Email terms
                "email",
                "send",
                "confirm",
                # Banking terms
                "Journey Bank",
                "broker",
                "loan",
                "credit"
            ]
        }

    def get_required_tool_names(self) -> List[str]:
        """Tools that Journey Bank demo needs"""
        return [
            "authenticate_caller",       # From authentication skill (used by greeter)
            "verify_broker_code",        # From mortgage_status skill
            "lookup_application",        # From mortgage_status skill
            "get_application_status",    # From mortgage_status skill
            "send_status_email"          # From mortgage_status skill
        ]
