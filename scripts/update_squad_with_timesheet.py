"""
Update VAPI Squad to include Timesheet Assistant

This script programmatically updates the JSMB-Jill-multi-skill-squad to add:
1. Timesheet assistant as a member
2. Routing from greeter to timesheet assistant
"""

import asyncio
import os
import sys
import httpx
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
SQUAD_NAME = "JSMB-Jill-multi-skill-squad"

# Known assistant IDs
GREETER_ID = "4300f282-35d2-4a06-9a67-f5b6d45e167f"
VOICE_NOTES_ID = "8a6f3781-5320-46bb-ad68-6451ee553e81"
SITE_PROGRESS_ID = "a88bdc5e-0ed4-410b-9e5a-b136072b22d7"
TIMESHEET_ID = "d3a5e1cf-82cb-4f6e-a406-b0170ede3d10"  # Just created


async def update_squad():
    """Update the squad configuration"""

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Step 1: Get existing squad
        print("1️⃣  Fetching existing squad...")
        response = await client.get("https://api.vapi.ai/squad", headers=headers)

        if response.status_code != 200:
            print(f"❌ Failed to fetch squads: {response.status_code}")
            return

        squads = response.json()
        squad = None

        for s in squads:
            if s.get('name') == SQUAD_NAME:
                squad = s
                break

        if not squad:
            print(f"❌ Squad '{SQUAD_NAME}' not found")
            return

        squad_id = squad['id']
        print(f"   ✅ Found: {squad['name']} ({squad_id})")
        print(f"   Current members: {len(squad['members'])}")

        # Step 2: Check if timesheet is already in squad
        existing_assistant_ids = []
        for member in squad['members']:
            aid = member.get('assistantId')
            if aid:
                existing_assistant_ids.append(aid)

        if TIMESHEET_ID in existing_assistant_ids:
            print(f"\n   ⚠️  Timesheet assistant already in squad")
            return

        # Step 3: Build updated squad configuration
        print(f"\n2️⃣  Building updated squad configuration...")

        # Update greeter's destinations to include timesheet
        updated_members = []

        for member in squad['members']:
            if member.get('assistantId') == GREETER_ID:
                # This is the greeter - add timesheet to destinations
                destinations = member.get('assistantDestinations', [])

                # Check if timesheet destination already exists
                has_timesheet = any(
                    d.get('assistantName') == 'JSMB-Jill-timesheet'
                    for d in destinations
                )

                if not has_timesheet:
                    destinations.append({
                        "message": "",
                        "type": "assistant",
                        "assistantName": "JSMB-Jill-timesheet"
                    })

                updated_members.append({
                    "assistantId": GREETER_ID,
                    "assistantDestinations": destinations
                })
                print(f"   ✅ Updated greeter with timesheet destination")
            else:
                updated_members.append(member)

        # Add timesheet assistant as a member
        updated_members.append({
            "assistantId": TIMESHEET_ID
        })
        print(f"   ✅ Added timesheet assistant as member")

        # Step 4: Update squad
        print(f"\n3️⃣  Updating squad in VAPI...")

        updated_squad = {
            "name": squad['name'],
            "members": updated_members
        }

        response = await client.patch(
            f"https://api.vapi.ai/squad/{squad_id}",
            headers=headers,
            json=updated_squad
        )

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Squad updated successfully")
            print(f"\n   Squad now has {len(result['members'])} members:")

            for i, member in enumerate(result['members'], 1):
                aid = member.get('assistantId')
                destinations = member.get('assistantDestinations', [])

                # Get assistant name
                assistant_response = await client.get(
                    f"https://api.vapi.ai/assistant/{aid}",
                    headers=headers
                )

                if assistant_response.status_code == 200:
                    assistant = assistant_response.json()
                    name = assistant.get('name', 'Unknown')
                    print(f"      {i}. {name} ({aid})")

                    if destinations:
                        print(f"         Can route to:")
                        for dest in destinations:
                            print(f"           → {dest.get('assistantName')}")
                else:
                    print(f"      {i}. {aid}")

        else:
            print(f"   ❌ Failed to update squad: {response.status_code}")
            print(f"   {response.text}")
            return

        # Step 5: Verification
        print(f"\n4️⃣  Verifying update...")

        response = await client.get(
            f"https://api.vapi.ai/squad/{squad_id}",
            headers=headers
        )

        if response.status_code == 200:
            verified_squad = response.json()
            timesheet_found = False

            for member in verified_squad['members']:
                if member.get('assistantId') == TIMESHEET_ID:
                    timesheet_found = True
                    break

            if timesheet_found:
                print(f"   ✅ Timesheet assistant confirmed in squad")
            else:
                print(f"   ⚠️  Timesheet assistant not found in updated squad")
        else:
            print(f"   ⚠️  Could not verify: {response.status_code}")

        print(f"\n" + "=" * 70)
        print(f"✅ SQUAD UPDATE COMPLETE")
        print(f"=" * 70)
        print(f"\nThe timesheet skill is now available through:")
        print(f"  • Phone: Call from +61412345678")
        print(f"  • Say: 'timesheet' or 'log my time'")
        print(f"  • Jill will seamlessly transfer to timesheet assistant")
        print()


if __name__ == "__main__":
    print()
    print("=" * 70)
    print("UPDATING VAPI SQUAD WITH TIMESHEET ASSISTANT")
    print("=" * 70)
    print()

    asyncio.run(update_squad())
