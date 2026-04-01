"""Tests for the InBody PDF extractor — uses a synthetic minimal PDF."""
import io
import pytest
from unittest.mock import patch, MagicMock

from ..services.pdf_extractor import extract_metrics, _safe_float
from ..models.metric import STANDARD_METRIC_KEYS


class TestSafeFloat:
    def test_valid_number(self):
        assert _safe_float("12.5") == 12.5

    def test_number_with_comma(self):
        assert _safe_float("1,234") == 1234.0

    def test_invalid_string(self):
        assert _safe_float("N/A") is None

    def test_none_input(self):
        assert _safe_float(None) is None  # type: ignore


class TestExtractMetrics:
    def test_returns_all_standard_keys(self):
        """extract_metrics must return dict with all STANDARD_METRIC_KEYS."""
        sample_text = """
        Body Weight 75.5 kg
        Skeletal Muscle Mass 32.1 kg
        Body Fat Mass 18.3 kg
        Percent Body Fat 24.3 %
        Fat-Free Mass 57.2 kg
        Total Body Water 42.5 L
        Intracellular Water 27.0 L
        Extracellular Water 15.5 L
        ECW/TBW 0.365
        Protein 11.5 kg
        Minerals 3.8 kg
        BMI 24.5
        Basal Metabolic Rate 1750 kcal
        Visceral Fat Level 8
        """
        with patch("pdfplumber.open") as mock_open:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = sample_text
            mock_open.return_value.__enter__.return_value.pages = [mock_page]

            result = extract_metrics(b"fake-pdf")

        assert set(result.keys()) == set(STANDARD_METRIC_KEYS)

    def test_extracts_body_weight(self):
        sample_text = "Body Weight 82.0 kg"
        with patch("pdfplumber.open") as mock_open:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = sample_text
            mock_open.return_value.__enter__.return_value.pages = [mock_page]
            result = extract_metrics(b"fake")
        assert result["body_weight_kg"] == 82.0

    def test_missing_metrics_are_none(self):
        with patch("pdfplumber.open") as mock_open:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = ""
            mock_open.return_value.__enter__.return_value.pages = [mock_page]
            result = extract_metrics(b"fake")
        assert all(v is None for v in result.values())
