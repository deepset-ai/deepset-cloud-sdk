"""Progress bar for tracking file upload progress."""
from progress.bar import PixelBar


class ProgressBar(PixelBar):
    """Progress Bar Class."""

    suffix = "%(index)d/%(max)d elapsed: %(elapsed_minutes)s"

    @property
    def elapsed_minutes(self) -> str:
        """Returns the elapsed minutes the bar ha been active.

        :return str: Elapsed time message
        """
        return f"{int(self.elapsed/60)}m{self.elapsed%60}s"
