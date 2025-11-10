"""
Timesheet Skill - FastAPI Endpoints

Webhook endpoints for verbal timesheet logging using VAPI format.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional, List
import logging
import json
import httpx
import uuid
from datetime import datetime, time as datetime_time
import pytz

from app.vapi_utils import extract_vapi_args
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["timesheet"])

# Sydney timezone for date handling
SYDNEY_TZ = pytz.timezone('Australia/Sydney')


# Helper function to get session context
async def get_session_context_by_call_id(vapi_call_id: str) -> Optional[Dict]:
    """
    Get session context from vapi_logs using call ID
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/vapi_logs",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                },
                params={
                    "vapi_call_id": f"eq.{vapi_call_id}",
                    "interaction_type": "eq.authentication",
                    "select": "tenant_id,user_id,caller_phone,raw_log_data",
                    "limit": "1",
                    "order": "created_at.desc"
                }
            )

            if response.status_code == 200:
                logs = response.json()
                if logs:
                    log_entry = logs[0]
                    return {
                        "tenant_id": log_entry["tenant_id"],
                        "user_id": log_entry["user_id"],
                        "caller_phone": log_entry["caller_phone"],
                        "user_name": log_entry["raw_log_data"].get("user_name"),
                        "tenant_name": log_entry["raw_log_data"].get("tenant_name"),
                        "available_sites": log_entry["raw_log_data"].get("available_sites", [])
                    }

            logger.warning(f"No session context found for call ID: {vapi_call_id}")
            return None

    except Exception as e:
        logger.error(f"Error getting session context for call {vapi_call_id}: {str(e)}")
        return None


def calculate_hours_worked(start_time: str, end_time: str) -> float:
    """
    Calculate hours worked from start and end times

    Args:
        start_time: Time in HH:MM format
        end_time: Time in HH:MM format

    Returns:
        Hours worked as a decimal (e.g., 7.5 for 7 hours 30 minutes)
    """
    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")

        # Handle case where end time is past midnight
        if end < start:
            end = end.replace(day=start.day + 1)

        duration = end - start
        hours = duration.total_seconds() / 3600
        return round(hours, 2)
    except Exception as e:
        logger.error(f"Error calculating hours: {e}")
        return 0.0


@router.post("/api/v1/skills/timesheet/identify-site")
async def identify_site_for_timesheet(request: dict):
    """
    Identify which site the user wants to log time for
    Uses AI to match user's description to available sites in their tenant
    """
    try:
        # Extract VAPI arguments
        tool_call_id, args = extract_vapi_args(request)

        # Extract call ID from the full request structure
        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = tool_call_id

        site_description = args.get("site_description", "")

        logger.info(f"Identifying site for timesheet. Call: {vapi_call_id}, Input: {site_description}")

        # Get session context
        session_context = await get_session_context_by_call_id(vapi_call_id)

        if not session_context:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "site_identified": False,
                        "error": "Session not found. Please authenticate first.",
                        "message": "I couldn't find your session. Please try calling again."
                    }
                }]
            }

        tenant_id = session_context["tenant_id"]

        async with httpx.AsyncClient() as client:
            # Get available sites for this tenant
            sites_response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/entities",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                },
                params={
                    "tenant_id": f"eq.{tenant_id}",
                    "entity_type": "eq.sites",
                    "is_active": "eq.true",
                    "select": "id,name,identifier,address"
                }
            )

            if sites_response.status_code != 200 or not sites_response.json():
                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "site_identified": False,
                            "message": "I couldn't find any active sites for your account. Please contact support."
                        }
                    }]
                }

            sites = sites_response.json()

            # If no site_description provided, return the list of available sites
            if not site_description or site_description.strip() == "":
                site_list_for_assistant = [
                    {
                        "site_id": site['id'],
                        "site_name": site['name'],
                        "site_identifier": site.get('identifier'),
                        "site_address": site.get('address')
                    }
                    for site in sites
                ]

                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "site_identified": False,
                            "sites_list": site_list_for_assistant,
                            "message": f"You have {len(sites)} sites available for timesheet logging."
                        }
                    }]
                }

            # Use OpenAI to match user input to available sites
            site_list = "\n".join([
                f"- ID: {site['id']}, Name: {site['name']}, Identifier: {site.get('identifier', 'None')}, Address: {site.get('address', 'None')}"
                for site in sites
            ])

            prompt = f"""
Available construction sites:
{site_list}

User said: "{site_description}"

Which site are they referring to? You MUST use the exact ID from the list above. Return JSON only:
{{
  "site_found": true/false,
  "site_id": "exact UUID from the ID field above if found, null if not found",
  "site_name": "exact name if found",
  "confidence": "high/medium/low"
}}

IMPORTANT: The site_id MUST be the exact UUID from the ID field, not a shortened version.
"""

            # Call OpenAI API for site matching
            openai_response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 500,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            if openai_response.status_code != 200:
                logger.error(f"OpenAI API error: {openai_response.status_code} - {openai_response.text}")
                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "site_identified": False,
                            "message": "I had trouble identifying that site. Could you be more specific?"
                        }
                    }]
                }

            openai_data = openai_response.json()
            ai_content = openai_data['choices'][0]['message']['content']

            # Parse JSON from AI response
            # Handle markdown code blocks
            if "```json" in ai_content:
                ai_content = ai_content.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_content:
                ai_content = ai_content.split("```")[1].split("```")[0].strip()

            match_result = json.loads(ai_content)

            if match_result.get("site_found"):
                site_id = match_result["site_id"]
                site_name = match_result["site_name"]
                confidence = match_result.get("confidence", "medium")

                logger.info(f"Site identified: {site_name} ({site_id}) with {confidence} confidence")

                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "site_identified": True,
                            "site_id": site_id,
                            "site_name": site_name,
                            "confidence": confidence,
                            "message": f"Great! I've identified {site_name}. What time did you start work there today?"
                        }
                    }]
                }
            else:
                # Site not found - provide list for clarification
                site_names = [site['name'] for site in sites]
                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "site_identified": False,
                            "available_sites": site_names,
                            "message": f"I couldn't find that site. Your available sites are: {', '.join(site_names)}. Which one did you mean?"
                        }
                    }]
                }

    except Exception as e:
        logger.error(f"Error in identify_site_for_timesheet: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "site_identified": False,
                    "error": str(e),
                    "message": "I encountered an error identifying the site. Please try again."
                }
            }]
        }


