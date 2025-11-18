"""
Fix the timesheet assistant name in VAPI

The assistant was created with name "timesheet" instead of "JSMB-Jill-timesheet".
This script will:
1. Delete the incorrectly named assistant
2. Recreate it with the correct name
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")

async def fix_assistant_name():
    """Fix the assistant name"""

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Find and delete the incorrectly named assistant
        print("1️⃣  Finding incorrectly named assistant...")
        response = await client.get("https://api.vapi.ai/assistant", headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to fetch assistants: {response.status_code}")
            return

        assistants = response.json()
        timesheet_assistant = None

        for a in assistants:
            if a.get('name') == 'timesheet':
                timesheet_assistant = a
                break

        if timesheet_assistant:
            print(f"   Found: {timesheet_assistant['name']} ({timesheet_assistant['id']})")
            print(f"\n2️⃣  Deleting incorrectly named assistant...")

            delete_response = await client.delete(
                f"https://api.vapi.ai/assistant/{timesheet_assistant['id']}",
                headers=headers
            )

            if delete_response.status_code == 200:
                print(f"   ✅ Deleted")
            else:
                print(f"   ❌ Failed to delete: {delete_response.status_code}")
                return
        else:
            print(f"   ⚠️  Assistant 'timesheet' not found")

        # Step 2: Recreate with correct name
        print(f"\n3️⃣  Creating assistant with correct name...")

        from app.assistants.timesheet import TimesheetAssistant
        from app.skills.timesheet import TimesheetSkill
        from app.skills.authentication import AuthenticationSkill

        # Get tool IDs
        timesheet_skill = TimesheetSkill()
        auth_skill = AuthenticationSkill()

        # Get existing tools
        tools_response = await client.get("https://api.vapi.ai/tool", headers=headers)
        tools = tools_response.json()

        tool_ids = {}
        for tool in tools:
            tool_name = tool.get('function', {}).get('name', '')
            tool_ids[tool_name] = tool['id']

        print(f"   Found {len(tool_ids)} existing tools")

        # Create assistant with correct name
        assistant = TimesheetAssistant()

        # Override the base create method to use self.name instead of self.assistant_key
        required_tool_names = assistant.get_required_tool_names()
        assistant_tool_ids = []

        for tool_name in required_tool_names:
            if tool_name in tool_ids:
                assistant_tool_ids.append(tool_ids[tool_name])
            else:
                print(f"   ❌ Required tool '{tool_name}' not found")
                return

        # Build assistant config with CORRECT name
        model_config = assistant.get_model_config()
        model_config["messages"] = [
            {
                "role": "system",
                "content": assistant.get_system_prompt()
            }
        ]
        model_config["toolIds"] = assistant_tool_ids

        assistant_config = {
            "name": assistant.name,  # Use assistant.name NOT assistant.assistant_key!
            "model": model_config,
            "voice": assistant.get_voice_config(),
            "firstMessage": assistant.get_first_message(),
            "firstMessageMode": "assistant-speaks-first"
        }

        create_response = await client.post(
            "https://api.vapi.ai/assistant",
            headers=headers,
            json=assistant_config
        )

        if create_response.status_code == 201:
            new_assistant = create_response.json()
            print(f"   ✅ Created: {new_assistant['name']}")
            print(f"   ID: {new_assistant['id']}")

            # Update database
            print(f"\n4️⃣  Updating database...")
            import httpx as db_httpx

            SUPABASE_URL = os.getenv("SUPABASE_URL")
            SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

            db_headers = {
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json"
            }

            db_response = await client.patch(
                f"{SUPABASE_URL}/rest/v1/skills",
                headers=db_headers,
                params={"skill_key": "eq.timesheet"},
                json={"vapi_assistant_id": new_assistant['id']}
            )

            if db_response.status_code == 204:
                print(f"   ✅ Database updated")
            else:
                print(f"   ⚠️  Database update status: {db_response.status_code}")

            print(f"\n✅ COMPLETE!")
            print(f"\nTimesheet Assistant:")
            print(f"  Name: {new_assistant['name']}")
            print(f"  ID: {new_assistant['id']}")

        else:
            print(f"   ❌ Failed to create: {create_response.status_code}")
            print(f"   {create_response.text}")

if __name__ == "__main__":
    asyncio.run(fix_assistant_name())
