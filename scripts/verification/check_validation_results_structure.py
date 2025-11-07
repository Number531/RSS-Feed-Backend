#!/usr/bin/env python3
"""
Check the structure of validation_results stored in database.

This script queries the database to see what data is actually stored
in the validation_results JSONB field to determine if we need to modify
the storage strategy.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.fact_check import ArticleFactCheck


async def check_validation_results_structure():
    """Check what's stored in validation_results field."""
    
    async with AsyncSessionLocal() as session:  # type: AsyncSession
        # Get a COMPLETED fact-check record (not PENDING)
        result = await session.execute(
            select(ArticleFactCheck)
            .where(ArticleFactCheck.verdict != "PENDING")
            .limit(1)
        )
        fact_check = result.scalar_one_or_none()
        
        if not fact_check:
            print("❌ No fact-check records found in database")
            return
        
        print(f"✅ Found fact-check record: {fact_check.id}")
        print(f"   Article ID: {fact_check.article_id}")
        print(f"   Job ID: {fact_check.job_id}")
        print(f"   Verdict: {fact_check.verdict}")
        print(f"   Mode: {fact_check.validation_mode}")
        print()
        
        # Check validation_results structure
        validation_results = fact_check.validation_results
        
        print("=" * 80)
        print("VALIDATION_RESULTS STRUCTURE:")
        print("=" * 80)
        print(json.dumps(validation_results, indent=2))
        print()
        
        # Check if it's a list or dict
        if isinstance(validation_results, list):
            print("📋 validation_results is a LIST")
            if validation_results:
                first_result = validation_results[0]
                print(f"\n🔍 First validation result keys: {list(first_result.keys())}")
                
                # Check for validation_result field
                if "validation_result" in first_result:
                    val_result = first_result["validation_result"]
                    print(f"\n🔍 validation_result keys: {list(val_result.keys())}")
                    
                    # Check for references
                    if "references" in val_result:
                        print(f"\n✅ FOUND 'references' field!")
                        print(f"   Number of references: {len(val_result['references'])}")
                        if val_result['references']:
                            print(f"   First reference: {val_result['references'][0]}")
                    else:
                        print(f"\n❌ NO 'references' field found")
                    
                    # Check for key_evidence
                    if "key_evidence" in val_result:
                        print(f"\n✅ FOUND 'key_evidence' field!")
                        print(f"   Evidence categories: {list(val_result['key_evidence'].keys())}")
                    else:
                        print(f"\n❌ NO 'key_evidence' field found")
                        
        elif isinstance(validation_results, dict):
            print("📋 validation_results is a DICT")
            print(f"   Keys: {list(validation_results.keys())}")
            
            if "claims" in validation_results:
                claims = validation_results["claims"]
                print(f"\n🔍 Found {len(claims)} claims")
                if claims:
                    first_claim = claims[0]
                    print(f"   First claim keys: {list(first_claim.keys())}")
        else:
            print(f"⚠️  validation_results is {type(validation_results)}")


async def main():
    """Main function."""
    print("\n🔍 Checking validation_results structure in database...\n")
    await check_validation_results_structure()


if __name__ == "__main__":
    asyncio.run(main())
