"""
Apply the timesheets table migration to Supabase

This script reads the migration file and applies it to your Supabase database.
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


async def apply_migration():
    """Apply the timesheets table migration"""

    print("=" * 70)
    print("APPLYING TIMESHEETS TABLE MIGRATION")
    print("=" * 70)
    print()

    # Read migration file
    migration_file = "migrations/003_create_timesheets.sql"
    print(f"1️⃣  Reading migration file: {migration_file}")

    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        print(f"   ✅ Read {len(migration_sql)} characters")
    except FileNotFoundError:
        print(f"   ❌ Migration file not found: {migration_file}")
        return False

    print()
    print("2️⃣  Applying migration to Supabase...")
    print()

    # Split SQL into individual statements
    statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }

        success_count = 0
        error_count = 0

        for i, statement in enumerate(statements, 1):
            # Skip empty statements and comments
            if not statement or statement.startswith('--'):
                continue

            # Show what we're executing (first 100 chars)
            preview = statement[:100].replace('\n', ' ')
            if len(statement) > 100:
                preview += "..."

            print(f"   [{i}/{len(statements)}] {preview}")

            try:
                # Execute via Supabase PostgREST (SQL function)
                # Note: This uses the pg_stat_statements extension
                # For direct SQL execution, we need to use the database URL

                # Alternative: Use psycopg2 or execute via Supabase SQL Editor
                # For now, we'll provide instructions

                print(f"        ⏳ Would execute...")
                success_count += 1

            except Exception as e:
                print(f"        ❌ Error: {e}")
                error_count += 1

        print()
        print("=" * 70)
        print("⚠️  MANUAL MIGRATION REQUIRED")
        print("=" * 70)
        print()
        print("Unfortunately, Supabase PostgREST API doesn't support direct SQL execution.")
        print("You need to apply the migration manually via Supabase Dashboard.")
        print()
        print("Here's how:")
        print()
        print("1. Go to your Supabase Dashboard:")
        print(f"   {SUPABASE_URL.replace('/rest/v1', '')}")
        print()
        print("2. Navigate to: SQL Editor (left sidebar)")
        print()
        print("3. Click 'New Query'")
        print()
        print("4. Copy and paste this SQL:")
        print()
        print("-" * 70)
        print(migration_sql)
        print("-" * 70)
        print()
        print("5. Click 'Run' or press Cmd/Ctrl + Enter")
        print()
        print("6. Verify the table was created:")
        print("   - Go to 'Table Editor'")
        print("   - Look for 'timesheets' table")
        print()

        # Check if table exists
        print("3️⃣  Checking if timesheets table exists...")
        try:
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/timesheets",
                headers=headers,
                params={"limit": "1"}
            )

            if response.status_code == 200:
                print("   ✅ Timesheets table exists!")
                print()
                print("   The migration has already been applied.")
                print()
                return True
            elif response.status_code == 404 or "relation" in response.text.lower():
                print("   ❌ Timesheets table does NOT exist")
                print()
                print("   Please apply the migration using the instructions above.")
                print()
                return False
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
                print(f"   {response.text}")
                print()
                return False

        except Exception as e:
            print(f"   ⚠️  Could not check table existence: {e}")
            print()
            return False


if __name__ == "__main__":
    print()
    result = asyncio.run(apply_migration())

    if not result:
        print()
        print("=" * 70)
        print("QUICK COPY-PASTE FOR SUPABASE SQL EDITOR")
        print("=" * 70)
        print()

        # Read and display the migration for easy copy-paste
        try:
            with open("migrations/003_create_timesheets.sql", 'r') as f:
                print(f.read())
        except:
            pass

        print()
        print("=" * 70)
        print()
