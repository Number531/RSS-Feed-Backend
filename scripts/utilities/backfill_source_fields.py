"""
Backfill new source analysis fields for existing fact-check records.

Populates:
- source_breakdown (JSONB): Evidence breakdown by type
- primary_source_type (VARCHAR): Dominant source type
- source_diversity_score (NUMERIC): Diversity metric 0.0-1.0
"""

import asyncio
import sys
from pathlib import Path
from math import log

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import json

load_dotenv()


async def backfill_source_fields():
    """Backfill new source analysis fields."""

    engine = create_async_engine(os.getenv("DATABASE_URL"))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Get all fact-check records
        result = await session.execute(
            text(
                """
            SELECT id, validation_results, num_sources
            FROM article_fact_checks
            WHERE validation_results IS NOT NULL
        """
            )
        )

        records = result.fetchall()
        total = len(records)

        print(f"\n{'='*80}")
        print(f"Backfilling {total} records with new source analysis fields")
        print(f"{'='*80}\n")

        updated = 0

        for record in records:
            fact_check_id = record[0]
            validation_results = record[1]
            current_num_sources = record[2]

            # Parse validation results
            if isinstance(validation_results, str):
                vr = json.loads(validation_results)
            else:
                vr = validation_results

            if not isinstance(vr, list):
                continue

            # Aggregate source breakdown
            source_breakdown = {"news": 0, "general": 0, "research": 0, "historical": 0}
            num_sources = 0

            for claim in vr:
                if isinstance(claim, dict) and "validation_result" in claim:
                    result_validation = claim["validation_result"]

                    evidence_count = result_validation.get("evidence_count", 0)
                    num_sources += evidence_count

                    evidence_breakdown = result_validation.get("evidence_breakdown", {})
                    for source_type, count in evidence_breakdown.items():
                        if source_type in source_breakdown:
                            source_breakdown[source_type] += count

            # Calculate primary source type and diversity
            if num_sources > 0:
                # Primary source type
                primary_source_type = max(source_breakdown, key=source_breakdown.get)

                # Diversity score using Shannon entropy
                total_types = sum(1 for count in source_breakdown.values() if count > 0)
                if total_types > 1:
                    entropy = 0.0
                    for count in source_breakdown.values():
                        if count > 0:
                            proportion = count / num_sources
                            entropy -= proportion * log(proportion, total_types)
                    source_diversity_score = round(entropy, 2)
                else:
                    source_diversity_score = 0.0
            else:
                primary_source_type = None
                source_diversity_score = None

            # Update record
            await session.execute(
                text(
                    """
                    UPDATE article_fact_checks
                    SET source_breakdown = :source_breakdown,
                        primary_source_type = :primary_source_type,
                        source_diversity_score = :source_diversity_score
                    WHERE id = :id
                """
                ),
                {
                    "id": fact_check_id,
                    "source_breakdown": json.dumps(source_breakdown),
                    "primary_source_type": primary_source_type,
                    "source_diversity_score": source_diversity_score,
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
                num_sources,
                primary_source_type,
                source_diversity_score,
                source_breakdown
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
            print(f"  Verdict: {row[0]} | Sources: {row[1]}")
            print(f"  Primary Type: {row[2]} | Diversity: {row[3]}")
            print(f"  Breakdown: {row[4]}")
            print()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(backfill_source_fields())
