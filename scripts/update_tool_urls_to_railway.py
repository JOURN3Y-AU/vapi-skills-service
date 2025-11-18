"""
Update timesheet tool URLs from Cloudflare Tunnel to Railway

This script updates the webhook URLs for all timesheet tools to point to the
Railway production URL instead of the local Cloudflare Tunnel.
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
RAILWAY_URL = "https://journ3y-vapi-skills-service.up.railway.app"

# Tool IDs for timesheet tools
TIMESHEET_TOOLS = {
    "identify_site_for_timesheet": "af084258-9d44-4ba7-b7cf-c0d781faa262",
    "save_timesheet_entry": "ec4e9d4a-06f9-4055-a378-1f3e7b545fdf",
    "confirm_and_save_all": "e219b712-76b4-4fdb-9ea3-51bf98be86c2"
}

# Endpoint paths
TOOL_ENDPOINTS = {
    "identify_site_for_timesheet": "/api/v1/skills/timesheet/identify-site",
    "save_timesheet_entry": "/api/v1/skills/timesheet/save-entry",
    "confirm_and_save_all": "/api/v1/skills/timesheet/confirm-all"
}


async def update_tool_urls():
    """Update tool URLs to Railway"""

    print("=" * 70)
    print("UPDATING TIMESHEET TOOL URLs TO RAILWAY")
    print("=" * 70)
    print()
    print(f"Target URL: {RAILWAY_URL}")
    print()

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        for tool_name, tool_id in TIMESHEET_TOOLS.items():
            print(f"🔧 Updating {tool_name}...")
            print(f"   Tool ID: {tool_id}")

            # Get current tool configuration
            response = await client.get(
                f"https://api.vapi.ai/tool/{tool_id}",
                headers=headers
            )

            if response.status_code != 200:
                print(f"   ❌ Failed to fetch tool: {response.status_code}")
                continue

            tool_config = response.json()
            current_url = tool_config.get('server', {}).get('url', 'Unknown')
            print(f"   Current URL: {current_url}")

            # Build new URL
            endpoint = TOOL_ENDPOINTS[tool_name]
            new_url = f"{RAILWAY_URL}{endpoint}"
            print(f"   New URL: {new_url}")

            # Build update payload with only server URL
            update_payload = {
                "server": {
                    "url": new_url
                }
            }

            # Update the tool
            update_response = await client.patch(
                f"https://api.vapi.ai/tool/{tool_id}",
                headers=headers,
                json=update_payload
            )

            if update_response.status_code == 200:
                print(f"   ✅ Updated successfully")
            else:
                print(f"   ❌ Failed to update: {update_response.status_code}")
                print(f"   {update_response.text}")

            print()

        print("=" * 70)
        print("✅ TOOL URL UPDATE COMPLETE")
        print("=" * 70)
        print()
        print("All timesheet tools now point to Railway production:")
        print(f"  {RAILWAY_URL}")
        print()
        print("Next steps:")
        print("  1. Test by calling the VAPI number")
        print("  2. Say 'timesheet'")
        print("  3. Tools will now hit Railway instead of local tunnel")
        print()
        print("⚠️  Note: Make sure Railway deployment is live and healthy!")
        print(f"  Check: {RAILWAY_URL}/health")
        print()


if __name__ == "__main__":
    print()
    print("This will update timesheet tool URLs to point to Railway production.")
    print()

    asyncio.run(update_tool_urls())
