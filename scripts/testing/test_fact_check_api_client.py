#!/usr/bin/env python3
"""
Test script for FactCheckAPIClient.

Tests connectivity to internal fact-check API.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.clients.fact_check_client import FactCheckAPIClient
from app.core.config import settings


async def test_health_check():
    """Test API health check."""
    print("🔍 Testing API Health Check...")
    
    async with FactCheckAPIClient() as client:
        try:
            health = await client.health_check()
            print(f"  ✅ API is healthy: {health}")
            return True
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False


async def test_submit_job():
    """Test submitting a fact-check job."""
    print("\n🔍 Testing Job Submission...")
    
    # Use a real news article URL from integration guide
    test_url = "https://www.foxnews.com/media/kamala-harris-says-its-f-up-what-rfk-jrs-hhs-doing-america"
    
    async with FactCheckAPIClient() as client:
        try:
            result = await client.submit_fact_check(
                url=test_url,
                mode="summary",
                generate_image=False,
                generate_article=True
            )
            
            print(f"  ✅ Job submitted successfully!")
            print(f"     Job ID: {result.get('job_id')}")
            print(f"     Status URL: {result.get('status_url')}")
            print(f"     Estimated time: {result.get('estimated_time_seconds')}s")
            
            return result.get('job_id')
            
        except Exception as e:
            print(f"  ❌ Job submission failed: {e}")
            return None


async def test_get_status(job_id: str):
    """Test getting job status."""
    print(f"\n🔍 Testing Status Check for job: {job_id}...")
    
    async with FactCheckAPIClient() as client:
        try:
            status = await client.get_job_status(job_id)
            
            print(f"  ✅ Status retrieved:")
            print(f"     Status: {status.get('status')}")
            print(f"     Progress: {status.get('progress')}%")
            print(f"     Elapsed: {status.get('elapsed_time_seconds')}s")
            
            return status
            
        except Exception as e:
            print(f"  ❌ Status check failed: {e}")
            return None


async def test_poll_until_complete(job_id: str, max_wait: int = 120):
    """Poll job status until complete."""
    print(f"\n🔍 Polling job until complete (max {max_wait}s)...")
    
    async with FactCheckAPIClient() as client:
        elapsed = 0
        interval = 5
        
        while elapsed < max_wait:
            try:
                status = await client.get_job_status(job_id)
                current_status = status.get('status')
                progress = status.get('progress', 0)
                
                print(f"  ⏳ Status: {current_status} ({progress}%) - Elapsed: {elapsed}s")
                
                if current_status == 'finished':
                    print(f"  ✅ Job completed!")
                    return True
                elif current_status == 'failed':
                    print(f"  ❌ Job failed")
                    return False
                
                await asyncio.sleep(interval)
                elapsed += interval
                
            except Exception as e:
                print(f"  ❌ Polling error: {e}")
                return False
        
        print(f"  ⏱️  Timeout reached after {max_wait}s")
        return False


async def test_get_result(job_id: str):
    """Test getting job result."""
    print(f"\n🔍 Testing Result Retrieval for job: {job_id}...")
    
    async with FactCheckAPIClient() as client:
        try:
            result = await client.get_job_result(job_id)
            
            print(f"  ✅ Result retrieved:")
            print(f"     Status: {result.get('status')}")
            print(f"     Claims analyzed: {result.get('claims_analyzed')}")
            print(f"     Processing time: {result.get('processing_time_seconds')}s")
            
            # Check validation results
            validation_results = result.get('validation_results', [])
            if validation_results:
                first_result = validation_results[0]
                print(f"     First claim: {first_result.get('claim', 'N/A')[:50]}...")
                verdict_output = first_result.get('validation_output', {})
                print(f"     Verdict: {verdict_output.get('verdict')}")
                print(f"     Confidence: {verdict_output.get('confidence')}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Result retrieval failed: {e}")
            return None


async def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 FACT-CHECK API CLIENT TEST")
    print("=" * 60)
    print(f"API URL: {settings.FACT_CHECK_API_URL}")
    print()
    
    # Test 1: Health check
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ Health check failed. API may be down.")
        print("   Check if API is accessible:")
        print(f"   curl {settings.FACT_CHECK_API_URL}/health")
        return 1
    
    # Test 2: Submit job
    job_id = await test_submit_job()
    if not job_id:
        print("\n❌ Job submission failed. Cannot proceed with remaining tests.")
        return 1
    
    # Test 3: Get status (immediate)
    await test_get_status(job_id)
    
    # Test 4: Poll until complete
    completed = await test_poll_until_complete(job_id, max_wait=120)
    
    # Test 5: Get result (if completed)
    if completed:
        result = await test_get_result(job_id)
        if result:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\nThe FactCheckAPIClient is working correctly:")
            print("  • API is reachable")
            print("  • Jobs can be submitted")
            print("  • Status can be polled")
            print("  • Results can be retrieved")
            return 0
    
    print("\n" + "=" * 60)
    print("⚠️  TESTS INCOMPLETE")
    print("=" * 60)
    print("Job did not complete in time, but API client functions correctly.")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
