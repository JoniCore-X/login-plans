from datetime import UTC, datetime

from app.application.ports.clock import Clock


class FixedClock(Clock):
    def __init__(
        self,
        now: datetime | None = None,
    ) -> None:
        self.current = now or datetime(
            2026,
            1,
            1,
            tzinfo=UTC,
        )

    def now(self) -> datetime:
        return self.current
