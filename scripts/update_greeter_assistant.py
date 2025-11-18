"""
Update the Greeter Assistant in VAPI with the updated system prompt

The greeter's system prompt was updated to include timesheet routing,
but the VAPI assistant needs to be updated with this new prompt.
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.assistants.greeter import GreeterAssistant

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
GREETER_ASSISTANT_ID = "4300f282-35d2-4a06-9a67-f5b6d45e167f"


async def update_greeter():
    """Update the greeter assistant in VAPI"""

    print("=" * 70)
    print("UPDATING GREETER ASSISTANT IN VAPI")
    print("=" * 70)
    print()

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Get current greeter configuration
        print("1️⃣  Fetching current greeter configuration...")
        response = await client.get(
            f"https://api.vapi.ai/assistant/{GREETER_ASSISTANT_ID}",
            headers=headers
        )

        if response.status_code != 200:
            print(f"❌ Failed to fetch assistant: {response.status_code}")
            return

        current_config = response.json()
        print(f"   ✅ Found: {current_config.get('name')}")

        # Step 2: Get updated prompt from code
        print("\n2️⃣  Getting updated system prompt from code...")
        greeter = GreeterAssistant()
        updated_prompt = greeter.get_system_prompt()

        # Check if prompt mentions timesheet
        if "timesheet" in updated_prompt.lower():
            print("   ✅ New prompt includes timesheet routing")
        else:
            print("   ⚠️  Warning: Prompt doesn't mention timesheet")

        # Step 3: Build update payload
        print("\n3️⃣  Building update payload...")

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
            "firstMessage": current_config.get('firstMessage'),
            "firstMessageMode": current_config.get('firstMessageMode')
        }

        # Preserve other optional fields if they exist
        if 'server' in current_config:
            update_payload['server'] = current_config['server']
        if 'serverMessages' in current_config:
            update_payload['serverMessages'] = current_config['serverMessages']

        print("   ✅ Payload prepared")

        # Step 4: Update the assistant
        print("\n4️⃣  Updating assistant in VAPI...")

        response = await client.patch(
            f"https://api.vapi.ai/assistant/{GREETER_ASSISTANT_ID}",
            headers=headers,
            json=update_payload
        )

        if response.status_code == 200:
            print("   ✅ Assistant updated successfully")

            # Verify the update
            print("\n5️⃣  Verifying update...")
            verify_response = await client.get(
                f"https://api.vapi.ai/assistant/{GREETER_ASSISTANT_ID}",
                headers=headers
            )

            if verify_response.status_code == 200:
                verified = verify_response.json()
                system_prompt = verified.get('model', {}).get('messages', [{}])[0].get('content', '')

                if 'timesheet' in system_prompt.lower():
                    print("   ✅ Verified: Timesheet routing is in the prompt")

                    # Show the relevant section
                    print("\n   📝 Relevant section of updated prompt:")
                    lines = system_prompt.split('\n')
                    for i, line in enumerate(lines):
                        if 'timesheet' in line.lower():
                            # Show context around timesheet mentions
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            for j in range(start, end):
                                marker = "   >>> " if j == i else "       "
                                print(f"{marker}{lines[j]}")
                            break
                else:
                    print("   ⚠️  Warning: Timesheet not found in verified prompt")
            else:
                print(f"   ⚠️  Could not verify: {verify_response.status_code}")

        else:
            print(f"   ❌ Failed to update: {response.status_code}")
            print(f"   {response.text}")
            return

        print("\n" + "=" * 70)
        print("✅ GREETER ASSISTANT UPDATE COMPLETE")
        print("=" * 70)
        print()
        print("The greeter now includes timesheet in its routing logic:")
        print("  • Single skill (timesheet): 'Hi [name], it's Jill! Ready to log your timesheet?'")
        print("  • Multiple skills: 'I can help with voice notes, site updates, or timesheets'")
        print()
        print("Next steps:")
        print("  1. Test by calling from +61412345678")
        print("  2. Say 'timesheet' or 'log my time'")
        print("  3. Verify smooth transfer to timesheet assistant")
        print()


if __name__ == "__main__":
    asyncio.run(update_greeter())
