#!/usr/bin/env python3
"""
Create Overhead Site for Tenant

Creates a generic "Overheads" site entity for any tenant to allow users
to log timesheet entries for non-site-specific work like admin, general
duties, paperwork, etc.

The site name follows the pattern: "{TenantName} - Overheads"

Usage:
    python scripts/create_overhead_site.py <tenant_name>
    python scripts/create_overhead_site.py "Built By MK Prod"
    python scripts/create_overhead_site.py "JOURN3Y"
"""

import httpx
import json
import uuid
import sys
from datetime import datetime
from pathlib import Path

# Load environment variables
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings


async def create_overhead_site(tenant_name: str):
    """Create overhead site for the specified tenant"""

    print("=" * 70)
    print("Creating Overhead Site Entity")
    print("=" * 70)
    print()

    # Find the tenant
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/tenants",
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
            },
            params={
                "name": f"eq.{tenant_name}",
                "select": "id,name,timezone"
            }
        )

        if response.status_code != 200 or not response.json():
            print(f"❌ ERROR: Tenant '{tenant_name}' not found!")
            print()
            print("Available tenants:")
            # Get all tenants
            all_response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/tenants",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                },
                params={"select": "name"}
            )
            for t in all_response.json():
                print(f"  - {t['name']}")
            return None

        tenant = response.json()[0]
        tenant_id = tenant['id']
        tenant_name = tenant['name']

        print(f"Tenant: {tenant_name}")
        print(f"ID: {tenant_id}")
        print(f"Timezone: {tenant.get('timezone', 'Not set')}")
        print()

        # Check if overhead site already exists
        print("Checking for existing overhead site...")
        response = await client.get(
            f"{settings.SUPABASE_URL}/rest/v1/entities",
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
            },
            params={
                "tenant_id": f"eq.{tenant_id}",
                "entity_type": "eq.sites",
                "select": "id,name,metadata"
            }
        )

        existing_sites = response.json()
        overhead_site = None
        for site in existing_sites:
            metadata = site.get('metadata', {})
            if isinstance(metadata, dict) and metadata.get('is_overhead') == True:
                overhead_site = site
                break

        if overhead_site:
            print(f"✓ Overhead site already exists!")
            print(f"  ID: {overhead_site['id']}")
            print(f"  Name: {overhead_site['name']}")
            print()

            # Check if name needs updating to new convention
            expected_name = f"{tenant_name} - Overheads"
            if overhead_site['name'] != expected_name:
                print(f"⚠️  Name doesn't match convention: '{expected_name}'")
                print(f"   Current name: '{overhead_site['name']}'")
                print()
                print("Would you like to update it? (This is cosmetic only)")
            else:
                print("✅ Name follows convention. No action needed.")

            return overhead_site

        # Create the new overhead site
        site_name = f"{tenant_name} - Overheads"
        site_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "entity_type": "sites",
            "name": site_name,
            "address": None,
            "metadata": {
                "is_overhead": True,
                "description": "Admin, general duties, and non-site-specific work",
                "keywords": ["admin", "overheads", "office", "general", "paperwork", "overhead", "administration"],
                "created_by": "script:create_overhead_site",
                "created_at": datetime.utcnow().isoformat()
            }
        }

        print(f"Creating overhead site: '{site_name}'")
        print()

        response = await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/entities",
            headers={
                "apikey": settings.SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            json=site_data
        )

        if response.status_code == 201:
            created = response.json()[0]
            print("✅ SUCCESS! Overhead site created!")
            print(f"  ID: {created['id']}")
            print(f"  Name: {created['name']}")
            print()

            # Verify it appears in sites list
            print("Verifying site appears in tenant's sites list...")
            response = await client.get(
                f"{settings.SUPABASE_URL}/rest/v1/entities",
                headers={
                    "apikey": settings.SUPABASE_SERVICE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}"
                },
                params={
                    "tenant_id": f"eq.{tenant_id}",
                    "entity_type": "eq.sites",
                    "select": "id,name,metadata"
                }
            )

            all_sites = response.json()
            print(f"✓ Total sites for {tenant_name}: {len(all_sites)}")
            for site in all_sites:
                metadata = site.get('metadata', {})
                is_overhead = isinstance(metadata, dict) and metadata.get('is_overhead') == True
                marker = "⭐" if is_overhead else "  "
                print(f"  {marker} {site['name']}")

            print()
            print("=" * 70)
            print("✅ Overhead site is ready to use!")
            print("=" * 70)
            print()
            print("Users can now say phrases like:")
            print("  - 'I did admin work today'")
            print("  - 'I was doing overheads'")
            print("  - 'Office work'")
            print("  - 'General duties'")
            print()
            print("The backend will automatically find this overhead site.")

            return created
        else:
            print(f"❌ ERROR: Failed to create site")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            raise Exception(f"Failed to create overhead site: {response.text}")


if __name__ == "__main__":
    import asyncio

    if len(sys.argv) < 2:
        print("Usage: python scripts/create_overhead_site.py <tenant_name>")
        print()
        print("Examples:")
        print("  python scripts/create_overhead_site.py \"Built By MK Prod\"")
        print("  python scripts/create_overhead_site.py \"JOURN3Y\"")
        sys.exit(1)

    tenant_name = sys.argv[1]
    asyncio.run(create_overhead_site(tenant_name))
