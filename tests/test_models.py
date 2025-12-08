"""
Unit tests for data models.

Tests the core data models including Advisory severity ranking.
"""

import unittest
from app.models.advisory import Advisory


class TestAdvisorySeverityRanking(unittest.TestCase):
    """Tests for Advisory severity ranking functionality."""
    
    def test_warning_severity_rank(self):
        """Test that Warning severity has the highest rank (3).
        
        Validates: Requirements 6.4
        """
        advisory = Advisory(
            type="Heat Warning",
            description="Excessive heat warning in effect",
            severity="Warning"
        )
        self.assertEqual(advisory.get_severity_rank(), 3)
    
    def test_advisory_severity_rank(self):
        """Test that Advisory severity has middle rank (2).
        
        Validates: Requirements 6.4
        """
        advisory = Advisory(
            type="Heat Advisory",
            description="Heat advisory in effect",
            severity="Advisory"
        )
        self.assertEqual(advisory.get_severity_rank(), 2)
    
    def test_watch_severity_rank(self):
        """Test that Watch severity has the lowest rank (1).
        
        Validates: Requirements 6.4
        """
        advisory = Advisory(
            type="Heat Watch",
            description="Heat watch in effect",
            severity="Watch"
        )
        self.assertEqual(advisory.get_severity_rank(), 1)
    
    def test_severity_ordering_warning_greater_than_advisory(self):
        """Test that Warning > Advisory in severity ranking.
        
        Validates: Requirements 6.4
        """
        warning = Advisory(type="Test", description="Test", severity="Warning")
        advisory = Advisory(type="Test", description="Test", severity="Advisory")
        
        self.assertGreater(warning.get_severity_rank(), advisory.get_severity_rank())
    
    def test_severity_ordering_advisory_greater_than_watch(self):
        """Test that Advisory > Watch in severity ranking.
        
        Validates: Requirements 6.4
        """
        advisory = Advisory(type="Test", description="Test", severity="Advisory")
        watch = Advisory(type="Test", description="Test", severity="Watch")
        
        self.assertGreater(advisory.get_severity_rank(), watch.get_severity_rank())
    
    def test_severity_ordering_warning_greater_than_watch(self):
        """Test that Warning > Watch in severity ranking.
        
        Validates: Requirements 6.4
        """
        warning = Advisory(type="Test", description="Test", severity="Warning")
        watch = Advisory(type="Test", description="Test", severity="Watch")
        
        self.assertGreater(warning.get_severity_rank(), watch.get_severity_rank())
    
    def test_case_insensitive_severity_warning(self):
        """Test that severity comparison is case-insensitive for Warning.
        
        Validates: Requirements 6.4
        """
        warning_upper = Advisory(type="Test", description="Test", severity="WARNING")
        warning_lower = Advisory(type="Test", description="Test", severity="warning")
        warning_mixed = Advisory(type="Test", description="Test", severity="Warning")
        
        self.assertEqual(warning_upper.get_severity_rank(), 3)
        self.assertEqual(warning_lower.get_severity_rank(), 3)
        self.assertEqual(warning_mixed.get_severity_rank(), 3)
    
    def test_case_insensitive_severity_advisory(self):
        """Test that severity comparison is case-insensitive for Advisory.
        
        Validates: Requirements 6.4
        """
        advisory_upper = Advisory(type="Test", description="Test", severity="ADVISORY")
        advisory_lower = Advisory(type="Test", description="Test", severity="advisory")
        advisory_mixed = Advisory(type="Test", description="Test", severity="Advisory")
        
        self.assertEqual(advisory_upper.get_severity_rank(), 2)
        self.assertEqual(advisory_lower.get_severity_rank(), 2)
        self.assertEqual(advisory_mixed.get_severity_rank(), 2)
    
    def test_case_insensitive_severity_watch(self):
        """Test that severity comparison is case-insensitive for Watch.
        
        Validates: Requirements 6.4
        """
        watch_upper = Advisory(type="Test", description="Test", severity="WATCH")
        watch_lower = Advisory(type="Test", description="Test", severity="watch")
        watch_mixed = Advisory(type="Test", description="Test", severity="Watch")
        
        self.assertEqual(watch_upper.get_severity_rank(), 1)
        self.assertEqual(watch_lower.get_severity_rank(), 1)
        self.assertEqual(watch_mixed.get_severity_rank(), 1)
    
    def test_unknown_severity_returns_zero(self):
        """Test that unknown severity types return rank 0.
        
        Validates: Requirements 6.4
        """
        unknown = Advisory(type="Test", description="Test", severity="Unknown")
        self.assertEqual(unknown.get_severity_rank(), 0)
    
    def test_empty_severity_returns_zero(self):
        """Test that empty severity string returns rank 0.
        
        Validates: Requirements 6.4
        """
        empty = Advisory(type="Test", description="Test", severity="")
        self.assertEqual(empty.get_severity_rank(), 0)


if __name__ == '__main__':
    unittest.main()
