"""
Create the 3 new timesheet tools in VAPI for historical timesheet support

This script creates:
1. get_recent_timesheets - Query recently logged timesheets
2. check_date_for_conflicts - Check for existing entries on a date
3. update_timesheet_entry - Update/overwrite existing entry
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
RAILWAY_BASE_URL = "https://journ3y-vapi-skills-service.up.railway.app"


async def create_vapi_tools():
    """Create the 3 new timesheet tools in VAPI"""

    print("=" * 70)
    print("CREATING NEW TIMESHEET TOOLS IN VAPI")
    print("=" * 70)
    print()

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    tools = [
        {
            "name": "get_recent_timesheets",
            "description": "Get a summary of recently logged timesheets for the current user. Returns the dates they've logged time for in the last 14 days (or custom period). Use this when user asks 'what have I logged?' or 'what days did I work?'",
            "url": f"{RAILWAY_BASE_URL}/api/v1/skills/timesheet/get-recent-timesheets",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "number",
                        "description": "Number of days to look back (default 14)"
                    },
                    "vapi_call_id": {
                        "type": "string",
                        "description": "The VAPI call ID for retrieving session context"
                    }
                },
                "required": ["vapi_call_id"]
            }
        },
        {
            "name": "check_date_for_conflicts",
            "description": "Check if the user has already logged timesheets for a specific date. Returns existing entries if found. MUST be called BEFORE collecting time details when logging historical dates (not today). This allows Jill to ask if user wants to update existing entry or add more time.",
            "url": f"{RAILWAY_BASE_URL}/api/v1/skills/timesheet/check-date-conflicts",
            "parameters": {
                "type": "object",
                "properties": {
                    "work_date": {
                        "type": "string",
                        "description": "The date to check in ISO format (YYYY-MM-DD)"
                    },
                    "site_id": {
                        "type": "string",
                        "description": "Optional site ID to check for specific site conflicts"
                    },
                    "vapi_call_id": {
                        "type": "string",
                        "description": "The VAPI call ID for retrieving session context"
                    }
                },
                "required": ["work_date", "vapi_call_id"]
            }
        },
        {
            "name": "update_timesheet_entry",
            "description": "Update/overwrite an existing timesheet entry. Use this when user wants to correct or change an existing entry (different from adding a new entry for same date). Requires the timesheet_id from check_date_for_conflicts.",
            "url": f"{RAILWAY_BASE_URL}/api/v1/skills/timesheet/update-entry",
            "parameters": {
                "type": "object",
                "properties": {
                    "timesheet_id": {
                        "type": "string",
                        "description": "The ID of the timesheet entry to update (from check_date_for_conflicts)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "New start time in HH:MM 24-hour format (e.g., '07:00')"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "New end time in HH:MM 24-hour format (e.g., '15:00')"
                    },
                    "work_description": {
                        "type": "string",
                        "description": "Updated description of work performed"
                    },
                    "plans_for_tomorrow": {
                        "type": "string",
                        "description": "Updated plans for tomorrow (optional, can be empty string)"
                    },
                    "vapi_call_id": {
                        "type": "string",
                        "description": "The VAPI call ID for retrieving session context"
                    }
                },
                "required": ["timesheet_id", "start_time", "end_time", "work_description", "vapi_call_id"]
            }
        }
    ]

    created_tools = []

    async with httpx.AsyncClient() as client:
        for i, tool_def in enumerate(tools, 1):
            print(f"{i}️⃣  Creating tool: {tool_def['name']}")
            print(f"   URL: {tool_def['url']}")

            # Build the VAPI tool payload
            payload = {
                "type": "function",
                "async": False,
                "function": {
                    "name": tool_def["name"],
                    "description": tool_def["description"],
                    "parameters": tool_def["parameters"]
                },
                "server": {
                    "url": tool_def["url"]
                }
            }

            response = await client.post(
                "https://api.vapi.ai/tool",
                headers=headers,
                json=payload
            )

            if response.status_code == 201:
                tool_data = response.json()
                tool_id = tool_data.get("id")
                created_tools.append({
                    "name": tool_def["name"],
                    "id": tool_id,
                    "url": tool_def["url"]
                })
                print(f"   ✅ Created successfully")
                print(f"   📝 Tool ID: {tool_id}")
                print()
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   {response.text}")
                print()

    print("=" * 70)
    print("✅ TOOL CREATION COMPLETE")
    print("=" * 70)
    print()
    print("Created Tools Summary:")
    print()
    for tool in created_tools:
        print(f"  • {tool['name']}")
        print(f"    ID: {tool['id']}")
        print(f"    URL: {tool['url']}")
        print()

    print("Next steps:")
    print("  1. Update timesheet assistant in VAPI with new system prompt")
    print("  2. Deploy code changes to Railway")
    print("  3. Test historical timesheet logging flow")
    print()

    return created_tools


if __name__ == "__main__":
    asyncio.run(create_vapi_tools())
