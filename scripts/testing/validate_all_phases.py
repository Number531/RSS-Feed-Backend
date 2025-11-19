#!/usr/bin/env python3
"""
Complete Validation Script for All Phases (2, 3, 4)

Validates all frontend optimization columns across all 3 phases.
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
from rich.panel import Panel

console = Console()


async def validate():
    """Validate all 3 phases of migrations."""
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)
    
    try:
        async with engine.begin() as conn:
            console.print("\n")
            console.print(Panel.fit(
                "[bold cyan]Complete Frontend Optimization Validation[/bold cyan]\n"
                "[yellow]Phases 2, 3, and 4[/yellow]",
                border_style="cyan"
            ))
            console.print()
            
            # ═══════════════════════════════════════════════════
            # PHASE 2: Frontend Helper Columns
            # ═══════════════════════════════════════════════════
            console.print("[bold magenta]═══ PHASE 2: Frontend Helper Columns ═══[/bold magenta]\n")
            
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
            
            table = Table(title="Phase 2 Column Coverage", show_header=True)
            table.add_column("Column", style="cyan")
            table.add_column("Count", justify="right", style="yellow")
            table.add_column("Status", style="green")
            
            table.add_row("Total synthesis articles", str(total), "")
            table.add_row("has_synthesis", str(has_bool), 
                         "✅" if has_bool == total else "❌")
            table.add_row("synthesis_word_count", str(has_count),
                         "✅" if has_count == total else "❌")
            table.add_row("synthesis_preview", str(has_preview),
                         "✅" if has_preview == total else "❌")
            table.add_row("has_context_emphasis", str(has_context),
                         "✅" if has_context == total else "❌")
            table.add_row("has_timeline", str(has_timeline),
                         "✅" if has_timeline == total else "❌")
            
            console.print(table)
            console.print()
            
            phase2_pass = (has_bool == total and has_count == total and has_preview == total)
            
            # ═══════════════════════════════════════════════════
            # PHASE 3: Metadata Enrichment
            # ═══════════════════════════════════════════════════
            console.print("[bold magenta]═══ PHASE 3: Metadata Enrichment ═══[/bold magenta]\n")
            
            result = await conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(timeline_event_count) as has_timeline_count,
                    COUNT(reference_count) as has_ref_count,
                    COUNT(margin_note_count) as has_note_count,
                    COUNT(fact_check_mode) as has_mode,
                    COUNT(synthesis_generated_at) as has_timestamp,
                    AVG(timeline_event_count) as avg_timeline,
                    AVG(reference_count) as avg_refs,
                    AVG(margin_note_count) as avg_notes
                FROM articles
                WHERE synthesis_article IS NOT NULL
            """))
            
            row = result.fetchone()
            (total, has_timeline_count, has_ref_count, has_note_count, 
             has_mode, has_timestamp, avg_timeline, avg_refs, avg_notes) = row
            
            table = Table(title="Phase 3 Column Coverage", show_header=True)
            table.add_column("Column", style="cyan")
            table.add_column("Count", justify="right", style="yellow")
            table.add_column("Avg Value", justify="right", style="blue")
            table.add_column("Status", style="green")
            
            table.add_row("timeline_event_count", str(has_timeline_count), 
                         f"{avg_timeline:.1f}" if avg_timeline else "N/A",
                         "✅" if has_timeline_count == total else "❌")
            table.add_row("reference_count", str(has_ref_count), 
                         f"{avg_refs:.1f}" if avg_refs else "N/A",
                         "✅" if has_ref_count == total else "❌")
            table.add_row("margin_note_count", str(has_note_count), 
                         f"{avg_notes:.1f}" if avg_notes else "N/A",
                         "✅" if has_note_count == total else "❌")
            table.add_row("fact_check_mode", str(has_mode), "N/A",
                         "✅" if has_mode == total else "❌")
            table.add_row("synthesis_generated_at", str(has_timestamp), "N/A",
                         "✅" if has_timestamp == total else "❌")
            
            console.print(table)
            console.print()
            
            # Check fact_check_mode values
            result = await conn.execute(text("""
                SELECT fact_check_mode, COUNT(*) as count
                FROM articles
                WHERE synthesis_article IS NOT NULL
                GROUP BY fact_check_mode
                ORDER BY count DESC
            """))
            
            console.print("[bold yellow]Fact Check Mode Distribution:[/bold yellow]")
            for row in result:
                console.print(f"  {row[0]}: {row[1]} articles")
            console.print()
            
            phase3_pass = (has_timeline_count == total and has_ref_count == total and has_mode == total)
            
            # ═══════════════════════════════════════════════════
            # PHASE 4: UX Enhancements
            # ═══════════════════════════════════════════════════
            console.print("[bold magenta]═══ PHASE 4: UX Enhancements ═══[/bold magenta]\n")
            
            result = await conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(synthesis_read_minutes) as has_read_time,
                    COUNT(verdict_color) as has_color,
                    AVG(synthesis_read_minutes) as avg_read_time
                FROM articles
                WHERE synthesis_article IS NOT NULL
            """))
            
            row = result.fetchone()
            total, has_read_time, has_color, avg_read_time = row
            
            table = Table(title="Phase 4 Column Coverage", show_header=True)
            table.add_column("Column", style="cyan")
            table.add_column("Count", justify="right", style="yellow")
            table.add_column("Avg Value", justify="right", style="blue")
            table.add_column("Status", style="green")
            
            table.add_row("synthesis_read_minutes", str(has_read_time), 
                         f"{avg_read_time:.1f} min" if avg_read_time else "N/A",
                         "✅" if has_read_time == total else "❌")
            table.add_row("verdict_color", str(has_color), "N/A",
                         "✅" if has_color == total else "❌")
            
            console.print(table)
            console.print()
            
            # Check verdict color distribution
            result = await conn.execute(text("""
                SELECT verdict_color, COUNT(*) as count
                FROM articles
                WHERE synthesis_article IS NOT NULL
                GROUP BY verdict_color
                ORDER BY count DESC
            """))
            
            console.print("[bold yellow]Verdict Color Distribution:[/bold yellow]")
            for row in result:
                color_name = row[0] if row[0] else "NULL"
                count = row[1]
                console.print(f"  {color_name}: {count} articles")
            console.print()
            
            phase4_pass = (has_read_time == total and has_color == total)
            
            # ═══════════════════════════════════════════════════
            # INDEX VERIFICATION
            # ═══════════════════════════════════════════════════
            console.print("[bold magenta]═══ Index Verification ═══[/bold magenta]\n")
            
            result = await conn.execute(text("""
                SELECT indexname
                FROM pg_indexes 
                WHERE tablename = 'articles' 
                  AND (indexname LIKE '%synthesis%' OR indexname LIKE '%fact_check%' OR indexname LIKE '%verdict%')
                ORDER BY indexname
            """))
            
            indexes = [row[0] for row in result]
            
            expected_indexes = {
                'Phase 2': ['idx_articles_has_synthesis_v2', 'idx_articles_synthesis_ready', 'idx_articles_synthesis_preview_fts'],
                'Phase 3': ['idx_articles_fact_check_mode', 'idx_articles_synthesis_generated_at'],
                'Phase 4': ['idx_articles_verdict_color'],
                'Original': ['ix_articles_has_synthesis', 'ix_articles_synthesis_fact_checked', 'ix_articles_synthesis_fts']
            }
            
            for phase, phase_indexes in expected_indexes.items():
                console.print(f"[bold cyan]{phase}:[/bold cyan]")
                for idx in phase_indexes:
                    if idx in indexes:
                        console.print(f"  [green]✅ {idx}[/green]")
                    else:
                        console.print(f"  [red]❌ {idx} (MISSING)[/red]")
                console.print()
            
            # ═══════════════════════════════════════════════════
            # SAMPLE DATA VERIFICATION
            # ═══════════════════════════════════════════════════
            console.print("[bold magenta]═══ Sample Article Data ═══[/bold magenta]\n")
            
            result = await conn.execute(text("""
                SELECT 
                    title,
                    synthesis_word_count,
                    LENGTH(synthesis_preview) as preview_len,
                    has_context_emphasis,
                    has_timeline,
                    timeline_event_count,
                    reference_count,
                    margin_note_count,
                    fact_check_mode,
                    synthesis_read_minutes,
                    verdict_color
                FROM articles
                WHERE synthesis_article IS NOT NULL
                LIMIT 2
            """))
            
            for i, sample in enumerate(result, 1):
                console.print(f"[bold yellow]Article #{i}:[/bold yellow]")
                console.print(f"  Title: {sample[0][:60]}...")
                console.print(f"  Word count: {sample[1]:,}")
                console.print(f"  Preview length: {sample[2]} chars")
                console.print(f"  Has context/emphasis: {sample[3]}")
                console.print(f"  Has timeline: {sample[4]}")
                console.print(f"  Timeline events: {sample[5]}")
                console.print(f"  References: {sample[6]}")
                console.print(f"  Margin notes: {sample[7]}")
                console.print(f"  Fact-check mode: {sample[8]}")
                console.print(f"  Read time: {sample[9]} minutes")
                console.print(f"  Verdict color: {sample[10]}")
                console.print()
            
            # ═══════════════════════════════════════════════════
            # FINAL VERDICT
            # ═══════════════════════════════════════════════════
            all_pass = phase2_pass and phase3_pass and phase4_pass
            
            console.print(Panel.fit(
                f"[bold {'green' if phase2_pass else 'red'}]Phase 2: {'✅ PASS' if phase2_pass else '❌ FAIL'}[/bold {'green' if phase2_pass else 'red'}]\n"
                f"[bold {'green' if phase3_pass else 'red'}]Phase 3: {'✅ PASS' if phase3_pass else '❌ FAIL'}[/bold {'green' if phase3_pass else 'red'}]\n"
                f"[bold {'green' if phase4_pass else 'red'}]Phase 4: {'✅ PASS' if phase4_pass else '❌ FAIL'}[/bold {'green' if phase4_pass else 'red'}]\n\n"
                f"[bold {'green' if all_pass else 'red'}]Overall: {'✅ ALL PHASES VALIDATED' if all_pass else '❌ VALIDATION FAILED'}[/bold {'green' if all_pass else 'red'}]",
                border_style="green" if all_pass else "red",
                title="Migration Validation Results"
            ))
            console.print()
            
            return 0 if all_pass else 1
            
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