@router.post("/api/v1/skills/timesheet/save-entry")
async def save_timesheet_entry(request: dict):
    """
    Save a timesheet entry for one site
    This is called for each site the user worked at
    """
    try:
        # Extract VAPI arguments
        tool_call_id, args = extract_vapi_args(request)

        # Extract call ID
        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = args.get("vapi_call_id", tool_call_id)

        # Get required fields
        site_id = args.get("site_id")
        start_time = args.get("start_time")
        end_time = args.get("end_time")
        work_description = args.get("work_description")
        plans_for_tomorrow = args.get("plans_for_tomorrow", "")

        logger.info(f"Saving timesheet entry. Call: {vapi_call_id}, Site: {site_id}")

        # Get session context
        session_context = await get_session_context_by_call_id(vapi_call_id)

        if not session_context:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "error": "Session not found",
                        "message": "I couldn't find your session. Please try calling again."
                    }
                }]
            }

        # Calculate hours worked
        hours_worked = calculate_hours_worked(start_time, end_time)

        # Get today's date in Sydney time
        sydney_now = datetime.now(SYDNEY_TZ)
        work_date = sydney_now.date()

        # Create timesheet entry
        timesheet_entry = {
            "id": str(uuid.uuid4()),
            "site_id": site_id,
            "user_id": session_context["user_id"],
            "tenant_id": session_context["tenant_id"],
            "vapi_call_id": vapi_call_id,
            "work_date": work_date.isoformat(),
            "start_time": start_time,
            "end_time": end_time,
            "hours_worked": hours_worked,
            "work_description": work_description,
            "plans_for_tomorrow": plans_for_tomorrow
        }

        # Save to database
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.SUPABASE_URL}/rest/v1/timesheets",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                },
                json=timesheet_entry
            )

            if response.status_code != 201:
                logger.error(f"Failed to save timesheet: {response.status_code} - {response.text}")
                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "success": False,
                            "error": "Database error",
                            "message": "I had trouble saving that entry. Please try again."
                        }
                    }]
                }

        logger.info(f"Timesheet entry saved successfully: {timesheet_entry['id']}")

        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "success": True,
                    "entry_id": timesheet_entry['id'],
                    "hours_worked": hours_worked,
                    "message": f"Got it! I've logged {hours_worked} hours for that site."
                }
            }]
        }

    except Exception as e:
        logger.error(f"Error in save_timesheet_entry: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "success": False,
                    "error": str(e),
                    "message": "I encountered an error saving your timesheet. Please try again."
                }
            }]
        }


@router.post("/api/v1/skills/timesheet/confirm-all")
async def confirm_and_save_all(request: dict):
    """
    Finalize all timesheet entries for this call
    This is called after all sites have been logged and user confirms
    """
    try:
        # Extract VAPI arguments
        tool_call_id, args = extract_vapi_args(request)

        # Extract call ID
        vapi_call_id = None
        if "message" in request and "call" in request["message"]:
            vapi_call_id = request["message"]["call"]["id"]

        if not vapi_call_id:
            vapi_call_id = args.get("vapi_call_id", tool_call_id)

        user_confirmed = args.get("user_confirmed", False)

        logger.info(f"Confirming timesheet entries. Call: {vapi_call_id}, Confirmed: {user_confirmed}")

        if not user_confirmed:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "message": "No problem, let's make corrections. What needs to be changed?"
                    }
                }]
            }

        # Get session context
        session_context = await get_session_context_by_call_id(vapi_call_id)

        if not session_context:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": {
                        "success": False,
                        "error": "Session not found"
                    }
                }]
            }

        # Get all timesheet entries for this call
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/timesheets",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                },
                params={
                    "vapi_call_id": f"eq.{vapi_call_id}",
                    "select": "id,hours_worked,site_id,entities(name)"
                }
            )

            if response.status_code == 200:
                entries = response.json()
                total_hours = sum(entry.get('hours_worked', 0) for entry in entries)
                num_sites = len(entries)

                logger.info(f"Confirmed {num_sites} timesheet entries totaling {total_hours} hours")

                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "success": True,
                            "total_entries": num_sites,
                            "total_hours": total_hours,
                            "message": f"Perfect! I've saved your timesheet for {num_sites} site{'s' if num_sites > 1 else ''}, totaling {total_hours} hours. Have a great day!"
                        }
                    }]
                }
            else:
                logger.error(f"Failed to retrieve entries: {response.status_code}")
                return {
                    "results": [{
                        "toolCallId": tool_call_id,
                        "result": {
                            "success": True,
                            "message": "Your timesheet has been saved. Have a great day!"
                        }
                    }]
                }

    except Exception as e:
        logger.error(f"Error in confirm_and_save_all: {str(e)}", exc_info=True)
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": {
                    "success": True,
                    "message": "Your timesheet has been saved. Have a great day!"
                }
            }]
        }
