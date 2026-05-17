from typing import Any, Dict, List, Optional


def build_citation(
    source: str,
    row_count: int,
    columns_used: List[str],
    period: Optional[Dict[str, Any]] = None,
    metric_sources: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "source": source,
        "row_count": row_count,
        "columns_used": columns_used,
        "period": {
            "period_label": period.get("period_label") if period else None,
            "start_date": period.get("start_date") if period else None,
            "end_date": period.get("end_date") if period else None,
        },
        "metric_sources": metric_sources or {},
    }


def build_multi_source_citation(
    sources: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "sources": sources,
    }