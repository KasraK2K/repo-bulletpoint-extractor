"""Progress tracking and user feedback utilities."""
import sys
from typing import Optional, TextIO
from contextlib import contextmanager


class ProgressTracker:
    """Enhanced progress tracking with better user feedback."""
    
    def __init__(self, verbose: bool = True, output: Optional[TextIO] = None):
        self.verbose = verbose
        self.output = output or sys.stdout
        self._step = 0
        self._total_steps = 0
    
    def set_total_steps(self, total: int) -> None:
        """Set the total number of steps for progress tracking."""
        self._total_steps = total
        self._step = 0
    
    def step(self, message: str, details: Optional[str] = None) -> None:
        """Log a progress step with optional details."""
        if not self.verbose:
            return
        
        self._step += 1
        
        if self._total_steps > 0:
            progress = f"[{self._step}/{self._total_steps}]"
        else:
            progress = f"[{self._step}]"
        
        main_msg = f"{progress} {message}..."
        self.output.write(main_msg)
        self.output.flush()
        
        if details:
            self.output.write(f"\n  → {details}")
        
        self.output.write("\n")
        self.output.flush()
    
    def info(self, message: str) -> None:
        """Log an informational message."""
        if self.verbose:
            self.output.write(f"  ℹ {message}\n")
            self.output.flush()
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        if self.verbose:
            self.output.write(f"  ⚠ {message}\n")
            self.output.flush()
    
    def success(self, message: str) -> None:
        """Log a success message."""
        if self.verbose:
            self.output.write(f"  ✓ {message}\n")
            self.output.flush()
    
    def error(self, message: str) -> None:
        """Log an error message."""
        if self.verbose:
            self.output.write(f"  ✗ {message}\n")
            self.output.flush()
    
    @contextmanager
    def step_context(self, message: str):
        """Context manager for tracking a step with automatic completion."""
        if self.verbose:
            self.output.write(f"[{self._step + 1}] {message}...")
            self.output.flush()
        
        try:
            yield self
            if self.verbose:
                self.output.write(" ✓\n")
                self.output.flush()
            self._step += 1
        except Exception as e:
            if self.verbose:
                self.output.write(f" ✗ ({str(e)})\n")
                self.output.flush()
            raise