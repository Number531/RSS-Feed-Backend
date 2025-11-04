"""
Backfill high_risk_claims_count for existing fact-check records.

Counts the number of claims with risk_level='HIGH' for each article.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import json

load_dotenv()


async def backfill_high_risk_counts():
    """Backfill high_risk_claims_count field."""

    engine = create_async_engine(os.getenv("DATABASE_URL"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get all fact-check records
        result = await session.execute(
            text(
                """
            SELECT id, validation_results
            FROM article_fact_checks
            WHERE validation_results IS NOT NULL
        """
            )
        )

        records = result.fetchall()
        total = len(records)

        print(f"\n{'='*80}")
        print(f"Backfilling high_risk_claims_count for {total} records")
        print(f"{'='*80}\n")

        updated = 0
        high_risk_articles = 0

        for record in records:
            fact_check_id = record[0]
            validation_results = record[1]

            # Parse validation results
            if isinstance(validation_results, str):
                vr = json.loads(validation_results)
            else:
                vr = validation_results

            if not isinstance(vr, list):
                continue

            # Count high-risk claims
            high_risk_count = 0

            for claim in vr:
                if isinstance(claim, dict) and "claim" in claim:
                    claim_data = claim["claim"]
                    risk_level = claim_data.get("risk_level", "")
                    if risk_level and risk_level.upper() == "HIGH":
                        high_risk_count += 1

            if high_risk_count > 0:
                high_risk_articles += 1

            # Update record
            await session.execute(
                text(
                    """
                    UPDATE article_fact_checks
                    SET high_risk_claims_count = :count
                    WHERE id = :id
                """
                ),
                {"id": fact_check_id, "count": high_risk_count},
            )

            updated += 1

            if updated % 10 == 0:
                print(f"  Processed {updated}/{total} records...")

        await session.commit()

        print(f"\n✅ Successfully updated {updated} records")
        print(
            f"📊 Articles with high-risk claims: {high_risk_articles}/{total} ({high_risk_articles/total*100:.1f}%)"
        )

        # Show distribution
        result = await session.execute(
            text(
                """
            SELECT 
                high_risk_claims_count,
                COUNT(*) as count
            FROM article_fact_checks
            GROUP BY high_risk_claims_count
            ORDER BY high_risk_claims_count DESC
        """
            )
        )

        print(f"\n{'='*80}")
        print("High-Risk Claims Distribution:")
        print(f"{'='*80}\n")

        for row in result:
            print(f"  {row[0]} high-risk claims: {row[1]} articles")

        # Show sample high-risk articles
        result = await session.execute(
            text(
                """
            SELECT 
                verdict,
                credibility_score,
                high_risk_claims_count
            FROM article_fact_checks
            WHERE high_risk_claims_count > 0
            ORDER BY high_risk_claims_count DESC
            LIMIT 5
        """
            )
        )

        print(f"\n{'='*80}")
        print("Sample High-Risk Articles:")
        print(f"{'='*80}\n")

        for row in result:
            print(f"  Verdict: {row[0]} | Score: {row[1]} | High-Risk Claims: {row[2]}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(backfill_high_risk_counts())
