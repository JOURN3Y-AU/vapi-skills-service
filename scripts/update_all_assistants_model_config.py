"""
Update all VAPI assistants with optimized model configurations

This script updates the model configuration (LLM model, temperature, maxTokens)
for all VAPI assistants to use cost-optimized settings.

Changes:
- Greeter: Already using gpt-4o-mini (no change needed)
- Timesheet: gpt-4 → gpt-4o-mini + maxTokens: 1200
- Voice Notes: gpt-4 → gpt-4o-mini + maxTokens: 1200
- Site Progress: gpt-4o → gpt-4o-mini + maxTokens: 1500
"""

import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.assistants.greeter import GreeterAssistant
from app.assistants.timesheet import TimesheetAssistant
from app.assistants.jill_voice_notes import JillVoiceNotesAssistant
from app.assistants.site_progress import SiteProgressAssistant

VAPI_API_KEY = os.getenv("VAPI_API_KEY")

# VAPI Assistant IDs (from your existing scripts)
ASSISTANT_IDS = {
    "greeter": "4300f282-35d2-4a06-9a67-f5b6d45e167f",
    "timesheet": "d3a5e1cf-82cb-4f6e-a406-b0170ede3d10",
    "voice_notes": None,  # Will be fetched dynamically
    "site_progress": None  # Will be fetched dynamically
}


async def find_assistant_id(client, headers, name_pattern):
    """Find assistant ID by name pattern"""
    response = await client.get(
        "https://api.vapi.ai/assistant",
        headers=headers
    )

    if response.status_code == 200:
        assistants = response.json()
        for assistant in assistants:
            if name_pattern.lower() in assistant.get('name', '').lower():
                return assistant['id']
    return None


async def update_assistant_model(client, headers, assistant_id, assistant_name, assistant_obj):
    """Update a single assistant's model configuration"""

    print(f"\n{'='*70}")
    print(f"UPDATING {assistant_name.upper()}")
    print(f"{'='*70}")

    # Step 1: Get current configuration
    print(f"\n1️⃣  Fetching current configuration...")
    response = await client.get(
        f"https://api.vapi.ai/assistant/{assistant_id}",
        headers=headers
    )

    if response.status_code != 200:
        print(f"   ❌ Failed to fetch assistant: {response.status_code}")
        return False

    current_config = response.json()
    print(f"   ✅ Found: {current_config.get('name')}")

    # Step 2: Get updated model config from code
    print(f"\n2️⃣  Getting optimized model configuration...")
    new_model_config = assistant_obj.get_model_config()
    new_prompt = assistant_obj.get_system_prompt()
    new_first_message = assistant_obj.get_first_message()

    print(f"   📊 New model settings:")
    print(f"      • Model: {new_model_config.get('model')}")
    print(f"      • Temperature: {new_model_config.get('temperature')}")
    print(f"      • Max Tokens: {new_model_config.get('maxTokens', 'Not set')}")

    # Step 3: Build update payload
    print(f"\n3️⃣  Building update payload...")

    # Update the model configuration
    current_model = current_config.get('model', {})

    # Update messages with new system prompt
    messages = [
        {
            "role": "system",
            "content": new_prompt
        }
    ]

    # Merge new model config with existing settings
    updated_model = {
        **current_model,
        "provider": new_model_config.get("provider"),
        "model": new_model_config.get("model"),
        "temperature": new_model_config.get("temperature"),
        "messages": messages
    }

    # Add maxTokens if specified
    if "maxTokens" in new_model_config:
        updated_model["maxTokens"] = new_model_config["maxTokens"]

    # Preserve tool IDs
    if "toolIds" in current_model:
        updated_model["toolIds"] = current_model["toolIds"]

    update_payload = {
        "name": current_config.get('name'),
        "model": updated_model,
        "voice": current_config.get('voice'),
        "firstMessage": new_first_message if new_first_message else current_config.get('firstMessage'),
        "firstMessageMode": current_config.get('firstMessageMode')
    }

    # Preserve optional fields
    if 'server' in current_config:
        update_payload['server'] = current_config['server']
    if 'serverMessages' in current_config:
        update_payload['serverMessages'] = current_config['serverMessages']

    print("   ✅ Payload prepared")

    # Step 4: Update the assistant
    print(f"\n4️⃣  Updating assistant in VAPI...")

    response = await client.patch(
        f"https://api.vapi.ai/assistant/{assistant_id}",
        headers=headers,
        json=update_payload
    )

    if response.status_code == 200:
        print("   ✅ Assistant updated successfully")

        # Verify the update
        print(f"\n5️⃣  Verifying update...")
        verify_response = await client.get(
            f"https://api.vapi.ai/assistant/{assistant_id}",
            headers=headers
        )

        if verify_response.status_code == 200:
            verified = verify_response.json()
            verified_model = verified.get('model', {})

            print(f"   ✅ Verified settings:")
            print(f"      • Model: {verified_model.get('model')}")
            print(f"      • Temperature: {verified_model.get('temperature')}")
            print(f"      • Max Tokens: {verified_model.get('maxTokens', 'Not set')}")

            return True
        else:
            print(f"   ⚠️  Could not verify: {verify_response.status_code}")
            return True  # Update succeeded even if verification failed
    else:
        print(f"   ❌ Failed to update: {response.status_code}")
        print(f"   {response.text}")
        return False


