"""
Update the Timesheet Assistant in VAPI with V2 system prompt and new tools

This script updates:
1. System prompt to timesheet_prompt_v2 with historical support
2. Adds 3 new tools: get_recent_timesheets, check_date_for_conflicts, update_timesheet_entry
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.assistants.timesheet_prompt_v2 import TIMESHEET_SYSTEM_PROMPT_V2
from app.assistants.timesheet import TimesheetAssistant

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
TIMESHEET_ASSISTANT_ID = "d3a5e1cf-82cb-4f6e-a406-b0170ede3d10"

# Tool IDs (from create_historical_timesheet_tools.py output)
NEW_TOOL_IDS = [
    "77f7df54-69b6-4cac-b3dc-4e6b5a2fe95c",  # get_recent_timesheets
    "f1ac8144-4cc2-420e-8761-664259d767fc",  # check_date_for_conflicts
    "0444a816-a2f1-4321-98e8-dc84f1430c87"   # update_timesheet_entry
]


async def update_timesheet_assistant():
    """Update the timesheet assistant with V2 prompt and new tools"""

    print("=" * 70)
    print("UPDATING TIMESHEET ASSISTANT TO V2 WITH HISTORICAL SUPPORT")
    print("=" * 70)
    print()

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Get current assistant configuration
        print("1️⃣  Fetching current timesheet assistant configuration...")
        response = await client.get(
            f"https://api.vapi.ai/assistant/{TIMESHEET_ASSISTANT_ID}",
            headers=headers
        )

        if response.status_code != 200:
            print(f"   ❌ Failed to fetch assistant: {response.status_code}")
            return

        current_config = response.json()
        print(f"   ✅ Found: {current_config.get('name')}")
        print()

        # Step 2: Check V2 prompt features and get updated greeting
        print("2️⃣  Loading V2 system prompt and first message...")
        timesheet_assistant = TimesheetAssistant()
        updated_prompt = TIMESHEET_SYSTEM_PROMPT_V2
        updated_first_message = timesheet_assistant.get_first_message()

        # Check for key V2 features
        v2_features = [
            ("Timezone awareness", "tenant_timezone" in updated_prompt),
            ("Historical date support", "work_date" in updated_prompt),
            ("Conflict detection", "check_date_for_conflicts" in updated_prompt),
            ("Update entry support", "update_timesheet_entry" in updated_prompt),
            ("Date calculation", "current_date" in updated_prompt)
        ]

        for feature, present in v2_features:
            status = "✅" if present else "❌"
            print(f"   {status} {feature}")
        print()

        # Step 3: Get current tools and add new ones
        print("3️⃣  Updating tool list...")
        current_model = current_config.get('model', {})
        current_tool_ids = current_model.get('toolIds', [])
        print(f"   Current tools: {len(current_tool_ids)}")

        # Add new tool IDs (avoid duplicates)
        updated_tool_ids = list(current_tool_ids)
        for tool_id in NEW_TOOL_IDS:
            if tool_id not in updated_tool_ids:
                updated_tool_ids.append(tool_id)

        print(f"   Updated tools: {len(updated_tool_ids)}")
        print(f"   Added: {len(updated_tool_ids) - len(current_tool_ids)} new tools")
        print()

        # Step 4: Build update payload
        print("4️⃣  Building update payload...")

        # Update the system prompt in messages
        messages = [
            {
                "role": "system",
                "content": updated_prompt
            }
        ]

        # Update model config with new prompt and tools
        current_model['messages'] = messages
        current_model['toolIds'] = updated_tool_ids

        update_payload = {
            "name": current_config.get('name'),
            "model": current_model,
            "voice": current_config.get('voice'),
            "firstMessage": updated_first_message,
            "firstMessageMode": current_config.get('firstMessageMode')
        }

        # Preserve other optional fields if they exist
        if 'server' in current_config:
            update_payload['server'] = current_config['server']
        if 'serverMessages' in current_config:
            update_payload['serverMessages'] = current_config['serverMessages']

        print("   ✅ Payload prepared")
        print()

        # Step 5: Update the assistant
        print("5️⃣  Updating assistant in VAPI...")

        response = await client.patch(
            f"https://api.vapi.ai/assistant/{TIMESHEET_ASSISTANT_ID}",
            headers=headers,
            json=update_payload
        )

        if response.status_code == 200:
            print("   ✅ Assistant updated successfully")
            print()

            # Verify the update
            print("6️⃣  Verifying update...")
            verify_response = await client.get(
                f"https://api.vapi.ai/assistant/{TIMESHEET_ASSISTANT_ID}",
                headers=headers
            )

            if verify_response.status_code == 200:
                verified = verify_response.json()
                system_prompt = verified.get('model', {}).get('messages', [{}])[0].get('content', '')
                tool_ids = verified.get('toolIds', [])

                # Check V2 features in verified prompt
                if 'tenant_timezone' in system_prompt:
                    print("   ✅ Verified: Timezone awareness present")
                if 'check_date_for_conflicts' in system_prompt:
                    print("   ✅ Verified: Conflict detection logic present")
                if 'update_timesheet_entry' in system_prompt:
                    print("   ✅ Verified: Update entry logic present")

                print(f"   ✅ Verified: {len(tool_ids)} tools configured")
                print()
            else:
                print(f"   ⚠️  Could not verify: {verify_response.status_code}")
                print()

        else:
            print(f"   ❌ Failed to update: {response.status_code}")
            print(f"   {response.text}")
            return

        print("=" * 70)
        print("✅ TIMESHEET ASSISTANT V2 UPDATE COMPLETE")
        print("=" * 70)
        print()
        print("The timesheet assistant now supports:")
        print("  • Timezone-aware date handling")
        print("  • Historical timesheet logging (last 14 days)")
        print("  • Conflict detection for existing entries")
        print("  • Updating/overwriting existing entries")
        print("  • Query recent timesheet history")
        print()
        print("Next steps:")
        print("  1. Deploy code changes to Railway")
        print("  2. Test historical timesheet flow")
        print("     - Log for today")
        print("     - Log for yesterday")
        print("     - Test conflict detection")
        print("     - Test update entry")
        print()


if __name__ == "__main__":
    asyncio.run(update_timesheet_assistant())
