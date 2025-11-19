#!/usr/bin/env python3
"""
Complete Fox News Politics Fact-Check Test - SYNTHESIS MODE
=============================================================
This script executes all 6 steps of the fact-check testing workflow using SYNTHESIS MODE:
1. Clear database tables
2. Populate Fox News Politics articles
3. Trigger fact-checking with SYNTHESIS MODE
4. Poll for completion (4-7 min per article)
5. Display results with synthesis article data
6. Process remaining articles (optional)

SYNTHESIS MODE generates:
- 1,400-2,500 word narrative articles
- Context & Emphasis analysis
- Event timelines
- Margin notes
- Full citations

Usage:
    python3 scripts/testing/complete_fox_politics_test_synthesis.py
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
from app.models.article_analytics import ArticleAnalytics
from app.services.fact_check_service import FactCheckService
from app.repositories.fact_check_repository import FactCheckRepository
from app.repositories.article_repository import ArticleRepository

console = Console()

# Database connection with increased pool size for concurrent operations
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    pool_timeout=30,
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
            
            # Delete from tables in correct order
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
    """Step 2: Populate Fox News Politics articles"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 2: Populating Fox News Politics Articles[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Add RSS source
            console.print("📡 Adding RSS source...")
            rss_source = RSSSource(
                name="Fox News - Politics",
                url="http://feeds.foxnews.com/foxnews/politics",
                source_name="Fox News",
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
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
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
                        
                        author = entry.get("author", "Fox News")
                        url_hash = hashlib.md5(url.encode()).hexdigest()
                        
                        article = Article(
                            title=title,
                            url=url,
                            description=description,
                            content=description,
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
    """Step 3: Trigger fact-checking with SYNTHESIS MODE"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 3: Triggering Synthesis Mode Fact-Check Jobs[/bold cyan]")
    console.print("[bold yellow]⚡ Using SYNTHESIS MODE - Generates full narrative articles![/bold yellow]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text("SELECT id, title, url FROM articles WHERE fact_check_score IS NULL")
            )
            articles = result.fetchall()
            
            console.print(f"📝 Found {len(articles)} articles to fact-check\n")
            
            if not articles:
                console.print("⚠️  No articles to fact-check!")
                return []
            
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
                task = progress.add_task("Submitting synthesis fact-check jobs...", total=len(articles))
                
                for article_id, title, url in articles:
                    try:
                        # Submit fact-check with SYNTHESIS mode
                        job = await fact_check_service.submit_fact_check(
                            article_id,
                            mode="synthesis"  # ← SYNTHESIS MODE (generate_article=True is hardcoded in service)
                        )
                        
                        if job:
                            submitted_jobs.append({
                                "article_id": article_id,
                                "title": title,
                                "job_id": job.job_id
                            })
                            console.print(f"   ✓ Submitted: {title[:60]}... (Job: {job.job_id})")
                        
                    except Exception as e:
                        console.print(f"   ⚠️  Failed: {title[:60]}... - {e}")
                    
                    progress.advance(task)
                
                await session.commit()
            
            console.print(f"\n✅ [bold green]Successfully submitted {len(submitted_jobs)} synthesis jobs![/bold green]")
            console.print(f"[yellow]⏱️  Expected time: 4-7 minutes per article[/yellow]\n")
            return submitted_jobs
            
        except Exception as e:
            console.print(f"\n❌ [bold red]Error triggering fact-checks: {e}[/bold red]\n")
            raise


async def step_4_poll_for_completion(submitted_jobs: List[Dict[str, Any]]):
    """Step 4: Poll for synthesis fact-check completion
    
    Uses backend config settings:
    - FACT_CHECK_MAX_POLL_ATTEMPTS (default: 180)
    - FACT_CHECK_POLL_INTERVAL (default: 5s)
    - Total timeout: 180 × 5s = 900s (15 minutes)
    """
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 4: Polling for Synthesis Mode Completion[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    if not submitted_jobs:
        console.print("⚠️  No jobs to poll!")
        return []
    
    # Use backend configuration settings
    max_attempts = settings.FACT_CHECK_MAX_POLL_ATTEMPTS  # 180 (15 minutes)
    poll_interval = settings.FACT_CHECK_POLL_INTERVAL  # 5 seconds
    total_timeout_min = (max_attempts * poll_interval) / 60
    
    console.print(f"⏳ Polling {len(submitted_jobs)} synthesis jobs (max wait: {total_timeout_min:.0f} minutes per job)")
    console.print(f"   [yellow]Config: {max_attempts} attempts × {poll_interval}s = {total_timeout_min:.0f} min[/yellow]")
    console.print("   [yellow]Est. synthesis time: 4-7 minutes per article[/yellow]\n")
    
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
        
        async def poll_job(job_info):
            """Poll a single synthesis job using backend config settings."""
            job_id = job_info["job_id"]
            attempt = 0
            
            try:
                from app.clients.fact_check_client import FactCheckAPIClient
                from app.utils.fact_check_transform import transform_api_result_to_db
                
                async with FactCheckAPIClient() as api_client:
                    while attempt < max_attempts:
                        status = await api_client.get_job_status(job_id)
                        current_status = status.get("status")
                        
                        if current_status == "finished":
                            # Get full synthesis result
                            result = await api_client.get_job_result(job_id)
                            
                            async with AsyncSessionLocal() as session:
                                fact_check_repo = FactCheckRepository(session)
                                article_repo = ArticleRepository(session)
                                
                                fact_check = await fact_check_repo.get_by_job_id(job_id)
                                if not fact_check:
                                    raise Exception(f"Fact-check record not found for job {job_id}")
                                
                                db_data = transform_api_result_to_db(result, fact_check.article_id)
                                
                                updated_fact_check = await fact_check_repo.update(
                                    fact_check.id,
                                    db_data
                                )
                                
                                # Update article with synthesis content
                                article = await article_repo.get_article_by_id(fact_check.article_id)
                                if article:
                                    article.fact_check_score = db_data["credibility_score"]
                                    article.fact_check_verdict = updated_fact_check.verdict
                                    article.fact_checked_at = updated_fact_check.fact_checked_at
                                    
                                    # Store synthesis article (NEW!)
                                    article_text = result.get("article_text", "")
                                    if article_text:
                                        article.synthesis_article = article_text
                                        word_count = len(article_text.split())
                                        console.print(f"   📝 Synthesis article: {word_count} words")
                                    
                                    # Store structured data
                                    crawled_content = result.get("crawled_content", "")
                                    article_data = result.get("article_data", {})
                                    if crawled_content:
                                        article.crawled_content = crawled_content
                                    if article_data:
                                        article.article_data = article_data
                                
                                await session.commit()
                            
                            console.print(f"   ✓ Completed: {job_info['title'][:60]}...")
                            progress.advance(task)
                            return {**job_info, "result": updated_fact_check, "status": "completed"}
                        
                        elif current_status == "failed":
                            error_msg = status.get("error", "Unknown error")
                            
                            async with AsyncSessionLocal() as session:
                                fact_check_repo = FactCheckRepository(session)
                                fact_check = await fact_check_repo.get_by_job_id(job_id)
                                if fact_check:
                                    await fact_check_repo.update(
                                        fact_check.id,
                                        {
                                            "verdict": "ERROR",
                                            "credibility_score": -1,
                                            "summary": f"Synthesis fact-check failed: {error_msg}",
                                            "validation_results": {"error": error_msg}
                                        }
                                    )
                                    await session.commit()
                            
                            raise Exception(f"Job failed: {error_msg}")
                        
                        await asyncio.sleep(poll_interval)
                        attempt += 1
                
                # Timeout
                async with AsyncSessionLocal() as session:
                    fact_check_repo = FactCheckRepository(session)
                    fact_check = await fact_check_repo.get_by_job_id(job_id)
                    if fact_check:
                        await fact_check_repo.update(
                            fact_check.id,
                            {
                                "verdict": "TIMEOUT",
                                "credibility_score": -1,
                                "summary": f"Synthesis job timed out after {max_attempts * poll_interval}s ({(max_attempts * poll_interval)/60:.1f} min)",
                                "validation_results": {"error": "timeout", "max_wait_seconds": max_attempts * poll_interval}
                            }
                        )
                        await session.commit()
                
                raise Exception(f"Job timed out after {max_attempts * poll_interval}s ({(max_attempts * poll_interval)/60:.1f} minutes)")
                
            except Exception as e:
                console.print(f"   ⚠️  Failed: {job_info['title'][:60]}... - {e}")
                progress.advance(task)
                return {**job_info, "error": str(e), "status": "failed"}
        
        # Poll all jobs concurrently
        results = await asyncio.gather(*[poll_job(job) for job in submitted_jobs], return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                if result.get("status") == "completed":
                    completed_jobs.append(result)
                else:
                    failed_jobs.append(result)
        
        console.print(f"\n✅ [bold green]Completed {len(completed_jobs)}/{len(submitted_jobs)} synthesis fact-checks![/bold green]")
        if failed_jobs:
            console.print(f"⚠️  [yellow]Failed: {len(failed_jobs)} jobs[/yellow]\n")
        else:
            console.print()
        
        return completed_jobs


async def step_5_display_results():
    """Step 5: Display synthesis mode results"""
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]STEP 5: Synthesis Mode Results & Statistics[/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
    
    async with AsyncSessionLocal() as session:
        try:
            # Get statistics
            result = await session.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN fact_check_score IS NOT NULL THEN 1 END) as fact_checked,
                    COUNT(CASE WHEN synthesis_article IS NOT NULL THEN 1 END) as has_synthesis,
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
            
            # Display summary
            table = Table(title="📊 Synthesis Mode Test Summary", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", justify="right", style="green")
            
            table.add_row("Total Articles", str(stats.total))
            table.add_row("Fact-Checked", str(stats.fact_checked))
            table.add_row("With Synthesis Article", str(stats.has_synthesis))
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
            
            # Display sample synthesis articles
            result = await session.execute(text("""
                SELECT 
                    id, title, fact_check_score, fact_check_verdict, 
                    LENGTH(synthesis_article) as article_length,
                    CASE WHEN synthesis_article IS NOT NULL 
                         THEN ARRAY_LENGTH(STRING_TO_ARRAY(synthesis_article, ' '), 1) 
                         ELSE 0 END as word_count
                FROM articles
                WHERE fact_check_score IS NOT NULL
                ORDER BY fact_checked_at DESC
                LIMIT 5
            """))
            articles = result.fetchall()
            
            if articles:
                article_table = Table(title="📰 Synthesis Fact-Checked Articles", show_header=True, header_style="bold magenta")
                article_table.add_column("Title", style="cyan", max_width=40)
                article_table.add_column("Score", justify="center", style="yellow")
                article_table.add_column("Verdict", style="green")
                article_table.add_column("Words", justify="right", style="blue")
                
                for article_id, title, score, verdict, article_length, word_count in articles:
                    article_table.add_row(
                        title[:40] + "..." if len(title) > 40 else title,
                        str(score),
                        verdict or "N/A",
                        str(word_count) if word_count else "-"
                    )
                
                console.print(article_table)
                console.print()
            
            # Display API endpoints
            console.print(Panel.fit(
                "[bold yellow]Synthesis Mode API Endpoints:[/bold yellow]\n\n"
                "• List articles:\n"
                "  GET /api/v1/articles?category=politics\n\n"
                "• Get fact-check details:\n"
                "  GET /api/v1/articles/{article_id}/fact-check\n\n"
                "• Get synthesis article (NEW!):\n"
                "  GET /api/v1/articles/{article_id}/synthesis\n\n"
                "• Example article IDs:\n"
                f"  {', '.join(str(a[0]) for a in articles[:3]) if articles else 'N/A'}",
                title="🔗 Integration Info",
                border_style="green"
            ))
            
        except Exception as e:
            console.print(f"\n❌ [bold red]Error displaying results: {e}[/bold red]\n")
            raise


async def main():
    """Execute all steps with synthesis mode"""
    console.print("\n[bold green]╔════════════════════════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║   Fox News Politics - SYNTHESIS MODE Test Workflow        ║[/bold green]")
    console.print("[bold green]╚════════════════════════════════════════════════════════════╝[/bold green]\n")
    
    start_time = datetime.utcnow()
    
    try:
        await step_1_clear_database()
        article_count = await step_2_populate_articles()
        submitted_jobs = await step_3_trigger_fact_checks()
        completed_jobs = await step_4_poll_for_completion(submitted_jobs)
        await step_5_display_results()
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        console.print(f"\n[bold green]✅ Synthesis test completed in {elapsed/60:.1f} minutes![/bold green]\n")
        
        console.print("[bold yellow]Next Steps:[/bold yellow]")
        console.print("  • Review synthesis articles with Context & Emphasis")
        console.print("  • Test synthesis API endpoint with frontend")
        console.print("  • Check full narrative articles with citations")
        console.print("  • Review event timelines and margin notes\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test failed: {e}[/bold red]\n")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)
    finally:
        await engine.dispose()
        console.print("\n[dim]🔌 Database connections closed[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
