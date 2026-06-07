"""Human and machine report rendering."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table

from vectormeta.limits import advisory_limit_message, get_target_limit, get_target_limits
from vectormeta.models import FixResult, RecordAnalysis, ScanReport


def bytes_to_kb(size_bytes: int) -> float:
    """Convert bytes to KiB."""
    return size_bytes / 1024


def scan_report_to_dict(report: ScanReport, *, top: int) -> dict[str, Any]:
    """Convert a scan report to stable JSON-serializable data."""
    target_limit = get_target_limit(report.target)
    advisory_message = advisory_limit_message(report.target, report.limit_bytes)
    return {
        "target": report.target,
        "limit_bytes": report.limit_bytes,
        "limit_kb": round(bytes_to_kb(report.limit_bytes), 3),
        "limit_policy": target_limit.policy,
        "limit_note": target_limit.note,
        "limit_warning": advisory_message,
        "total_records": report.total_records,
        "oversized_count": report.oversized_count,
        "oversized_records": [
            _record_analysis_to_dict(record) for record in report.oversized_records[:top]
        ],
    }


def render_scan_report(console: Console, report: ScanReport, *, top: int) -> None:
    """Render a human-readable scan report."""
    console.print(f"[bold]Target:[/bold] {report.target}")
    console.print(
        f"[bold]Metadata limit:[/bold] {report.limit_bytes} bytes "
        f"({bytes_to_kb(report.limit_bytes):.2f} KB)"
    )
    advisory_message = advisory_limit_message(report.target, report.limit_bytes)
    if advisory_message is not None:
        console.print(f"[yellow]Warning:[/yellow] {advisory_message}")
    console.print(f"[bold]Records scanned:[/bold] {report.total_records}")
    color = "red" if report.oversized_count else "green"
    console.print(f"[bold]Oversized records:[/bold] [{color}]{report.oversized_count}[/{color}]")

    table = Table(title=f"Top {top} Oversized Records")
    table.add_column("Record ID", overflow="fold")
    table.add_column("Metadata", justify="right")
    table.add_column("Over Limit", justify="right")
    table.add_column("Largest Fields", overflow="fold")
    table.add_column("Suggested Moves", overflow="fold")

    for record in report.oversized_records[:top]:
        largest = ", ".join(
            f"{field.field_name} ({field.size_kb:.1f} KB)" for field in record.largest_fields[:3]
        )
        suggestions = ", ".join(field.field_name for field in record.largest_fields[:3])
        table.add_row(
            record.record_id,
            f"{record.metadata_size_bytes} B / {record.metadata_size_kb:.2f} KB",
            f"{record.over_limit_by_bytes} B",
            largest,
            suggestions,
        )

    if report.oversized_count:
        console.print(table)
    else:
        console.print("[green]All records are within the configured metadata limit.[/green]")


def render_fix_summary(console: Console, result: FixResult, *, dry_run: bool) -> None:
    """Render a human-readable fix summary."""
    action = "would update" if dry_run else "updated"
    console.print(
        f"[bold]Fix summary:[/bold] {action} {len(result.cleaned_records)} records; "
        f"{result.changed_count} records have sidecar payloads."
    )
    if result.warnings:
        warning_table = Table(title="Warnings")
        warning_table.add_column("Record ID", overflow="fold")
        warning_table.add_column("Message", overflow="fold")
        for warning in result.warnings:
            warning_table.add_row(warning.record_id, warning.message)
        console.print(warning_table)


def render_limits(console: Console) -> None:
    """Render known target metadata limits."""
    table = Table(title="Vector DB Metadata Limit Presets")
    table.add_column("Target")
    table.add_column("Default Limit", justify="right")
    table.add_column("Policy")
    table.add_column("Note", overflow="fold")
    for target_limit in get_target_limits():
        if target_limit.limit_bytes is None:
            limit = "custom"
        else:
            limit = f"{target_limit.limit_bytes} B / {target_limit.limit_bytes / 1024:.0f} KB"
        table.add_row(target_limit.name, limit, target_limit.policy, target_limit.note)
    console.print(table)
    console.print(
        "[dim]Limits and service behavior can change. Verify official vector database docs "
        "for production limits.[/dim]"
    )


def _record_analysis_to_dict(record: RecordAnalysis) -> dict[str, Any]:
    return {
        "id": record.record_id,
        "metadata_size_bytes": record.metadata_size_bytes,
        "metadata_size_kb": round(record.metadata_size_kb, 3),
        "over_limit_by_bytes": record.over_limit_by_bytes,
        "largest_fields": [
            {
                "field": field.field_name,
                "size_bytes": field.size_bytes,
                "size_kb": round(field.size_kb, 3),
            }
            for field in record.largest_fields
        ],
        "suggested_move_fields": [field.field_name for field in record.largest_fields[:3]],
    }
