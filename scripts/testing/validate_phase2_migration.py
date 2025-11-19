#!/usr/bin/env python3
"""
Phase 2 Migration Validation Script

Validates that all frontend helper columns were added correctly
and that computed values are accurate for all synthesis articles.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from rich.console import Console
from rich.table import Table

console = Console()


async def validate():
    """Validate Phase 2 migration."""
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    
    try:
        async with engine.begin() as conn:
            console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
            console.print("[bold cyan]Phase 2 Migration Validation[/bold cyan]")
            console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
            
            # Test 1: Check all synthesis articles have computed values
            result = await conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(has_synthesis) as has_bool,
                    COUNT(synthesis_word_count) as has_count,
                    COUNT(synthesis_preview) as has_preview,
                    COUNT(has_context_emphasis) as has_context,
                    COUNT(has_timeline) as has_timeline
                FROM articles
                WHERE synthesis_article IS NOT NULL
            """))
            
            row = result.fetchone()
            total, has_bool, has_count, has_preview, has_context, has_timeline = row
            
            table = Table(title="Computed Column Coverage", show_header=True)
            table.add_column("Column", style="cyan")
            table.add_column("Count", justify="right", style="yellow")
            table.add_column("Status", style="green")
            
            table.add_row("Total synthesis articles", str(total), "")
            table.add_row("has_synthesis", str(has_bool), 
                         "✅ PASS" if has_bool == total else "❌ FAIL")
            table.add_row("synthesis_word_count", str(has_count),
                         "✅ PASS" if has_count == total else "❌ FAIL")
            table.add_row("synthesis_preview", str(has_preview),
                         "✅ PASS" if has_preview == total else "❌ FAIL")
            table.add_row("has_context_emphasis", str(has_context),
                         "✅ PASS" if has_context == total else "❌ FAIL")
            table.add_row("has_timeline", str(has_timeline),
                         "✅ PASS" if has_timeline == total else "❌ FAIL")
            
            console.print(table)
            console.print()
            
            # Test 2: Verify word counts are reasonable
            result = await conn.execute(text("""
                SELECT 
                    MIN(synthesis_word_count) as min_words,
                    MAX(synthesis_word_count) as max_words,
                    AVG(synthesis_word_count) as avg_words
                FROM articles
                WHERE has_synthesis = true
            """))
            
            row = result.fetchone()
            min_words, max_words, avg_words = row
            
            console.print("[bold yellow]Word Count Statistics:[/bold yellow]")
            console.print(f"  Minimum: {min_words:,} words")
            console.print(f"  Maximum: {max_words:,} words")
            console.print(f"  Average: {avg_words:,.0f} words")
            
            # Validate range (synthesis articles should be 1,400-2,500 words)
            if min_words >= 1000 and max_words <= 3000:
                console.print("  [green]✅ Word counts within expected range (1,000-3,000)[/green]\n")
            else:
                console.print("  [yellow]⚠️  Word counts outside typical range - verify manually[/yellow]\n")
            
            # Test 3: Verify preview length
            result = await conn.execute(text("""
                SELECT 
                    MIN(LENGTH(synthesis_preview)) as min_preview,
                    MAX(LENGTH(synthesis_preview)) as max_preview,
                    AVG(LENGTH(synthesis_preview)) as avg_preview
                FROM articles
                WHERE has_synthesis = true
            """))
            
            row = result.fetchone()
            min_preview, max_preview, avg_preview = row
            
            console.print("[bold yellow]Preview Statistics:[/bold yellow]")
            console.print(f"  Minimum: {min_preview} characters")
            console.print(f"  Maximum: {max_preview} characters")
            console.print(f"  Average: {avg_preview:.0f} characters")
            
            # Preview should be exactly 500 chars (or less if article is shorter)
            if max_preview <= 500:
                console.print("  [green]✅ Preview lengths correct (≤500 chars)[/green]\n")
            else:
                console.print("  [red]❌ Preview length exceeds 500 chars - check migration[/red]\n")
            
            # Test 4: Check indexes
            result = await conn.execute(text("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'articles' 
                  AND indexname LIKE '%synthesis%'
                ORDER BY indexname
            """))
            
            indexes = result.fetchall()
            
            console.print("[bold yellow]Indexes Created:[/bold yellow]")
            expected_indexes = [
                'idx_articles_has_synthesis',
                'idx_articles_has_synthesis_v2',
                'idx_articles_synthesis_fts',
                'idx_articles_synthesis_preview_fts',
                'idx_articles_synthesis_ready'
            ]
            
            found_indexes = [idx[0] for idx in indexes]
            for idx_name in found_indexes:
                console.print(f"  [green]✅ {idx_name}[/green]")
            
            console.print()
            
            # Test 5: Test query performance
            console.print("[bold yellow]Testing Query Performance:[/bold yellow]")
            
            # Query 1: Filter by has_synthesis
            result = await conn.execute(text("""
                EXPLAIN ANALYZE
                SELECT COUNT(*) 
                FROM articles 
                WHERE has_synthesis = true
            """))
            
            explain_output = [row[0] for row in result]
            execution_time = [line for line in explain_output if 'Execution Time' in line]
            if execution_time:
                console.print(f"  Filter query: {execution_time[0]}")
            
            # Query 2: Get preview
            result = await conn.execute(text("""
                SELECT 
                    title,
                    synthesis_word_count,
                    LENGTH(synthesis_preview) as preview_length,
                    has_context_emphasis,
                    has_timeline
                FROM articles
                WHERE has_synthesis = true
                LIMIT 1
            """))
            
            sample = result.fetchone()
            if sample:
                console.print(f"\n[bold yellow]Sample Article Verification:[/bold yellow]")
                console.print(f"  Title: {sample[0][:50]}...")
                console.print(f"  Word count: {sample[1]:,}")
                console.print(f"  Preview length: {sample[2]} chars")
                console.print(f"  Has context/emphasis: {sample[3]}")
                console.print(f"  Has timeline: {sample[4]}")
            
            # Final verdict
            console.print("\n[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]")
            
            all_pass = (
                has_bool == total and
                has_count == total and
                has_preview == total and
                max_preview <= 500 and
                min_words >= 1000
            )
            
            if all_pass:
                console.print("[bold green]✅ Phase 2 Migration Validated Successfully![/bold green]")
                console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
                return 0
            else:
                console.print("[bold red]❌ Phase 2 Migration Validation Failed - Review Output Above[/bold red]")
                console.print("[bold cyan]═══════════════════════════════════════════════════════════[/bold cyan]\n")
                return 1
            
    except Exception as e:
        console.print(f"\n[bold red]❌ Validation Error: {e}[/bold red]\n")
        import traceback
        console.print(traceback.format_exc())
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(validate())
    sys.exit(exit_code)
