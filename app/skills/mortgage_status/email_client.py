"""
Email Client - Journey Bank Demo

Sends branded email summaries via Resend API.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if resend is available
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend package not installed. Email functionality will be mocked.")


def get_html_template(
    broker_name: str,
    applicant_name: str,
    property_address: str,
    loan_amount: str,
    status: str,
    stage: str,
    has_issue: bool,
    issue: Optional[str],
    resolution: Optional[str],
    expected_resolution_time: Optional[str]
) -> str:
    """
    Generate branded HTML email template for Journey Bank.

    Args:
        broker_name: The broker's name
        applicant_name: The applicant's full name
        property_address: The property address
        loan_amount: Formatted loan amount
        status: Current status (e.g., "On Hold", "In Progress")
        stage: Current stage (e.g., "Documentation Review")
        has_issue: Whether there's an issue with the application
        issue: Description of the issue (if any)
        resolution: How to resolve the issue (if any)
        expected_resolution_time: Expected time to resolve (if any)

    Returns:
        HTML string for the email body
    """
    # Status color coding
    status_colors = {
        "On Hold": "#F59E0B",  # Amber
        "In Progress": "#3B82F6",  # Blue
        "Approved": "#10B981",  # Green
        "Declined": "#EF4444",  # Red
    }
    status_color = status_colors.get(status, "#6B7280")  # Gray default

    # Issue section HTML (only shown if has_issue)
    issue_section = ""
    if has_issue and issue:
        issue_section = f"""
        <div style="background-color: #FEF3C7; border-left: 4px solid #F59E0B; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <h3 style="color: #92400E; margin: 0 0 8px 0; font-size: 16px;">Action Required</h3>
            <p style="color: #78350F; margin: 0 0 12px 0;">{issue}</p>
            {f'<p style="color: #78350F; margin: 0;"><strong>How to resolve:</strong> {resolution}</p>' if resolution else ''}
        </div>
        """

    # Expected resolution time (if provided)
    timeline_section = ""
    if expected_resolution_time:
        timeline_section = f"""
        <div style="background-color: #EFF6FF; border-left: 4px solid #3B82F6; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="color: #1E40AF; margin: 0;"><strong>Expected Timeline:</strong> {expected_resolution_time}</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1F2937; margin: 0; padding: 0; background-color: #F3F4F6;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #1E3A5F 0%, #2D5A87 100%); padding: 32px 24px; text-align: center;">
                <h1 style="color: #FFFFFF; margin: 0; font-size: 28px; font-weight: 600;">Journey Bank</h1>
                <p style="color: #93C5FD; margin: 8px 0 0 0; font-size: 14px;">Mortgage Application Status Update</p>
            </div>

            <!-- Main Content -->
            <div style="padding: 32px 24px;">
                <p style="margin: 0 0 24px 0;">Hi {broker_name},</p>

                <p style="margin: 0 0 24px 0;">Here's the status update for the mortgage application you enquired about:</p>

                <!-- Application Summary Box -->
                <div style="background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 8px; padding: 20px; margin: 0 0 24px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Applicant</td>
                            <td style="padding: 8px 0; text-align: right; font-weight: 500;">{applicant_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Property</td>
                            <td style="padding: 8px 0; text-align: right; font-weight: 500;">{property_address}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Loan Amount</td>
                            <td style="padding: 8px 0; text-align: right; font-weight: 500;">{loan_amount}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Current Stage</td>
                            <td style="padding: 8px 0; text-align: right; font-weight: 500;">{stage}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #6B7280; font-size: 14px;">Status</td>
                            <td style="padding: 8px 0; text-align: right;">
                                <span style="background-color: {status_color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500;">{status}</span>
                            </td>
                        </tr>
                    </table>
                </div>

                {issue_section}
                {timeline_section}

                <p style="margin: 24px 0 0 0; color: #6B7280; font-size: 14px;">If you have any questions, please don't hesitate to contact our broker support team.</p>
            </div>

            <!-- Footer -->
            <div style="background-color: #F9FAFB; padding: 24px; text-align: center; border-top: 1px solid #E5E7EB;">
                <p style="margin: 0 0 8px 0; color: #6B7280; font-size: 14px;">Journey Bank - Broker Support</p>
                <p style="margin: 0 0 8px 0; color: #9CA3AF; font-size: 12px;">
                    <a href="mailto:broker.support@journeybank.com.au" style="color: #3B82F6; text-decoration: none;">broker.support@journeybank.com.au</a>
                    &nbsp;|&nbsp;
                    1800 JOURNEY
                </p>
                <p style="margin: 16px 0 0 0; color: #9CA3AF; font-size: 11px;">
                    This email was sent via our automated assistant, Jill.<br>
                    Generated on {datetime.now().strftime('%d %B %Y at %I:%M %p')}
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


class EmailClient:
    """
    Email client for sending status updates via Resend.

    Supports mock mode when Resend is not configured.
    """

    def __init__(self):
        from app.config import settings

        self.api_key = getattr(settings, 'RESEND_API_KEY', None)
        self.from_email = getattr(settings, 'RESEND_FROM_EMAIL', 'noreply@journeybank.com.au')

        if self.api_key and RESEND_AVAILABLE:
            resend.api_key = self.api_key
            self.mock_mode = False
            logger.info("EmailClient initialized with Resend API")
        else:
            self.mock_mode = True
            logger.info("EmailClient initialized in MOCK MODE (no Resend API key or package)")

    async def send_status_email(
        self,
        to_email: str,
        broker_name: str,
        applicant_name: str,
        property_address: str,
        loan_amount: str,
        status: str,
        stage: str,
        has_issue: bool,
        issue: Optional[str] = None,
        resolution: Optional[str] = None,
        expected_resolution_time: Optional[str] = None
    ) -> Dict:
        """
        Send application status email to the broker.

        Args:
            to_email: Recipient email address
            broker_name: Broker's name
            applicant_name: Applicant's full name
            property_address: Property address
            loan_amount: Formatted loan amount
            status: Current status
            stage: Current stage
            has_issue: Whether there's an issue
            issue: Issue description (if any)
            resolution: Resolution steps (if any)
            expected_resolution_time: Expected timeline (if any)

        Returns:
            Dict with success status and message
        """
        subject = f"Application Status Update - {applicant_name} - {property_address}"

        html_content = get_html_template(
            broker_name=broker_name,
            applicant_name=applicant_name,
            property_address=property_address,
            loan_amount=loan_amount,
            status=status,
            stage=stage,
            has_issue=has_issue,
            issue=issue,
            resolution=resolution,
            expected_resolution_time=expected_resolution_time
        )

        if self.mock_mode:
            logger.info(f"MOCK: Would send email to {to_email}")
            logger.info(f"MOCK: Subject: {subject}")
            return {
                "success": True,
                "mock": True,
                "message": f"Email would be sent to {to_email} (mock mode)",
                "email_id": "mock_email_001"
            }

        try:
            params = {
                "from": f"Journey Bank <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }

            email = resend.Emails.send(params)

            logger.info(f"Email sent successfully: {email.get('id')}")
            return {
                "success": True,
                "message": f"Email sent successfully to {to_email}",
                "email_id": email.get('id')
            }

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "error": str(e)
            }


# Singleton instance
_email_client = None


def get_email_client() -> EmailClient:
    """Get or create the email client singleton"""
    global _email_client
    if _email_client is None:
        _email_client = EmailClient()
    return _email_client
