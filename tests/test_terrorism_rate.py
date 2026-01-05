
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from app.services.rating_engine import get_terrorism_rate_per_mille

@pytest.fixture
def mock_db_engine():
    with patch("app.services.rating_engine.engine") as mock_engine:
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        yield mock_conn

def test_terrorism_rate_residential_low_si(mock_db_engine):
    """Test Residential slab <= 150 Cr (actually usually it's just one rate or slab based)"""
    # Mock return value
    mock_db_engine.execute.return_value.scalar.return_value = 0.10
    
    rate = get_terrorism_rate_per_mille(occupancy_type="Residential", total_si=1000000.0)
    
    assert rate == Decimal("0.10")
    # Verify strict total_si argument usage
    mock_db_engine.execute.assert_called_once()
    call_args = mock_db_engine.execute.call_args[1]
    assert call_args['ot'] == "Residential"
    assert call_args['tsi'] == 1000000.0

def test_terrorism_rate_residential_high_si(mock_db_engine):
    """Test Residential slab > 150 Cr"""
    mock_db_engine.execute.return_value.scalar.return_value = 0.15
    
    rate = get_terrorism_rate_per_mille(occupancy_type="Residential", total_si=2000000000.0)
    
    assert rate == Decimal("0.15")

def test_terrorism_rate_not_found(mock_db_engine):
    """Validation: If no slab found -> raise explicit ValueError"""
    mock_db_engine.execute.return_value.scalar.return_value = None
    
    with pytest.raises(ValueError) as exc:
        get_terrorism_rate_per_mille(occupancy_type="Unknown", total_si=50000.0)
    
    assert "No terrorism rate found" in str(exc.value)

def test_terrorism_rate_missing_arg_error():
    """Verify that calling without total_si (or with wrong name) raises TypeError"""
    # This ensures the signature change is effective and we catch regressions
    with pytest.raises(TypeError):
        get_terrorism_rate_per_mille(occupancy_type="Residential") # Missing total_si

