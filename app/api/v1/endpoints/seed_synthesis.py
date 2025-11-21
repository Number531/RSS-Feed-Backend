"""
Seed synthesis data endpoint for development/testing.
Quickly populate the database with sample synthesis articles.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.article import Article

router = APIRouter()


@router.post(
    "/seed-synthesis",
    status_code=status.HTTP_201_CREATED,
    summary="Seed synthesis test data",
    description="Populate existing articles with sample synthesis data for frontend testing. **Development only.**",
)
async def seed_synthesis_data(
    count: int = 5,
    db: AsyncSession = Depends(get_db),
):
    """
    Seed synthesis data into existing articles for testing.
    
    This endpoint takes existing articles and adds synthetic synthesis data
    so the frontend team can test the UI without waiting for fact-checking.
    
    **Args:**
    - count: Number of articles to populate (default: 5, max: 20)
    
    **Returns:**
    - Number of articles updated
    - List of updated article IDs
    """
    # Limit to reasonable number
    count = min(count, 20)
    
    # Get articles without synthesis
    result = await db.execute(
        select(Article)
        .where(Article.has_synthesis != True)
        .limit(count)
    )
    articles = result.scalars().all()
    
    if not articles:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No articles found without synthesis data"
        )
    
    updated_ids = []
    
    # Sample verdicts and colors
    verdicts = ["TRUE", "MOSTLY TRUE", "MIXED", "MOSTLY FALSE", "FALSE"]
    colors = ["#10b981", "#84cc16", "#fbbf24", "#fb923c", "#ef4444"]
    
    for i, article in enumerate(articles):
        verdict_idx = i % len(verdicts)
        
        # Sample synthesis article (markdown)
        synthesis_article = f"""# {article.title}

## Executive Summary

This comprehensive analysis examines the claims, context, and implications of the original article. Through thorough fact-checking and cross-referencing with authoritative sources, we provide a detailed synthesis of the information presented.

**Fact-Check Verdict:** {verdicts[verdict_idx]}

## Background Context

The article discusses important developments that require careful examination. Understanding the full context is crucial for accurate assessment of the claims made.

### Key Timeline Events

1. **Initial Report** - The story first emerged from credible sources
2. **Verification Process** - Multiple independent sources confirmed key details
3. **Expert Analysis** - Subject matter experts weighed in on the implications
4. **Current Status** - The situation continues to develop

## Detailed Analysis

### Claim 1: Primary Assertion

**Assessment:** This claim has been verified through multiple credible sources.

The evidence supporting this claim includes official documents, expert testimony, and corroborating reports from independent journalists. The factual accuracy is high, though some nuance is important to understand.

**Supporting Evidence:**
- Primary source documents
- Expert verification
- Independent corroboration

### Claim 2: Secondary Context

**Assessment:** This requires additional context for full understanding.

While the basic facts are accurate, the interpretation and implications require careful consideration of the broader situation.

### Claim 3: Implications and Impact

**Assessment:** Forward-looking statements with varying certainty.

Predictions and implications are based on current trends and expert analysis, but future outcomes involve inherent uncertainty.

## Expert Perspectives

Multiple experts in the field have provided insights:

> "The situation represents a significant development that warrants close attention. The evidence suggests important implications for policy and practice." - Dr. Expert Source

## References and Citations

1. [Reference Source 1] - Official government documentation
2. [Reference Source 2] - Academic peer-reviewed research
3. [Reference Source 3] - Independent journalism investigation
4. [Reference Source 4] - Expert testimony and analysis

## Conclusion

Based on comprehensive analysis of available evidence, the overall verdict is **{verdicts[verdict_idx]}**. The claims presented in the original article have been thoroughly examined, with supporting and contradicting evidence carefully weighed.

### Key Takeaways

- ✓ Main factual claims are substantiated
- ⚠️ Some context and nuance is important
- ℹ️ Ongoing developments may affect assessment

### Credibility Assessment

This article demonstrates {'strong' if verdict_idx < 2 else 'moderate' if verdict_idx < 3 else 'concerning'} adherence to factual accuracy. Sources are {'well-documented' if verdict_idx < 2 else 'mixed'}, and the overall presentation {'maintains' if verdict_idx < 2 else 'requires careful interpretation for'} high journalistic standards.

