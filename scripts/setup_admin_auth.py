#!/usr/bin/env python3
"""
Setup Admin Authentication System

This script:
1. Creates admin_users and admin_user_permissions tables
2. Creates initial super_admin user (kevin.morrell@journ3y.com.au)
3. Optionally creates tenant_admin user for Built by MK

Usage:
    python scripts/setup_admin_auth.py
"""

import os
import sys
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
import bcrypt

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


async def run_sql_file(sql_file_path: str):
    """Execute SQL file via Supabase"""
    print(f"📄 Reading SQL file: {sql_file_path}")

    with open(sql_file_path, 'r') as f:
        sql_content = f.read()

    # Split into individual statements (basic splitting by semicolon)
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, statement in enumerate(statements, 1):
            # Skip comments and empty statements
            if not statement or statement.startswith('--') or statement.startswith('/*'):
                continue

            print(f"  Executing statement {i}/{len(statements)}...")

            try:
                # Use Supabase SQL endpoint (if available) or PostgREST
                # Note: This is a simplified approach. In production, use a proper migration tool.
                response = await client.post(
                    f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                    headers={
                        "apikey": SUPABASE_SERVICE_KEY,
                        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={"query": statement}
                )

                if response.status_code not in [200, 201, 204]:
                    # Some statements might fail if objects already exist, that's ok
                    print(f"  ⚠️  Statement {i} returned {response.status_code}: {response.text[:100]}")
            except Exception as e:
                print(f"  ⚠️  Statement {i} error: {str(e)[:100]}")

    print("✅ SQL migration completed (check warnings above)")


async def create_admin_user(username: str, password: str, email: str, role: str, tenant_id: str = None):
    """Create an admin user"""
    password_hash = hash_password(password)

    user_data = {
        "username": username,
        "password_hash": password_hash,
        "email": email,
        "role": role,
        "is_active": True
    }

    if tenant_id:
        user_data["tenant_id"] = tenant_id

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/admin_users",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json=user_data
        )

        if response.status_code == 201:
            created_user = response.json()[0]
            print(f"✅ Created admin user: {username} (role: {role})")
            return created_user
        elif response.status_code == 409:
            print(f"⚠️  User {username} already exists")
            return None
        else:
            print(f"❌ Failed to create user {username}: {response.status_code} - {response.text}")
            return None


async def add_permission(admin_user_id: str, permission_type: str):
    """Add a permission to an admin user"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SUPABASE_URL}/rest/v1/admin_user_permissions",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            },
            json={
                "admin_user_id": admin_user_id,
                "permission_type": permission_type
            }
        )

        if response.status_code == 201:
            print(f"  ✅ Added permission: {permission_type}")
            return True
        elif response.status_code == 409:
            print(f"  ⚠️  Permission {permission_type} already exists")
            return True
        else:
            print(f"  ❌ Failed to add permission {permission_type}: {response.text}")
            return False


async def get_tenant_id_by_name(tenant_name: str):
    """Get tenant ID by name"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/rest/v1/tenants",
            headers={
                "apikey": SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
            },
            params={
                "name": f"ilike.{tenant_name}",
                "select": "id,name"
            }
        )

        if response.status_code == 200:
            tenants = response.json()
            if tenants:
                return tenants[0]["id"]

        return None


async def main():
    print("=" * 60)
    print("ADMIN AUTHENTICATION SYSTEM SETUP")
    print("=" * 60)
    print()

    # Step 1: Run SQL migration
    print("Step 1: Creating database tables...")
    sql_file = Path(__file__).parent / "create_admin_auth_tables.sql"

    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        sys.exit(1)

    # Note: Since Supabase doesn't have a direct SQL execution endpoint via REST,
    # we'll create the tables manually using the PostgREST API
    print("⚠️  Note: You may need to run the SQL file manually in Supabase SQL Editor")
    print(f"   File location: {sql_file}")
    print()
    input("Press Enter after running the SQL file in Supabase, or Ctrl+C to exit...")
    print()

    # Step 2: Create super admin user
    print("Step 2: Creating super admin user...")
    super_admin = await create_admin_user(
        username="kevin.morrell@journ3y.com.au",
        password="testing",
        email="kevin.morrell@journ3y.com.au",
        role="super_admin",
        tenant_id=None
    )
    print()

    # Step 3: Create Built by MK tenant admin (optional)
    print("Step 3: Creating Built by MK tenant admin...")
    create_bmk = input("Create Built by MK tenant admin? (y/n): ").lower().strip()

    if create_bmk == 'y':
        # Get Built by MK tenant ID
        bmk_tenant_id = await get_tenant_id_by_name("Built by MK")

        if not bmk_tenant_id:
            print("❌ Could not find 'Built by MK' tenant")
        else:
            print(f"Found Built by MK tenant: {bmk_tenant_id}")

            # Generate temporary password
            temp_password = "ChangeMe2025!"
            print(f"⚠️  Temporary password: {temp_password}")

            bmk_admin = await create_admin_user(
                username="jake@builtbymk.com.au",
                password=temp_password,
                email="jake@builtbymk.com.au",
                role="tenant_admin",
                tenant_id=bmk_tenant_id
            )

            if bmk_admin:
                print("Adding permissions...")
                await add_permission(bmk_admin["id"], "view_timesheets")
                await add_permission(bmk_admin["id"], "manage_users")
                await add_permission(bmk_admin["id"], "view_reports")

    print()
    print("=" * 60)
    print("✅ SETUP COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Test login at http://localhost:8000/admin/login")
    print("2. Super admin: kevin.morrell@journ3y.com.au / testing")
    if create_bmk == 'y':
        print(f"3. Built by MK admin: jake@builtbymk.com.au / {temp_password}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
