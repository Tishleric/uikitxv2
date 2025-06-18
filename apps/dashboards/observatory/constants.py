"""Constants for Observatory Dashboard"""

from typing import List, Dict, Any

# Database configuration
OBSERVATORY_DB_PATH = "logs/observatory.db"

# Column definitions for the 7-column trace table
COLUMN_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "Process",
        "id": "process",
        "type": "text",
        "width": "25%",
        "sortable": True,
        "filterable": True,
    },
    {
        "name": "Data",
        "id": "data",
        "type": "text", 
        "width": "15%",
        "sortable": True,
        "filterable": True,
    },
    {
        "name": "Data Type",
        "id": "data_type",
        "type": "text",
        "width": "10%",
        "sortable": True,
        "filterable": True,
    },
    {
        "name": "Exception",
        "id": "exception",
        "type": "text",
        "width": "15%",
        "sortable": True,
        "filterable": True,
    },
    {
        "name": "Timestamp",
        "id": "timestamp",
        "type": "datetime",
        "width": "15%",
        "sortable": True,
        "filterable": True,
    },
    {
        "name": "Status",
        "id": "status",
        "type": "text",
        "width": "10%",
        "sortable": True,
        "filterable": True,
    },
    {
        "name": "Duration (ms)",
        "id": "duration_ms",
        "type": "numeric",
        "width": "10%",
        "sortable": True,
        "filterable": True,
    },
]

# Tab configuration - 5 tabs without Cytoscape for now
TAB_CONFIGURATION = [
    {
        "id": "overview",
        "label": "Overview",
        "icon": "📊",
        "description": "System health metrics and recent activity",
    },
    {
        "id": "trace-explorer", 
        "label": "Trace Explorer",
        "icon": "🔍",
        "description": "Detailed function trace data with filtering",
    },
    {
        "id": "code-inspector",
        "label": "Code Inspector",
        "icon": "📝",
        "description": "View source code and performance metrics",
    },
    {
        "id": "alerts",
        "label": "Alerts",
        "icon": "🚨",
        "description": "Error patterns and stale data detection",
    },
    {
        "id": "settings",
        "label": "Settings",
        "icon": "⚙️",
        "description": "Data retention and monitoring configuration",
    },
]

# Query limits
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
MAX_EXPORT_ROWS = 10000

# Status colors (matching theme)
STATUS_COLORS = {
    "OK": "#2dc26b",      # Success green
    "ERR": "#e55353",     # Danger red
    "WARN": "#f0ad4e",    # Warning yellow
}

# Refresh intervals (seconds)
REFRESH_INTERVALS = {
    "overview": 5,        # Overview metrics
    "traces": 10,         # Trace table
    "alerts": 30,         # Alert checks
}

# Retention defaults
DEFAULT_RETENTION_HOURS = 6
MIN_RETENTION_HOURS = 1
MAX_RETENTION_HOURS = 168  # 7 days 