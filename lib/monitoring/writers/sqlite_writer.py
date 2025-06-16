"""SQLite writer for observability data - Phase 1 stub"""


class SQLiteWriter:
    """
    Writes observability data to SQLite database.
    
    Phase 1: Empty stub implementation
    """
    
    def __init__(self, db_path: str = "logs/observability.db"):
        self.db_path = db_path
    
    def write_batch(self, records):
        """Write a batch of records - Phase 1 stub"""
        pass
    
    def close(self):
        """Close database connection - Phase 1 stub"""
        pass 