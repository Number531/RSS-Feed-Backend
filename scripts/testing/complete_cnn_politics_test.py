#!/usr/bin/env python3
"""
Complete CNN Politics Fact-Check Test
======================================
This script executes all 6 steps of the fact-check testing workflow:
1. Clear database tables
2. Populate CNN Politics articles
3. Trigger fact-checking
4. Poll for completion
5. Display results
6. Process remaining articles (optional)

Usage:
    python3 scripts/testing/complete_cnn_politics_test.py
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
    """Step 2: Populate CNN Politics articles"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 2: Populating CNN Politics Articles[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Add RSS source
            console.print("📡 Adding RSS source...")
            rss_source = RSSSource(
                name="CNN - Politics",
                url="http://rss.cnn.com/rss/cnn_allpolitics.rss",
                source_name="CNN",  # Required field
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
                        author = entry.get("author", "CNN")
                        
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


async def step_3_trigger_fact_checks():
    """Step 3: Trigger fact-checking for articles"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 3: Triggering Fact-Check Jobs[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Get articles without fact-checks
            result = await session.execute(
                text("SELECT id, title, url FROM articles WHERE fact_check_score IS NULL")
            )
            articles = result.fetchall()
            
            console.print(f"📝 Found {len(articles)} articles to fact-check\n")
            
            if not articles:
                console.print("⚠️  No articles to fact-check!")
                return []
            
            # Initialize fact-check service with required repositories
            fact_check_repo = FactCheckRepository(session)
            article_repo = ArticleRepository(session)
            fact_check_service = FactCheckService(fact_check_repo, article_repo)
            
            submitted_jobs = []
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Submitting fact-check jobs...", total=len(articles))
                
                for article_id, title, url in articles:
                    try:
                        # Submit fact-check with thorough mode
                        job = await fact_check_service.submit_fact_check(
                            article_id,
                            mode="thorough"  # Using thorough mode for detailed analysis
                        )
                        
                        if job:
                            submitted_jobs.append({
                                "article_id": article_id,
                                "title": title,
                                "job_id": job.job_id
                            })
                            console.print(f"   ✓ Submitted: {title[:60]}... (Job ID: {job.job_id})")
                        
                    except Exception as e:
                        console.print(f"   ⚠️  Failed: {title[:60]}... - {e}")
                    
                    progress.advance(task)
                
                # Commit all pending fact-check records
                await session.commit()
            
            console.print(f"\n✅ [bold green]Successfully submitted {len(submitted_jobs)} fact-check jobs![/bold green]\n")
            return submitted_jobs
            
        except Exception as e:
            console.print(f"\n❌ [bold red]Error triggering fact-checks: {e}[/bold red]\n")
            raise


async def step_4_poll_for_completion(submitted_jobs: List[Dict[str, Any]], max_wait_minutes: int = 30):
    """Step 4: Poll for fact-check completion"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 4: Polling for Fact-Check Completion[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    if not submitted_jobs:
        console.print("⚠️  No jobs to poll!")
        return []
    
    console.print(f"⏳ Polling {len(submitted_jobs)} jobs (max wait: {max_wait_minutes} minutes)")
    console.print("   Est. time: ~2-3 minutes per article\n")
    
    completed_jobs = []
    failed_jobs = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("Polling for completion...", total=len(submitted_jobs))
        
        # Process jobs concurrently with asyncio.gather
        # Uses fresh DB connections for each poll to avoid timeout issues
        async def poll_job(job_info):
            """Poll a single job with connection management between checks."""
            job_id = job_info["job_id"]
            max_attempts = 120  # 120 * 30s = 60 minutes max
            poll_interval = 30  # Poll every 30 seconds
            attempt = 0
            
            try:
                # Import here to avoid circular dependencies
                from app.clients.fact_check_client import FactCheckAPIClient
                from app.utils.fact_check_transform import transform_api_result_to_db
                
                async with FactCheckAPIClient() as api_client:
                    while attempt < max_attempts:
                        # Check Railway API status (no DB connection needed)
                        status = await api_client.get_job_status(job_id)
                        current_status = status.get("status")
                        
                        # Job completed - open DB connection to store results
                        if current_status == "finished":
                            # Get full result from API
                            result = await api_client.get_job_result(job_id)
                            
                            # Open fresh DB connection for final update
                            async with AsyncSessionLocal() as session:
                                fact_check_repo = FactCheckRepository(session)
                                article_repo = ArticleRepository(session)
                                
                                # Get fact-check record
                                fact_check = await fact_check_repo.get_by_job_id(job_id)
                                if not fact_check:
                                    raise Exception(f"Fact-check record not found for job {job_id}")
                                
                                # Transform API result to DB format
                                db_data = transform_api_result_to_db(result, fact_check.article_id)
                                
                                # Update fact-check record
                                updated_fact_check = await fact_check_repo.update(
                                    fact_check.id,
                                    db_data
                                )
                                
                                # Update article credibility fields
                                article = await article_repo.get_article_by_id(fact_check.article_id)
                                if article:
                                    article.fact_check_score = db_data["credibility_score"]
                                    article.fact_check_verdict = updated_fact_check.verdict
                                    article.fact_checked_at = updated_fact_check.fact_checked_at
                                
                                # Commit all changes
                                await session.commit()
                            
                            console.print(f"   ✓ Completed: {job_info['title'][:60]}...")
                            progress.advance(task)
                            return {**job_info, "result": updated_fact_check, "status": "completed"}
                        
                        # Job failed
                        elif current_status == "failed":
                            error_msg = status.get("error", "Unknown error")
                            
                            # Open DB connection to store failure
                            async with AsyncSessionLocal() as session:
                                fact_check_repo = FactCheckRepository(session)
                                fact_check = await fact_check_repo.get_by_job_id(job_id)
                                if fact_check:
                                    await fact_check_repo.update(
                                        fact_check.id,
                                        {
                                            "verdict": "ERROR",
                                            "credibility_score": -1,
                                            "summary": f"Fact-check failed: {error_msg}",
                                            "validation_results": {"error": error_msg}
                                        }
                                    )
                                    await session.commit()
                            
                            raise Exception(f"Job failed: {error_msg}")
                        
                        # Still processing - wait before next check (no DB connection held)
                        await asyncio.sleep(poll_interval)
                        attempt += 1
                
                # Timeout reached
                async with AsyncSessionLocal() as session:
                    fact_check_repo = FactCheckRepository(session)
                    fact_check = await fact_check_repo.get_by_job_id(job_id)
                    if fact_check:
                        await fact_check_repo.update(
                            fact_check.id,
                            {
                                "verdict": "TIMEOUT",
                                "credibility_score": -1,
                                "summary": f"Fact-check timed out after {max_attempts * poll_interval}s",
                                "validation_results": {"error": "timeout"}
                            }
                        )
                        await session.commit()
                
                raise Exception(f"Job timed out after {max_attempts * poll_interval}s")
                
            except Exception as e:
                console.print(f"   ⚠️  Failed: {job_info['title'][:60]}... - {e}")
                progress.advance(task)
                return {**job_info, "error": str(e), "status": "failed"}
        
        # Poll all jobs concurrently
        results = await asyncio.gather(*[poll_job(job) for job in submitted_jobs], return_exceptions=True)
        
        # Categorize results
        for result in results:
            if isinstance(result, dict):
                if result.get("status") == "completed":
                    completed_jobs.append(result)
                else:
                    failed_jobs.append(result)
        
        console.print(f"\n✅ [bold green]Completed {len(completed_jobs)}/{len(submitted_jobs)} fact-checks![/bold green]")
        if failed_jobs:
            console.print(f"⚠️  [yellow]Failed: {len(failed_jobs)} jobs[/yellow]\n")
        else:
            console.print()
        
        return completed_jobs


async def step_5_display_results():
    """Step 5: Display comprehensive results"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 5: Test Results & Statistics[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Get statistics
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN fact_check_score IS NOT NULL THEN 1 END) as fact_checked,
                    AVG(CASE WHEN fact_check_score IS NOT NULL THEN fact_check_score END) as avg_score
                FROM articles
            """))
            stats = result.fetchone()
            
            result = await session.execute(text("""
                SELECT 
                    fact_check_verdict,
                    COUNT(*) as count
                FROM articles
                WHERE fact_check_verdict IS NOT NULL
                GROUP BY fact_check_verdict
            """))
            verdict_counts = result.fetchall()
            
            # Display summary statistics
            table = Table(title="📊 Test Summary", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")
            
            table.add_row("Total Articles", str(stats.total))
            table.add_row("Fact-Checked", str(stats.fact_checked))
            table.add_row("Pending", str(stats.total - stats.fact_checked))
            table.add_row("Avg Credibility Score", f"{stats.avg_score:.1f}" if stats.avg_score else "N/A")
            
            console.print(table)
            console.print()
            
            # Display verdict breakdown
            if verdict_counts:
                verdict_table = Table(title="📋 Verdict Breakdown", show_header=True, header_style="bold magenta")
                verdict_table.add_column("Verdict", style="cyan")
                verdict_table.add_column("Count", justify="right", style="green")
                
                for verdict, count in verdict_counts:
                    verdict_table.add_row(verdict or "Unknown", str(count))
                
                console.print(verdict_table)
                console.print()
            
            # Display sample fact-checked articles
            result = await session.execute(text("""
                SELECT 
                    id, title, fact_check_score, fact_check_verdict, fact_checked_at
                FROM articles
                WHERE fact_check_score IS NOT NULL
                ORDER BY fact_checked_at DESC
                LIMIT 5
            """))
            articles = result.fetchall()
            
            if articles:
                article_table = Table(title="📰 Sample Fact-Checked Articles", show_header=True, header_style="bold magenta")
                article_table.add_column("Title", style="cyan", max_width=50)
                article_table.add_column("Score", justify="center", style="yellow")
                article_table.add_column("Verdict", style="green")
                
                for article_id, title, score, verdict, checked_at in articles:
                    article_table.add_row(
                        title[:50] + "..." if len(title) > 50 else title,
                        str(score),
                        verdict or "N/A"
                    )
                
                console.print(article_table)
                console.print()
            
            # Display API endpoints
            console.print(Panel.fit(
                "[bold yellow]Frontend API Endpoints:[/bold yellow]\n\n"
                "• List articles:\n"
                "  GET /api/v1/articles?category=politics\n\n"
                "• Get fact-check details:\n"
                "  GET /api/v1/articles/{article_id}/fact-check\n\n"
                "• Example article IDs:\n"
                f"  {', '.join(str(a[0]) for a in articles[:3]) if articles else 'N/A'}",
                title="🔗 Integration Info",
                border_style="green"
            ))
            
        except Exception as e:
            console.print(f"\n❌ [bold red]Error displaying results: {e}[/bold red]\n")
            raise


async def main():
    """Execute all 6 steps"""
    console.print("\n[bold green]╔════════════════════════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║   Fox News Politics Fact-Check Test - Complete Workflow   ║[/bold green]")
    console.print("[bold green]╚════════════════════════════════════════════════════════════╝[/bold green]\n")
    
    start_time = datetime.utcnow()
    
    try:
        # Step 1: Clear database
        await step_1_clear_database()
        
        # Step 2: Populate articles
        article_count = await step_2_populate_articles()
        
        # Step 3: Trigger fact-checks
        submitted_jobs = await step_3_trigger_fact_checks()
        
        # Step 4: Poll for completion
        completed_jobs = await step_4_poll_for_completion(submitted_jobs, max_wait_minutes=30)
        
        # Step 5: Display results
        await step_5_display_results()
        
        # Summary
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        console.print(f"\n[bold green]✅ Test completed in {elapsed:.1f} seconds![/bold green]\n")
        
        console.print("[bold yellow]Next Steps:[/bold yellow]")
        console.print("  • Review fact-check results above")
        console.print("  • Test API endpoints with frontend")
        console.print("  • Run Step 6 (optional) to process remaining articles")
        console.print("  • Check Railway API dashboard for detailed reports\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed: {e}[/bold red]\n")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)


    finally:
        # Clean up database connections
        await engine.dispose()
        console.print("\n[dim]🔌 Database connections closed[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
