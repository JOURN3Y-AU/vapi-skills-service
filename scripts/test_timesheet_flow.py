"""
Test script for Timesheet skill endpoints

This script tests the timesheet skill workflow without needing a real VAPI call.
It simulates the VAPI request format to test the endpoints.
"""

import httpx
import asyncio
import json
from datetime import datetime
import pytz

# Base URL for local testing
BASE_URL = "http://localhost:8000"

# Test data
TEST_VAPI_CALL_ID = f"test_call_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
TEST_TOOL_CALL_ID = "test_tool_call_123"


def create_vapi_request(tool_name: str, arguments: dict) -> dict:
    """Create a VAPI-formatted request"""
    return {
        "message": {
            "call": {
                "id": TEST_VAPI_CALL_ID
            },
            "toolCalls": [{
                "id": TEST_TOOL_CALL_ID,
                "function": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }]
        }
    }


async def test_timesheet_flow():
    """Test the complete timesheet flow"""

    print("=" * 60)
    print("TIMESHEET SKILL FLOW TEST")
    print("=" * 60)
    print(f"Test Call ID: {TEST_VAPI_CALL_ID}\n")

    async with httpx.AsyncClient(timeout=30.0) as client:

        # Step 1: Authenticate (required for session context)
        print("\n1️⃣  AUTHENTICATION")
        print("-" * 60)

        auth_request = {
            "message": {
                "call": {
                    "id": TEST_VAPI_CALL_ID,
                    "customer": {
                        "number": "+61412345678"  # Test user
                    }
                },
                "toolCalls": [{
                    "id": TEST_TOOL_CALL_ID,
                    "function": {
                        "name": "authenticate_caller",
                        "arguments": {
                            "caller_phone": "+61412345678"
                        }
                    }
                }]
            }
        }

        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/vapi/authenticate-by-phone",
                json=auth_request
            )

            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                auth_result = result["results"][0]["result"]
                print(f"✅ Authenticated: {auth_result.get('user_name')}")
                print(f"   Available sites: {len(auth_result.get('available_sites', []))}")
            else:
                print(f"❌ Authentication failed: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return

        # Step 2: Identify Site
        print("\n2️⃣  SITE IDENTIFICATION")
        print("-" * 60)

        site_request = create_vapi_request(
            "identify_site_for_timesheet",
            {
                "site_description": "Ocean White House",
                "vapi_call_id": TEST_VAPI_CALL_ID
            }
        )

        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/skills/timesheet/identify-site",
                json=site_request
            )

            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                site_result = result["results"][0]["result"]

                if site_result.get("site_identified"):
                    site_id = site_result["site_id"]
                    site_name = site_result["site_name"]
                    print(f"✅ Site identified: {site_name}")
                    print(f"   Site ID: {site_id}")
                else:
                    print(f"❌ Site not identified")
                    print(f"   Message: {site_result.get('message')}")
                    return
            else:
                print(f"❌ Site identification failed: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return

        # Step 3: Save Timesheet Entry
        print("\n3️⃣  SAVE TIMESHEET ENTRY")
        print("-" * 60)

        entry_request = create_vapi_request(
            "save_timesheet_entry",
            {
                "site_id": site_id,
                "start_time": "07:30",
                "end_time": "15:45",
                "work_description": "Installed roof trusses and completed framing on the northern wing",
                "plans_for_tomorrow": "Start roofing installation",
                "vapi_call_id": TEST_VAPI_CALL_ID
            }
        )

        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/skills/timesheet/save-entry",
                json=entry_request
            )

            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                entry_result = result["results"][0]["result"]

                if entry_result.get("success"):
                    print(f"✅ Entry saved")
                    print(f"   Entry ID: {entry_result.get('entry_id')}")
                    print(f"   Hours worked: {entry_result.get('hours_worked')}")
                    print(f"   Message: {entry_result.get('message')}")
                else:
                    print(f"❌ Failed to save entry")
                    print(f"   Error: {entry_result.get('error')}")
                    return
            else:
                print(f"❌ Save failed: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return

        # Step 4: Confirm All Entries
        print("\n4️⃣  CONFIRM ALL ENTRIES")
        print("-" * 60)

        confirm_request = create_vapi_request(
            "confirm_and_save_all",
            {
                "vapi_call_id": TEST_VAPI_CALL_ID,
                "user_confirmed": True
            }
        )

        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/skills/timesheet/confirm-all",
                json=confirm_request
            )

            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                confirm_result = result["results"][0]["result"]

                if confirm_result.get("success"):
                    print(f"✅ Confirmed")
                    print(f"   Total entries: {confirm_result.get('total_entries')}")
                    print(f"   Total hours: {confirm_result.get('total_hours')}")
                    print(f"   Message: {confirm_result.get('message')}")
                else:
                    print(f"❌ Confirmation failed")
            else:
                print(f"❌ Confirm failed: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return

        print("\n" + "=" * 60)
        print("✅ TIMESHEET FLOW TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)


async def test_authentication():
    """Quick test of authentication endpoint"""
    print("\n🔐 Testing Authentication...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        auth_request = {
            "message": {
                "call": {
                    "id": "quick_test_call",
                    "customer": {"number": "+61412345678"}
                },
                "toolCalls": [{
                    "id": "quick_test_tool",
                    "function": {
                        "name": "authenticate_caller",
                        "arguments": {"caller_phone": "+61412345678"}
                    }
                }]
            }
        }

        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/vapi/authenticate-by-phone",
                json=auth_request
            )

            if response.status_code == 200:
                result = response.json()["results"][0]["result"]
                print(f"✅ User: {result.get('user_name')}")

                skills = result.get('available_skills', [])
                print(f"✅ Available skills: {len(skills)}")
                for skill in skills:
                    print(f"   • {skill.get('skill_name')} ({skill.get('skill_key')})")

                return True
            else:
                print(f"❌ Auth failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("STARTING TESTS")
    print("=" * 60)
    print(f"Server: {BASE_URL}")
    print(f"Make sure the server is running: uvicorn app.main:app --reload")
    print("=" * 60)

    # Quick auth test first
    auth_ok = asyncio.run(test_authentication())

    if auth_ok:
        print("\n" + "=" * 60)
        input("Press ENTER to continue with full timesheet flow test...")
        asyncio.run(test_timesheet_flow())
    else:
        print("\n❌ Authentication test failed. Make sure:")
        print("   1. Server is running")
        print("   2. Database is accessible")
        print("   3. Test user exists (+61412345678)")
        print("   4. Timesheet skill is enabled for test user")
