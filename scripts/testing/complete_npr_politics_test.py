#!/usr/bin/env python3
"""
Complete NPR Politics Fact-Check Test
======================================
This script executes all 6 steps of the fact-check testing workflow:
1. Clear database tables
2. Populate NPR Politics articles
3. Trigger fact-checking
4. Poll for completion
5. Display results
6. Process remaining articles (optional)

Usage:
    python3 scripts/testing/complete_npr_politics_test.py
"""

import asyncio
import sys
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import feedparser
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import print as rprint

from app.core.config import settings
from app.models.article import Article
from app.models.rss_source import RSSSource
from app.models.fact_check import ArticleFactCheck
from app.services.fact_check_service import FactCheckService
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository

console = Console()

# Database connection with increased pool size for concurrent operations
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
    pool_size=20,  # Increased from default 5 to handle concurrent jobs
    max_overflow=10,  # Allow up to 10 additional connections beyond pool_size
    pool_recycle=3600,  # Recycle connections every hour to prevent stale connections
    pool_timeout=30,  # Wait up to 30 seconds for a connection from the pool
)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def step_1_clear_database():
    """Step 1: Clear all database tables"""
    console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 1: Clearing Database Tables[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Count existing records
            result = await session.execute(text("SELECT COUNT(*) FROM rss_sources"))
            rss_count = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM articles"))
            article_count = result.scalar()
            result = await session.execute(text("SELECT COUNT(*) FROM article_fact_checks"))
            fact_check_count = result.scalar()
            
            console.print(f"📊 Current database state:")
            console.print(f"   • RSS Sources: {rss_count}")
            console.print(f"   • Articles: {article_count}")
            console.print(f"   • Fact Checks: {fact_check_count}\n")
            
            # Delete from tables in correct order (safer than TRUNCATE)
            tables = [
                "article_fact_checks",
                "votes", 
                "comments",
                "bookmarks",
                "reading_history",
                "notifications",
                "articles",
                "rss_sources"
            ]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Clearing tables...", total=len(tables))
                
                # Set statement timeout to 60 seconds
                await session.execute(text("SET statement_timeout = 60000"))
                
                for table in tables:
                    await session.execute(text(f"DELETE FROM {table}"))
                    progress.advance(task)
                
                await session.commit()
            
            console.print("\n✅ [bold green]Database cleared successfully![/bold green]\n")
            
        except Exception as e:
            console.print(f"\n❌ [bold red]Error clearing database: {e}[/bold red]\n")
            await session.rollback()
            raise


async def step_2_populate_articles():
    """Step 2: Populate NPR Politics articles"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 2: Populating NPR Politics Articles[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Add RSS source
            console.print("📡 Adding RSS source...")
            rss_source = RSSSource(
                name="NPR - Politics",
                url="https://feeds.npr.org/1014/rss.xml",
                source_name="NPR",  # Required field
                category="politics",
                is_active=True
            )
            session.add(rss_source)
            await session.commit()
            await session.refresh(rss_source)
            console.print(f"✓ Added RSS source: {rss_source.name}\n")
            
            # Fetch and parse RSS feed
            console.print("🔍 Fetching RSS feed...")
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
                response = await client.get(rss_source.url)
                response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            console.print(f"✓ Found {len(feed.entries)} articles in feed\n")
            
            # Process articles
            articles_added = 0
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Processing articles...", total=len(feed.entries))
                
                for entry in feed.entries[:10]:  # Limit to 10 articles
                    try:
                        # Extract article data
                        title = entry.get("title", "No Title")
                        url = entry.get("link", "")
                        description = entry.get("summary", "")[:500]
                        
                        # Get published date
                        published_date = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published_date = datetime(*entry.published_parsed[:6])
                        
                        # Get thumbnail
                        thumbnail_url = None
                        if hasattr(entry, "media_content") and entry.media_content:
                            thumbnail_url = entry.media_content[0].get("url")
                        elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                            thumbnail_url = entry.media_thumbnail[0].get("url")
                        
                        # Get author
                        author = entry.get("author", "NPR")
                        
                        # Create URL hash for deduplication
                        url_hash = hashlib.sha256(url.encode()).hexdigest()
                        
                        # Create article
                        article = Article(
                            title=title,
                            url=url,
                            description=description,
                            content=description,  # Use description as content
                            author=author,
                            published_date=published_date or datetime.utcnow(),
                            thumbnail_url=thumbnail_url,
                            category="politics",
                            rss_source_id=rss_source.id,
                            url_hash=url_hash
                        )
                        session.add(article)
                        articles_added += 1
                    except Exception as e:
                        console.print(f"⚠️  Skipped article: {e}")
                    
                    progress.advance(task)
                
                await session.commit()
            
            console.print(f"\n✅ [bold green]Successfully added {articles_added} articles![/bold green]\n")
            return articles_added
            
        except Exception as e:
            console.print(f"\n❌ [bold red]Error populating articles: {e}[/bold red]\n")
            await session.rollback()
            raise


async def step_3_submit_fact_checks():
    """Step 3: Submit fact-check jobs for all articles"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 3: Submitting Fact-Check Jobs[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        article_repo = ArticleRepository(session)
        fact_check_service = FactCheckService(
            fact_check_repo=FactCheckRepository(session),
            article_repo=article_repo
        )
        
        # Get all articles without fact-checks
        result = await session.execute(
            text("SELECT id, title FROM articles WHERE fact_check_score IS NULL ORDER BY published_date DESC")
        )
        articles = result.fetchall()
        
        if not articles:
            console.print("❌ No articles found to fact-check\n")
            return []
        
        console.print(f"📝 Found {len(articles)} articles to fact-check\n")
        
        job_ids = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Submitting jobs...", total=len(articles))
            
            for article_id, title in articles:
                try:
                    job_id = await fact_check_service.submit_fact_check(str(article_id))
                    job_ids.append((str(article_id), job_id, title))
                    console.print(f"✓ Submitted: {title[:60]}... (Job ID: {job_id})")
                except Exception as e:
                    console.print(f"❌ Failed: {title[:60]}... - {e}")
                
                progress.advance(task)
        
        console.print(f"\n✅ [bold green]Submitted {len(job_ids)} fact-check jobs![/bold green]\n")
        return job_ids


async def poll_job(article_id: str, job_id: str, title: str, max_attempts: int = 240, poll_interval: int = 5):
    """Poll a single job until completion"""
    api_client = httpx.AsyncClient(timeout=30.0)
    
    for attempt in range(max_attempts):
        try:
            # Query Railway API for job status
            response = await api_client.get(f"{settings.FACT_CHECK_API_URL}/job/{job_id}")
            
            if response.status_code == 200:
                job_data = response.json()
                status = job_data.get("status")
                
                if status == "completed":
                    # Open fresh DB session to update
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(
                            text("SELECT id FROM articles WHERE id = :article_id"),
                            {"article_id": article_id}
                        )
                        if result.scalar_one_or_none():
                            fact_check_service = FactCheckService(
                                fact_check_repo=FactCheckRepository(session),
                                article_repo=ArticleRepository(session)
                            )
                            await fact_check_service.poll_and_complete_job(job_id)
                    return {"status": "completed", "article_id": article_id, "job_id": job_id}
                
                elif status == "failed":
                    error = job_data.get("error", "Unknown error")
                    # Mark as failed in DB
                    async with AsyncSessionLocal() as session:
                        await session.execute(
                            text("DELETE FROM article_fact_checks WHERE job_id = :job_id"),
                            {"job_id": job_id}
                        )
                        await session.commit()
                    return {"status": "failed", "article_id": article_id, "job_id": job_id, "error": error}
            
            await asyncio.sleep(poll_interval)
            
        except Exception as e:
            if attempt == max_attempts - 1:
                # Final attempt failed, mark as timeout
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        text("DELETE FROM article_fact_checks WHERE job_id = :job_id"),
                        {"job_id": job_id}
                    )
                    await session.commit()
                return {"status": "timeout", "article_id": article_id, "job_id": job_id, "error": str(e)}
            await asyncio.sleep(poll_interval)
    
    await api_client.aclose()
    return {"status": "timeout", "article_id": article_id, "job_id": job_id}