async def main():
    """Update all assistants with optimized model configurations"""

    print("=" * 70)
    print("UPDATING ALL VAPI ASSISTANTS WITH OPTIMIZED MODEL CONFIGS")
    print("=" * 70)
    print()
    print("This will update:")
    print("  • Greeter: Already optimized (will verify)")
    print("  • Timesheet: gpt-4 → gpt-4o-mini + maxTokens")
    print("  • Voice Notes: gpt-4 → gpt-4o-mini + maxTokens")
    print("  • Site Progress: gpt-4o → gpt-4o-mini + maxTokens")
    print()

    if not VAPI_API_KEY:
        print("❌ VAPI_API_KEY not found in environment")
        return

    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        # Find missing assistant IDs
        print("🔍 Finding assistant IDs...")
        if not ASSISTANT_IDS["voice_notes"]:
            voice_notes_id = await find_assistant_id(client, headers, "jill-voice-notes")
            if voice_notes_id:
                ASSISTANT_IDS["voice_notes"] = voice_notes_id
                print(f"   ✅ Found Voice Notes: {voice_notes_id}")
            else:
                print(f"   ⚠️  Voice Notes assistant not found")

        if not ASSISTANT_IDS["site_progress"]:
            site_progress_id = await find_assistant_id(client, headers, "site-progress")
            if site_progress_id:
                ASSISTANT_IDS["site_progress"] = site_progress_id
                print(f"   ✅ Found Site Progress: {site_progress_id}")
            else:
                print(f"   ⚠️  Site Progress assistant not found")

        # Update each assistant
        results = {}

        # 1. Greeter
        if ASSISTANT_IDS["greeter"]:
            results["greeter"] = await update_assistant_model(
                client, headers,
                ASSISTANT_IDS["greeter"],
                "Greeter",
                GreeterAssistant()
            )

        # 2. Timesheet
        if ASSISTANT_IDS["timesheet"]:
            results["timesheet"] = await update_assistant_model(
                client, headers,
                ASSISTANT_IDS["timesheet"],
                "Timesheet",
                TimesheetAssistant()
            )

        # 3. Voice Notes
        if ASSISTANT_IDS["voice_notes"]:
            results["voice_notes"] = await update_assistant_model(
                client, headers,
                ASSISTANT_IDS["voice_notes"],
                "Voice Notes",
                JillVoiceNotesAssistant()
            )

        # 4. Site Progress
        if ASSISTANT_IDS["site_progress"]:
            results["site_progress"] = await update_assistant_model(
                client, headers,
                ASSISTANT_IDS["site_progress"],
                "Site Progress",
                SiteProgressAssistant()
            )

        # Summary
        print("\n" + "=" * 70)
        print("UPDATE SUMMARY")
        print("=" * 70)
        print()

        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)

        for name, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {name.replace('_', ' ').title()}")

        print()
        print(f"Updated {success_count}/{total_count} assistants successfully")
        print()
        print("=" * 70)
        print("EXPECTED COST SAVINGS")
        print("=" * 70)
        print()
        print("Before optimization: ~$0.50 LLM costs per call")
        print("After optimization:  ~$0.05 LLM costs per call")
        print()
        print("💰 Expected savings: ~90% reduction in LLM costs")
        print("💰 Overall call cost: $0.65 → $0.13-0.20 per call")
        print()
        print("Next steps:")
        print("  1. Test a call to verify functionality")
        print("  2. Check VAPI dashboard for cost per minute")
        print("  3. Monitor token usage to ensure maxTokens is appropriate")
        print()


if __name__ == "__main__":
    asyncio.run(main())
