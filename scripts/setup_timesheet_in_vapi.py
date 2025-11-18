"""
Script to setup Timesheet skill in VAPI programmatically

This script:
1. Creates the timesheet tools in VAPI
2. Creates the timesheet assistant in VAPI
3. Updates the database with VAPI IDs
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import logging

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# Import the skill and assistant
from app.skills.timesheet import TimesheetSkill
from app.assistants.timesheet import TimesheetAssistant


async def setup_timesheet_in_vapi():
    """Setup timesheet skill and assistant in VAPI"""

    print("=" * 70)
    print("SETTING UP TIMESHEET SKILL IN VAPI")
    print("=" * 70)
    print()

    # Step 1: Create the timesheet skill (tools)
    print("1️⃣  Creating Timesheet Tools in VAPI...")
    print("-" * 70)

    timesheet_skill = TimesheetSkill()

    try:
        tool_ids = await timesheet_skill.create_tools()
        print(f"✅ Created {len(tool_ids)} tools:")
        for tool_name, tool_id in tool_ids.items():
            print(f"   • {tool_name}: {tool_id}")

        # Save tool IDs to skill instance
        timesheet_skill.tool_ids = tool_ids

    except Exception as e:
        print(f"❌ Failed to create tools: {e}")
        return False

    # Step 2: Create the timesheet assistant
    print()
    print("2️⃣  Creating Timesheet Assistant in VAPI...")
    print("-" * 70)

    timesheet_assistant = TimesheetAssistant()

    try:
        # Get all tool IDs (we need to provide all available tools)
        all_tool_ids = tool_ids.copy()

        # Also need authentication tool - let's get it
        from app.skills.authentication import AuthenticationSkill
        auth_skill = AuthenticationSkill()

        # Check if auth tools already exist, if not create them
        try:
            auth_tool_ids = await auth_skill.create_tools()
            all_tool_ids.update(auth_tool_ids)
        except Exception as e:
            logger.warning(f"Auth tools might already exist: {e}")

        # Setup the assistant
        setup_info = await timesheet_assistant.setup(all_tool_ids)

        print(f"✅ Created assistant:")
        print(f"   • Name: {setup_info['name']}")
        print(f"   • VAPI ID: {setup_info['assistant_id']}")
        print(f"   • Required Skills: {', '.join(setup_info['required_skills'])}")

    except Exception as e:
        print(f"❌ Failed to create assistant: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 3: Update database with VAPI assistant ID
    print()
    print("3️⃣  Updating Database with VAPI IDs...")
    print("-" * 70)

    import httpx
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Update skills table with assistant ID
        response = await client.patch(
            f"{SUPABASE_URL}/rest/v1/skills",
            headers=headers,
            params={"skill_key": "eq.timesheet"},
            json={"vapi_assistant_id": setup_info['assistant_id']}
        )

        if response.status_code == 204:
            print(f"✅ Updated database with VAPI assistant ID")
        else:
            print(f"⚠️  Warning: Failed to update database: {response.status_code}")

    print()
    print("=" * 70)
    print("✅ TIMESHEET SKILL SETUP COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Restart your server to use the new VAPI IDs")
    print("2. Update your VAPI squad to include the timesheet assistant")
    print("3. Test by calling the phone number")
    print()
    print(f"Timesheet Assistant ID: {setup_info['vapi_assistant_id']}")
    print()

    return True


async def verify_setup():
    """Verify the setup is correct"""
    print()
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    print()

    import httpx
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    VAPI_API_KEY = os.getenv("VAPI_API_KEY")

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
    }

    async with httpx.AsyncClient() as client:
        # Check database
        print("Database Check:")
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/skills",
            headers=headers,
            params={"skill_key": "eq.timesheet", "select": "id,name,skill_key,vapi_assistant_id"}
        )

        if response.status_code == 200 and response.json():
            skill = response.json()[0]
            print(f"✅ Timesheet skill exists in database")
            print(f"   • ID: {skill['id']}")
            print(f"   • VAPI Assistant ID: {skill.get('vapi_assistant_id', 'Not set')}")
        else:
            print(f"❌ Timesheet skill not found in database")

        # Check VAPI
        print()
        print("VAPI Check:")

        vapi_headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}"
        }

        # Get all assistants
        response = await client.get(
            "https://api.vapi.ai/assistant",
            headers=vapi_headers
        )

        if response.status_code == 200:
            assistants = response.json()
            timesheet_assistants = [a for a in assistants if 'timesheet' in a.get('name', '').lower()]

            if timesheet_assistants:
                print(f"✅ Found {len(timesheet_assistants)} timesheet assistant(s) in VAPI:")
                for assistant in timesheet_assistants:
                    print(f"   • {assistant['name']}: {assistant['id']}")
            else:
                print(f"⚠️  No timesheet assistants found in VAPI")
                print(f"   (Found {len(assistants)} total assistants)")
        else:
            print(f"❌ Failed to query VAPI: {response.status_code}")

        # Get all tools
        print()
        response = await client.get(
            "https://api.vapi.ai/tool",
            headers=vapi_headers
        )

        if response.status_code == 200:
            tools = response.json()
            timesheet_tools = [
                t for t in tools
                if 'timesheet' in t.get('function', {}).get('name', '').lower()
            ]

            if timesheet_tools:
                print(f"✅ Found {len(timesheet_tools)} timesheet tool(s) in VAPI:")
                for tool in timesheet_tools:
                    print(f"   • {tool['function']['name']}: {tool['id']}")
            else:
                print(f"⚠️  No timesheet tools found in VAPI")
                print(f"   (Found {len(tools)} total tools)")
        else:
            print(f"❌ Failed to query VAPI tools: {response.status_code}")

    print()


if __name__ == "__main__":
    print()
    print("This script will create the timesheet skill tools and assistant in VAPI.")
    print()

    # Check environment
    if not os.getenv("VAPI_API_KEY"):
        print("❌ VAPI_API_KEY not set in environment")
        exit(1)

    if not os.getenv("SUPABASE_URL"):
        print("❌ SUPABASE_URL not set in environment")
        exit(1)

    # Run setup
    success = asyncio.run(setup_timesheet_in_vapi())

    if success:
        # Run verification
        asyncio.run(verify_setup())
    else:
        print()
        print("❌ Setup failed. Please check the errors above.")
        exit(1)
