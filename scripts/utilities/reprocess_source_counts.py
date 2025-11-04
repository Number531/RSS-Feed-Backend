"""
Reprocess existing fact-check records to populate num_sources and source_consensus.

This script re-applies the updated transformation logic to all existing fact-check
records that have validation_results but missing source information.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import json

load_dotenv()


async def reprocess_sources():
    """Reprocess all fact-check records to populate source information."""

    engine = create_async_engine(os.getenv("DATABASE_URL"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get all fact-check records with validation results but missing sources
        result = await session.execute(
            text(
                """
            SELECT id, validation_results
            FROM article_fact_checks
            WHERE validation_results IS NOT NULL
            AND (num_sources = 0 OR num_sources IS NULL)
        """
            )
        )

        records = result.fetchall()
        total = len(records)

        print(f"\n{'='*80}")
        print(f"Reprocessing {total} fact-check records to populate source information")
        print(f"{'='*80}\n")

        updated = 0

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

            # Aggregate source info
            num_sources = 0
            source_breakdown = {"news": 0, "general": 0, "research": 0, "historical": 0}

            for claim in vr:
                if isinstance(claim, dict) and "validation_result" in claim:
                    result_validation = claim["validation_result"]

                    # Get evidence count
                    evidence_count = result_validation.get("evidence_count", 0)
                    num_sources += evidence_count

                    # Aggregate breakdown
                    evidence_breakdown = result_validation.get("evidence_breakdown", {})
                    for source_type, count in evidence_breakdown.items():
                        if source_type in source_breakdown:
                            source_breakdown[source_type] += count

            # Calculate consensus
            if num_sources > 0:
                max_type = max(source_breakdown, key=source_breakdown.get)
                max_count = source_breakdown[max_type]
                consensus_percentage = (max_count / num_sources) * 100

                if consensus_percentage >= 60:
                    source_consensus = f"STRONG_{max_type.upper()}"
                elif consensus_percentage >= 40:
                    source_consensus = f"MODERATE_{max_type.upper()}"
                else:
                    source_consensus = "MIXED"
            else:
                source_consensus = None

            # Update record
            await session.execute(
                text(
                    """
                    UPDATE article_fact_checks
                    SET num_sources = :num_sources,
                        source_consensus = :source_consensus
                    WHERE id = :id
                """
                ),
                {
                    "id": fact_check_id,
                    "num_sources": num_sources,
                    "source_consensus": source_consensus,
                },
            )

            updated += 1

            if updated % 10 == 0:
                print(f"  Processed {updated}/{total} records...")

        await session.commit()

        print(f"\n✅ Successfully updated {updated} records")

        # Show sample results
        result = await session.execute(
            text(
                """
            SELECT 
                verdict,
                credibility_score,
                num_sources,
                source_consensus
            FROM article_fact_checks
            WHERE num_sources > 0
            LIMIT 5
        """
            )
        )

        print(f"\n{'='*80}")
        print("Sample updated records:")
        print(f"{'='*80}\n")

        for row in result:
            print(
                f"  Verdict: {row[0]} | Score: {row[1]} | Sources: {row[2]} | Consensus: {row[3]}"
            )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reprocess_sources())
