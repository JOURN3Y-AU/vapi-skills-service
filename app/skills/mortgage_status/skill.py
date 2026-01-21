"""
Mortgage Status Skill - Journey Bank Demo

Provides tools for brokers to check mortgage application status via voice call.
This skill only defines tools - it does not create assistants.
"""

from typing import Dict
from fastapi import FastAPI
import httpx
import logging

from app.skills.base_skill import BaseSkill
from app.config import settings

logger = logging.getLogger(__name__)


class MortgageStatusSkill(BaseSkill):
    """
    Mortgage Status Skill - Check loan application status (Journey Bank Demo)

    This skill provides tools only:
    - verify_broker_code: Validate the broker's authentication code (PIN)
    - lookup_application: Find application by surname + street address
    - get_application_status: Get detailed status and issues
    - send_status_email: Send email summary via Resend

    Note: This skill does not create assistants. Use JourneyBankDemoAssistant.
    """

    def __init__(self):
        super().__init__(
            skill_key="mortgage_status",
            name="Mortgage Status",
            description="Check mortgage application status (Journey Bank Demo)"
        )
        self.vapi_api_key = settings.VAPI_API_KEY
        self.vapi_base_url = "https://api.vapi.ai"
        self.webhook_base_url = settings.webhook_base_url

        if not self.vapi_api_key:
            raise ValueError("VAPI_API_KEY not configured")

    async def create_tools(self) -> Dict[str, str]:
        """
        Create VAPI tools for mortgage status skill

        Returns:
            Dict with tool names mapped to VAPI tool IDs
        """
        logger.info("Creating VAPI tools for Mortgage Status skill...")

        tools_config = {
            "verify_broker_code": {
                "type": "function",
                "function": {
                    "name": "verify_broker_code",
                    "description": "Verify the broker's authentication code (PIN) for security",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "broker_code": {
                                "type": "string",
                                "description": "The broker's authentication code (4-6 digit PIN)"
                            },
                            "vapi_call_id": {
                                "type": "string",
                                "description": "The VAPI call identifier"
                            }
                        },
                        "required": ["broker_code", "vapi_call_id"]
                    }
                },
                "server": {
                    "url": f"{self.webhook_base_url}/api/v1/skills/mortgage-status/verify-broker-code"
                }
            },
            "lookup_application": {
                "type": "function",
                "function": {
                    "name": "lookup_application",
                    "description": "Find a mortgage application by applicant surname and property street address",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "applicant_surname": {
                                "type": "string",
                                "description": "The surname/last name of the mortgage applicant"
                            },
                            "street_address": {
                                "type": "string",
                                "description": "The street address of the property (e.g., '123 Main Street')"
                            },
                            "vapi_call_id": {
                                "type": "string",
                                "description": "The VAPI call identifier"
                            }
                        },
                        "required": ["applicant_surname", "street_address", "vapi_call_id"]
                    }
                },
                "server": {
                    "url": f"{self.webhook_base_url}/api/v1/skills/mortgage-status/lookup-application"
                }
            },
            "get_application_status": {
                "type": "function",
                "function": {
                    "name": "get_application_status",
                    "description": "Get the detailed status and any issues for a mortgage application",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "application_id": {
                                "type": "string",
                                "description": "The unique identifier of the mortgage application"
                            },
                            "vapi_call_id": {
                                "type": "string",
                                "description": "The VAPI call identifier"
                            }
                        },
                        "required": ["application_id", "vapi_call_id"]
                    }
                },
                "server": {
                    "url": f"{self.webhook_base_url}/api/v1/skills/mortgage-status/get-status"
                }
            },
            "send_status_email": {
                "type": "function",
                "function": {
                    "name": "send_status_email",
                    "description": "Send an email summary of the application status to the broker",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "application_id": {
                                "type": "string",
                                "description": "The unique identifier of the mortgage application"
                            },
                            "confirmed_email": {
                                "type": "string",
                                "description": "The confirmed email address to send the summary to"
                            },
                            "vapi_call_id": {
                                "type": "string",
                                "description": "The VAPI call identifier"
                            }
                        },
                        "required": ["application_id", "confirmed_email", "vapi_call_id"]
                    }
                },
                "server": {
                    "url": f"{self.webhook_base_url}/api/v1/skills/mortgage-status/send-email"
                }
            }
        }

        tool_ids = {}
        headers = {
            "Authorization": f"Bearer {self.vapi_api_key}",
            "Content-Type": "application/json"
        }

        # Check for existing tools first
        existing_tools = await self._get_existing_tools(headers)

        async with httpx.AsyncClient() as client:
            for tool_name, tool_config in tools_config.items():
                # Skip if tool already exists
                if tool_name in existing_tools:
                    tool_ids[tool_name] = existing_tools[tool_name]
                    logger.info(f"Using existing tool: {tool_name} ({tool_ids[tool_name]})")
                    continue

                # Create new tool
                response = await client.post(
                    f"{self.vapi_base_url}/tool",
                    headers=headers,
                    json=tool_config
                )

                if response.status_code == 201:
                    tool = response.json()
                    tool_ids[tool_name] = tool['id']
                    logger.info(f"Created tool: {tool_name} ({tool_ids[tool_name]})")
                else:
                    logger.error(f"Failed to create tool {tool_name}: {response.status_code} - {response.text}")
                    raise Exception(f"Tool creation failed for {tool_name}: {response.text}")

        return tool_ids

    async def _get_existing_tools(self, headers: Dict) -> Dict[str, str]:
        """Get existing tools to avoid duplicates"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.vapi_base_url}/tool",
                headers=headers
            )

            if response.status_code == 200:
                tools = response.json()
                tool_map = {}
                for tool in tools:
                    if tool.get('function', {}).get('name'):
                        tool_map[tool['function']['name']] = tool['id']
                return tool_map
            else:
                logger.warning(f"Failed to get existing tools: {response.status_code}")
                return {}

    async def create_assistant(self, tool_ids: Dict[str, str]) -> str:
        """
        Mortgage Status skill does not create assistants.
        It only provides tools that assistants can use.

        Raises:
            NotImplementedError: This skill doesn't create assistants
        """
        raise NotImplementedError(
            "MortgageStatusSkill does not create assistants. "
            "It provides tools for assistants to use. "
            "Use JourneyBankDemoAssistant instead."
        )

    def register_routes(self, app: FastAPI, prefix: str = ""):
        """
        Register mortgage status endpoints with FastAPI

        Args:
            app: FastAPI application instance
            prefix: Optional URL prefix (e.g., "/api/v1")
        """
        from app.skills.mortgage_status.endpoints import router

        app.include_router(router, prefix=prefix)
        logger.info(f"Registered Mortgage Status routes with prefix: {prefix}")
