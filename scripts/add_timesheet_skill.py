"""
Script to add Timesheet skill to database and enable it for test user

This script:
1. Creates the timesheet skill record in the skills table
2. Enables the timesheet skill for the test user (John Smith / +61412345678)
"""

import httpx
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Test user phone number
TEST_USER_PHONE = "+61412345678"


async def add_timesheet_skill():
    """Add timesheet skill to database and enable for test user"""

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Get test user
        print(f"Looking up test user with phone: {TEST_USER_PHONE}")
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={
                "phone_number": f"eq.{TEST_USER_PHONE}",
                "select": "id,name,tenant_id"
            }
        )

        if response.status_code != 200 or not response.json():
            print(f"❌ Test user not found: {response.status_code}")
            return

        user = response.json()[0]
        user_id = user["id"]
        tenant_id = user["tenant_id"]
        print(f"✅ Found user: {user['name']} (ID: {user_id})")

        # Step 2: Check if timesheet skill exists
        print("\nChecking if timesheet skill exists...")
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/skills",
            headers=headers,
            params={
                "skill_key": "eq.timesheet",
                "select": "id,skill_key,name"
            }
        )

        if response.status_code == 200 and response.json():
            skill = response.json()[0]
            skill_id = skill["id"]
            print(f"✅ Timesheet skill already exists (ID: {skill_id})")
        else:
            # Create timesheet skill
            print("Creating timesheet skill...")
            skill_data = {
                "skill_key": "timesheet",
                "name": "Timesheet",
                "description": "Log work hours at construction sites",
                "vapi_assistant_id": None  # Will be populated when assistant is created via VAPI
            }

            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/skills",
                headers=headers,
                json=skill_data
            )

            if response.status_code == 201:
                # Get the created skill
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/skills",
                    headers=headers,
                    params={
                        "skill_key": "eq.timesheet",
                        "select": "id"
                    }
                )
                skill_id = response.json()[0]["id"]
                print(f"✅ Created timesheet skill (ID: {skill_id})")
            else:
                print(f"❌ Failed to create skill: {response.status_code} - {response.text}")
                return

        # Step 3: Check if user_skill association exists
        print("\nChecking if user has timesheet skill enabled...")
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/user_skills",
            headers=headers,
            params={
                "user_id": f"eq.{user_id}",
                "skill_id": f"eq.{skill_id}",
                "select": "id,is_enabled"
            }
        )

        if response.status_code == 200 and response.json():
            user_skill = response.json()[0]
            if user_skill["is_enabled"]:
                print(f"✅ User already has timesheet skill enabled")
            else:
                # Enable the skill
                print("Enabling timesheet skill for user...")
                response = await client.patch(
                    f"{SUPABASE_URL}/rest/v1/user_skills",
                    headers=headers,
                    params={"id": f"eq.{user_skill['id']}"},
                    json={"is_enabled": True}
                )

                if response.status_code == 204:
                    print("✅ Enabled timesheet skill for user")
                else:
                    print(f"❌ Failed to enable skill: {response.status_code}")
        else:
            # Create user_skill association
            print("Adding timesheet skill to user...")
            user_skill_data = {
                "user_id": user_id,
                "skill_id": skill_id,
                "is_enabled": True
            }

            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/user_skills",
                headers=headers,
                json=user_skill_data
            )

            if response.status_code == 201:
                print("✅ Added timesheet skill to user")
            else:
                print(f"❌ Failed to add skill to user: {response.status_code} - {response.text}")
                return

        # Step 4: Verify user's skills
        print("\n" + "="*50)
        print("VERIFICATION: User's enabled skills")
        print("="*50)

        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/user_skills",
            headers=headers,
            params={
                "user_id": f"eq.{user_id}",
                "is_enabled": "eq.true",
                "select": "skill_id,skills(skill_key,name)"
            }
        )

        if response.status_code == 200:
            user_skills = response.json()
            print(f"\n{user['name']} has {len(user_skills)} enabled skill(s):")
            for us in user_skills:
                skill_info = us['skills']
                print(f"  • {skill_info['name']} ({skill_info['skill_key']})")

        print("\n✅ Timesheet skill setup complete!")
        print("\nNext steps:")
        print("1. Run the database migration: migrations/003_create_timesheets.sql")
        print("2. Start/restart the server to register the timesheet skill")
        print("3. The skill will be available for the test user on their next call")


if __name__ == "__main__":
    asyncio.run(add_timesheet_skill())
