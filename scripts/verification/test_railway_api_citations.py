#!/usr/bin/env python3
"""
Test that Railway API returns references and key_evidence fields.

This script submits a new fact-check job and verifies the response
includes the full citation data.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.clients.fact_check_client import FactCheckAPIClient


async def test_railway_api():
    """Test Railway API response structure."""
    
    print("\n" + "="*80)
    print("TESTING RAILWAY API - REFERENCES AND KEY_EVIDENCE")
    print("="*80 + "\n")
    
    # Test URL - using a simple, short article for fast testing
    test_url = "https://www.foxnews.com/politics/james-carville-says-hed-find-convicted-pedophile-run-against-trump"
    
    print(f"📤 Submitting fact-check job for test article...")
    print(f"   URL: {test_url}\n")
    
    async with FactCheckAPIClient() as client:
        # Submit job
        try:
            submit_result = await client.submit_fact_check(
                url=test_url,
                mode="iterative",
                generate_article=True,
                generate_image=False
            )
            
            job_id = submit_result.get("job_id")
            print(f"✅ Job submitted successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Estimated time: {submit_result.get('estimated_time_seconds')}s\n")
            
        except Exception as e:
            print(f"❌ Failed to submit job: {e}")
            return
        
        # Poll for completion
        print(f"⏳ Polling for job completion (max 10 minutes)...\n")
        
        max_attempts = 120  # 10 minutes with 5s intervals
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status = await client.get_job_status(job_id)
                current_status = status.get("status")
                progress = status.get("progress", 0)
                
                if current_status == "finished":
                    print(f"\n✅ Job completed successfully!\n")
                    
                    # Fetch result
                    result = await client.get_job_result(job_id)
                    
                    # Check validation_results structure
                    validation_results = result.get("validation_results", [])
                    
                    if not validation_results:
                        print("❌ No validation_results in response")
                        return
                    
                    print("="*80)
                    print("CHECKING RESPONSE STRUCTURE")
                    print("="*80 + "\n")
                    
                    if isinstance(validation_results, list) and validation_results:
                        first_result = validation_results[0]
                        val_result = first_result.get("validation_result", {})
                        
                        print(f"📋 validation_result keys: {list(val_result.keys())}\n")
                        
                        # Check for references
                        if "references" in val_result:
                            references = val_result["references"]
                            print(f"✅ FOUND 'references' field!")
                            print(f"   Number of references: {len(references)}")
                            if references:
                                print(f"\n   First reference:")
                                print(f"   {json.dumps(references[0], indent=6)}")
                        else:
                            print(f"❌ NO 'references' field found")
                        
                        print()
                        
                        # Check for key_evidence
                        if "key_evidence" in val_result:
                            key_evidence = val_result["key_evidence"]
                            print(f"✅ FOUND 'key_evidence' field!")
                            print(f"   Evidence categories: {list(key_evidence.keys())}")
                            print(f"\n   Key evidence structure:")
                            print(f"   {json.dumps(key_evidence, indent=6)}")
                        else:
                            print(f"❌ NO 'key_evidence' field found")
                        
                        print("\n" + "="*80)
                        
                        if "references" in val_result and "key_evidence" in val_result:
                            print("🎉 SUCCESS! Railway API is returning full citation data!")
                        else:
                            print("⚠️  INCOMPLETE! Railway API still missing some fields.")
                        
                        print("="*80 + "\n")
                    
                    return
                    
                elif current_status == "failed":
                    error_msg = status.get("error_message", "Unknown error")
                    print(f"\n❌ Job failed: {error_msg}\n")
                    return
                
                # Still processing
                if attempt % 6 == 0:  # Print every 30 seconds
                    print(f"   [{attempt*5}s] Status: {current_status}, Progress: {progress}%")
                
                await asyncio.sleep(5)
                attempt += 1
                
            except Exception as e:
                print(f"\n❌ Error polling job: {e}\n")
                return
        
        print(f"\n⏰ Job timed out after {max_attempts * 5} seconds\n")


async def main():
    """Entry point."""
    try:
        await test_railway_api()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
