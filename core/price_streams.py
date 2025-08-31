from typing import Protocol


class PriceBatchPublisher(Protocol):
    """Protocol for publishing a batch of price rows.

    Implementations should serialize the provided Arrow table and deliver it to
    the configured transport (e.g., Redis channel).
    """

    def publish(self, batch_id: str, arrow_table) -> None:
        """Publish a complete batch.

        Args:
            batch_id: Unique identifier for the batch (e.g., timestamp token)
            arrow_table: pyarrow.Table containing rows for this batch
        """
        ...

