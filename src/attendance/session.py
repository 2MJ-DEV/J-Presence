"""Temporary in-memory de-duplication for camera detections."""

from datetime import datetime, timedelta


class DetectionCooldown:
    """Prevent repeated frames from creating repeated events."""

    def __init__(self, cooldown_seconds: int) -> None:
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._last_seen: dict[int, datetime] = {}

    def should_accept(self, student_id: int, now: datetime | None = None) -> bool:
        """Return True only when the student is outside the cooldown window."""

        current_time = now or datetime.now()
        previous = self._last_seen.get(student_id)
        if previous and current_time - previous < self.cooldown:
            return False

        self._last_seen[student_id] = current_time
        return True
