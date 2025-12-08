"""
Advisory Data Models

This module defines data models for weather advisories.
"""

from dataclasses import dataclass


@dataclass
class Advisory:
    """Weather advisory information."""
    type: str
    description: str
    severity: str  # "Warning", "Advisory", "Watch"
    
    def get_severity_rank(self) -> int:
        """Return numeric rank for severity comparison.
        
        Returns:
            int: Higher number = more severe (Warning=3, Advisory=2, Watch=1)
        """
        severity_map = {
            'warning': 3,
            'advisory': 2,
            'watch': 1
        }
        return severity_map.get(self.severity.lower(), 0)
