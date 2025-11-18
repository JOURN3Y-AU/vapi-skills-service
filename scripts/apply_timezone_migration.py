"""
Apply timezone and timesheet indexes migration

This script checks if the timezone column exists and provides instructions
for applying the migration in Supabase.
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


async def check_migration_status():
    """Check if the migration has been applied"""

    print("=" * 70)
    print("CHECKING TIMEZONE MIGRATION STATUS")
    print("=" * 70)
    print()

    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    }

    async with httpx.AsyncClient() as client:
        # Check if timezone column exists by trying to select it
        print("1️⃣  Checking if timezone column exists in tenants table...")
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/tenants",
            headers=headers,
            params={
                "select": "id,timezone",
                "limit": "1"
            }
        )

        if response.status_code == 200:
            print("   ✅ Timezone column EXISTS")

            # Check if Built by MK tenant has timezone set
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/tenants",
                headers=headers,
                params={
                    "id": "eq.ba920f42-43df-44b5-a2e8-f740764a56d5",
                    "select": "name,timezone"
                }
            )

            if response.status_code == 200 and response.json():
                tenant = response.json()[0]
                print(f"   ✅ Built by MK timezone: {tenant.get('timezone', 'NOT SET')}")

            print()
            print("✅ Migration has been applied!")
            print()
            return True

        else:
            print("   ❌ Timezone column does NOT exist")
            print()
            print("📋 TO APPLY THE MIGRATION:")
            print()
            print("1. Go to your Supabase Dashboard")
            print("2. Click 'SQL Editor' in the left sidebar")
            print("3. Click 'New Query'")
            print("4. Copy and paste the SQL below")
            print("5. Click 'Run' (or press Cmd/Ctrl + Enter)")
            print()
            print("=" * 70)
            print("SQL TO RUN:")
            print("=" * 70)
            print()

            # Read and print the migration file
            migration_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "migrations",
                "004_add_timezone_and_timesheet_indexes.sql"
            )

            try:
                with open(migration_path, 'r') as f:
                    sql = f.read()
                    print(sql)
            except FileNotFoundError:
                print("❌ Migration file not found!")
                print(f"   Looking for: {migration_path}")

            print()
            print("=" * 70)
            print()
            return False


if __name__ == "__main__":
    print()
    result = asyncio.run(check_migration_status())

    if result:
        print("🎉 You're all set! The timezone column is ready.")
        print()
        print("Next steps:")
        print("  1. Deploy code to Railway")
        print("  2. Create new VAPI tools")
        print("  3. Test historical timesheet logging")
    else:
        print("⚠️  Please apply the migration in Supabase SQL Editor")
        print("   Then run this script again to verify.")
    print()
