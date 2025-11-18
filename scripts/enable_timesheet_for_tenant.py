"""
Enable timesheet skill for all users in a specific tenant

This script enables the timesheet skill for all active users in the
Built by MK tenant.
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Built by MK tenant ID
TENANT_ID = "ba920f42-43df-44b5-a2e8-f740764a56d5"


async def enable_timesheet_for_tenant():
    """Enable timesheet skill for all users in the tenant"""

    print("=" * 70)
    print("ENABLING TIMESHEET SKILL FOR TENANT USERS")
    print("=" * 70)
    print()
    print(f"Tenant: Built by MK ({TENANT_ID})")
    print()

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Get the timesheet skill ID
        print("1️⃣  Finding timesheet skill...")
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/skills",
            headers=headers,
            params={"skill_key": "eq.timesheet", "select": "id,name"}
        )

        if response.status_code != 200 or not response.json():
            print(f"   ❌ Could not find timesheet skill")
            return False

        timesheet_skill = response.json()[0]
        skill_id = timesheet_skill["id"]
        print(f"   ✅ Found: {timesheet_skill['name']} ({skill_id})")
        print()

        # Step 2: Get all active users in the tenant
        print("2️⃣  Finding users in Built by MK tenant...")
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/users",
            headers=headers,
            params={
                "tenant_id": f"eq.{TENANT_ID}",
                "is_active": "eq.true",
                "select": "id,name,phone_number"
            }
        )

        if response.status_code != 200:
            print(f"   ❌ Could not fetch users: {response.status_code}")
            return False

        users = response.json()
        print(f"   ✅ Found {len(users)} active user(s)")
        print()

        if not users:
            print("   No active users found in this tenant.")
            return True

        # Display users
        for i, user in enumerate(users, 1):
            print(f"   {i}. {user['name']} ({user['phone_number']})")
        print()

        # Step 3: Check which users already have timesheet enabled
        print("3️⃣  Checking existing timesheet access...")
        user_ids = [user["id"] for user in users]

        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/user_skills",
            headers=headers,
            params={
                "user_id": f"in.({','.join(user_ids)})",
                "skill_id": f"eq.{skill_id}",
                "select": "user_id,is_enabled"
            }
        )

        existing_user_skills = {}
        if response.status_code == 200:
            for us in response.json():
                existing_user_skills[us["user_id"]] = us["is_enabled"]

        users_to_enable = []
        users_already_enabled = []
        users_to_update = []

        for user in users:
            user_id = user["id"]
            if user_id in existing_user_skills:
                if existing_user_skills[user_id]:
                    users_already_enabled.append(user)
                else:
                    users_to_update.append(user)
            else:
                users_to_enable.append(user)

        print(f"   • Already enabled: {len(users_already_enabled)}")
        print(f"   • Need to enable: {len(users_to_enable)}")
        print(f"   • Need to update: {len(users_to_update)}")
        print()

        # Step 4: Enable for new users
        if users_to_enable:
            print("4️⃣  Enabling timesheet for new users...")

            # Build insert records
            records = []
            for user in users_to_enable:
                records.append({
                    "user_id": user["id"],
                    "skill_id": skill_id,
                    "is_enabled": True
                })

            response = await client.post(
                f"{SUPABASE_URL}/rest/v1/user_skills",
                headers=headers,
                json=records
            )

            if response.status_code in (200, 201):
                print(f"   ✅ Enabled timesheet for {len(users_to_enable)} user(s)")
                for user in users_to_enable:
                    print(f"      • {user['name']}")
            else:
                print(f"   ❌ Failed to enable: {response.status_code}")
                print(f"   {response.text}")
            print()

        # Step 5: Update disabled users
        if users_to_update:
            print("5️⃣  Re-enabling timesheet for previously disabled users...")

            for user in users_to_update:
                response = await client.patch(
                    f"{SUPABASE_URL}/rest/v1/user_skills",
                    headers=headers,
                    params={
                        "user_id": f"eq.{user['id']}",
                        "skill_id": f"eq.{skill_id}"
                    },
                    json={"is_enabled": True}
                )

                if response.status_code == 204:
                    print(f"   ✅ Re-enabled for {user['name']}")
                else:
                    print(f"   ❌ Failed for {user['name']}: {response.status_code}")
            print()

        # Step 6: Summary
        print("=" * 70)
        print("✅ TIMESHEET SKILL ENABLED FOR TENANT")
        print("=" * 70)
        print()
        print(f"Tenant: Built by MK")
        print(f"Total users with timesheet access: {len(users)}")
        print()

        if users_already_enabled:
            print("Already had access:")
            for user in users_already_enabled:
                print(f"  • {user['name']} ({user['phone_number']})")
            print()

        if users_to_enable or users_to_update:
            print("Newly enabled:")
            for user in users_to_enable + users_to_update:
                print(f"  • {user['name']} ({user['phone_number']})")
            print()

        print("Users can now:")
        print("  1. Call the VAPI number from their registered phone")
        print("  2. Say 'timesheet' or 'log my time'")
        print("  3. Jill will help them log work hours at their sites")
        print()

        return True


if __name__ == "__main__":
    print()
    asyncio.run(enable_timesheet_for_tenant())