---

*This synthesis was generated to provide comprehensive fact-checking and context for informed readers.*
"""
        
        # Calculate word count and read time
        word_count = len(synthesis_article.split())
        read_minutes = max(1, word_count // 200)
        
        # Update article with synthesis data
        article.has_synthesis = True
        article.synthesis_article = synthesis_article
        article.synthesis_preview = synthesis_article[:280]
        article.synthesis_word_count = word_count
        article.synthesis_read_minutes = read_minutes
        article.fact_check_verdict = verdicts[verdict_idx]
        article.verdict_color = colors[verdict_idx]
        article.fact_check_score = 90 - (verdict_idx * 15)  # 90, 75, 60, 45, 30
        article.fact_check_mode = "synthesis"
        article.has_timeline = True
        article.has_context_emphasis = True
        article.timeline_event_count = 3 + i
        article.reference_count = 4 + i
        article.margin_note_count = 5 + i
        
        # Add sample JSONB data
        article.article_data = {
            "references": [
                {
                    "id": 1,
                    "text": "Official government documentation",
                    "url": "https://example.com/doc1",
                    "credibility": "high"
                },
                {
                    "id": 2,
                    "text": "Academic peer-reviewed research",
                    "url": "https://example.com/doc2",
                    "credibility": "high"
                },
                {
                    "id": 3,
                    "text": "Independent journalism investigation",
                    "url": "https://example.com/doc3",
                    "credibility": "medium"
                },
                {
                    "id": 4,
                    "text": "Expert testimony and analysis",
                    "url": "https://example.com/doc4",
                    "credibility": "high"
                }
            ],
            "event_timeline": [
                {
                    "date": "2025-01-15",
                    "event": "Initial Report",
                    "description": "The story first emerged from credible sources"
                },
                {
                    "date": "2025-01-17",
                    "event": "Verification Process",
                    "description": "Multiple independent sources confirmed key details"
                },
                {
                    "date": "2025-01-19",
                    "event": "Expert Analysis",
                    "description": "Subject matter experts weighed in on implications"
                }
            ],
            "margin_notes": [
                {
                    "location": "paragraph_2",
                    "note": "Important context: This development builds on previous policy changes."
                },
                {
                    "location": "paragraph_5",
                    "note": "Cross-reference: See related analysis in [Article XYZ]"
                },
                {
                    "location": "paragraph_8",
                    "note": "Expert perspective: Dr. Smith notes this is unprecedented."
                }
            ],
            "context_and_emphasis": [
                {
                    "type": "context",
                    "text": "Historical precedent suggests similar outcomes in comparable situations"
                },
                {
                    "type": "emphasis",
                    "text": "This represents a significant departure from previous policy"
                },
                {
                    "type": "context",
                    "text": "International implications extend beyond immediate concerns"
                }
            ]
        }
        
        updated_ids.append(str(article.id))
    
    # Commit all changes
    await db.commit()
    
    return {
        "message": f"Successfully seeded {len(updated_ids)} articles with synthesis data",
        "count": len(updated_ids),
        "article_ids": updated_ids
    }


@router.delete(
    "/seed-synthesis",
    status_code=status.HTTP_200_OK,
    summary="Clear synthesis test data",
    description="Remove synthesis data from all articles. **Development only.**",
)
async def clear_synthesis_data(
    db: AsyncSession = Depends(get_db),
):
    """
    Clear all synthesis data from articles.
    
    Useful for resetting the database to a clean state for testing.
    """
    # Update all articles to clear synthesis data
    await db.execute(
        update(Article)
        .where(Article.has_synthesis == True)
        .values(
            has_synthesis=False,
            synthesis_article=None,
            synthesis_preview=None,
            synthesis_word_count=None,
            synthesis_read_minutes=None,
            fact_check_verdict=None,
            verdict_color=None,
            fact_check_score=None,
            fact_check_mode=None,
            has_timeline=False,
            has_context_emphasis=False,
            timeline_event_count=None,
            reference_count=None,
            margin_note_count=None,
        )
    )
    
    await db.commit()
    
    return {
        "message": "Successfully cleared all synthesis data from articles"
    }