async def step_4_poll_completion(job_ids: List[tuple]):
    """Step 4: Poll for job completion"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 4: Polling for Job Completion[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    console.print(f"⏳ Polling {len(job_ids)} jobs (checking every 5 seconds, max 20 minutes per job)...\n")
    
    start_time = datetime.now()
    
    # Poll all jobs concurrently
    tasks = [poll_job(article_id, job_id, title) for article_id, job_id, title in job_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count results
    completed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "completed")
    failed = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "failed")
    timeout = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "timeout")
    
    duration = (datetime.now() - start_time).total_seconds()
    
    console.print(f"\n✅ [bold green]Polling complete in {duration:.1f} seconds![/bold green]")
    console.print(f"   • Completed: {completed}")
    console.print(f"   • Failed: {failed}")
    console.print(f"   • Timeout: {timeout}\n")
    
    # Show failures
    if failed > 0:
        console.print("[bold yellow]Failed jobs:[/bold yellow]")
        for i, (article_id, job_id, title) in enumerate(job_ids):
            result = results[i]
            if isinstance(result, dict) and result.get("status") == "failed":
                error = result.get("error", "Unknown")
                console.print(f"   ❌ {title[:60]}... - {error}")
        console.print()


async def step_5_display_results():
    """Step 5: Display fact-check results"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 5: Fact-Check Results[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        # Get overall stats
        result = await session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(fact_check_score) as fact_checked,
                AVG(fact_check_score) as avg_score
            FROM articles
        """))
        stats = result.fetchone()
        
        # Get verdict breakdown
        result = await session.execute(text("""
            SELECT 
                fact_check_verdict,
                COUNT(*) as count,
                AVG(fact_check_score) as avg_score
            FROM articles
            WHERE fact_check_verdict IS NOT NULL
            GROUP BY fact_check_verdict
            ORDER BY count DESC
        """))
        verdicts = result.fetchall()
        
        # Display stats
        table = Table(title="Test Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Articles", str(stats.total))
        table.add_row("Fact-Checked", str(stats.fact_checked))
        table.add_row("Pending", str(stats.total - stats.fact_checked))
        table.add_row("Avg Credibility Score", f"{stats.avg_score:.1f}" if stats.avg_score else "N/A")
        
        console.print(table)
        console.print()
        
        # Display verdict breakdown
        if verdicts:
            verdict_table = Table(title="Verdict Distribution", show_header=True, header_style="bold magenta")
            verdict_table.add_column("Verdict", style="cyan")
            verdict_table.add_column("Count", style="yellow")
            verdict_table.add_column("Avg Score", style="green")
            
            for verdict, count, avg_score in verdicts:
                verdict_table.add_row(
                    verdict,
                    str(count),
                    f"{avg_score:.1f}" if avg_score else "N/A"
                )
            
            console.print(verdict_table)
            console.print()
        
        # Sample articles
        result = await session.execute(text("""
            SELECT title, fact_check_score, fact_check_verdict, id
            FROM articles
            WHERE fact_check_score IS NOT NULL
            ORDER BY fact_checked_at DESC
            LIMIT 5
        """))
        samples = result.fetchall()
        
        if samples:
            sample_table = Table(title="Sample Fact-Checked Articles", show_header=True, header_style="bold magenta")
            sample_table.add_column("Title", style="cyan", width=50)
            sample_table.add_column("Score", style="yellow", width=6)
            sample_table.add_column("Verdict", style="green", width=30)
            
            for title, score, verdict, _ in samples:
                sample_table.add_row(
                    title[:50],
                    str(score),
                    verdict
                )
            
            console.print(sample_table)
            console.print()
        
        # Integration endpoints
        console.print("[bold cyan]Frontend Integration Endpoints:[/bold cyan]")
        console.print(f"   • GET /api/v1/articles?category=politics")
        if samples:
            console.print(f"   • GET /api/v1/articles/{{article_id}}/fact-check")
            console.print(f"   • Example IDs: {samples[0][3]}, {samples[1][3] if len(samples) > 1 else '...'}")
        console.print()


async def main():
    """Main execution flow"""
    console.print("\n[bold green]═══════════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]NPR POLITICS FACT-CHECK INTEGRATION TEST[/bold green]")
    console.print("[bold green]═══════════════════════════════════════════════════════════[/bold green]")
    
    start_time = datetime.now()
    
    try:
        # Execute all steps
        await step_1_clear_database()
        articles_count = await step_2_populate_articles()
        job_ids = await step_3_submit_fact_checks()
        
        if job_ids:
            await step_4_poll_completion(job_ids)
        
        await step_5_display_results()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        console.print("[bold green]═══════════════════════════════════════════════════════════[/bold green]")
        console.print(f"[bold green]✅ TEST COMPLETE - Total Duration: {duration:.1f} seconds[/bold green]")
        console.print("[bold green]═══════════════════════════════════════════════════════════[/bold green]\n")
        
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]⚠️  Test interrupted by user[/bold yellow]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n\n[bold red]❌ Test failed with error: {e}[/bold red]\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
