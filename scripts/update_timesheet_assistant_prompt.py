"""
Update the Timesheet Assistant in VAPI with the updated system prompt and greeting

This script updates the timesheet assistant to offer the site list proactively.
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.assistants.timesheet import TimesheetAssistant

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
TIMESHEET_ASSISTANT_ID = "d3a5e1cf-82cb-4f6e-a406-b0170ede3d10"


async def update_timesheet_assistant():
    """Update the timesheet assistant in VAPI"""

    print("=" * 70)
    print("UPDATING TIMESHEET ASSISTANT IN VAPI")
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

        # Step 2: Get updated configuration from code
        print("2️⃣  Getting updated configuration from code...")
        timesheet = TimesheetAssistant()
        updated_prompt = timesheet.get_system_prompt()
        updated_first_message = timesheet.get_first_message()

        # Check if prompt mentions site list offer
        if "I can list your sites" in updated_first_message:
            print("   ✅ New greeting offers to list sites")
        if "Would you like me to run through your sites" in updated_prompt:
            print("   ✅ New prompt includes site list instructions")
        print()

        # Step 3: Build update payload
        print("3️⃣  Building update payload...")

        # Get current model config
        current_model = current_config.get('model', {})

        # Update the system prompt in messages
        messages = current_model.get('messages', [])
        if messages and messages[0].get('role') == 'system':
            messages[0]['content'] = updated_prompt
        else:
            messages = [
                {
                    "role": "system",
                    "content": updated_prompt
                }
            ]

        current_model['messages'] = messages

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

        # Step 4: Update the assistant
        print("4️⃣  Updating assistant in VAPI...")

        response = await client.patch(
            f"https://api.vapi.ai/assistant/{TIMESHEET_ASSISTANT_ID}",
            headers=headers,
            json=update_payload
        )

        if response.status_code == 200:
            print("   ✅ Assistant updated successfully")
            print()

            # Verify the update
            print("5️⃣  Verifying update...")
            verify_response = await client.get(
                f"https://api.vapi.ai/assistant/{TIMESHEET_ASSISTANT_ID}",
                headers=headers
            )

            if verify_response.status_code == 200:
                verified = verify_response.json()
                first_message = verified.get('firstMessage', '')
                system_prompt = verified.get('model', {}).get('messages', [{}])[0].get('content', '')

                if 'I can list your sites' in first_message:
                    print("   ✅ Verified: Greeting offers to list sites")
                    print(f"   📝 New greeting: \"{first_message}\"")
                    print()

                if 'Would you like me to run through your sites' in system_prompt:
                    print("   ✅ Verified: System prompt includes site list logic")
                else:
                    print("   ⚠️  Warning: Site list logic not found in verified prompt")
            else:
                print(f"   ⚠️  Could not verify: {verify_response.status_code}")
                print()

        else:
            print(f"   ❌ Failed to update: {response.status_code}")
            print(f"   {response.text}")
            return

        print("=" * 70)
        print("✅ TIMESHEET ASSISTANT UPDATE COMPLETE")
        print("=" * 70)
        print()
        print("The timesheet assistant now:")
        print("  • Offers to list sites in the greeting message")
        print("  • Can proactively list sites when users seem uncertain")
        print("  • Uses available_sites from authentication")
        print()
        print("Next steps:")
        print("  1. Test by calling the VAPI number")
        print("  2. Say 'timesheet'")
        print("  3. Listen for the new greeting with site list offer")
        print("  4. Say 'yes' to hear your sites listed")
        print()


if __name__ == "__main__":
    asyncio.run(update_timesheet_assistant())
