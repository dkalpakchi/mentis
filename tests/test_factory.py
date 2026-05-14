"""Tests for factory functions and module-level APIs."""

import tempfile
import os
from pathlib import Path

import pytest

from mentis.kg import get_kg
from mentis.kg.graphml import TomGraphGraphML
from mentis.kg.rdf import TomGraphRDF


@pytest.fixture
def temp_file():
    """Create a temporary file path."""
    with tempfile.NamedTemporaryFile(suffix=".graphml", delete=False) as f:
        temp_path = f.name
    yield temp_path
    if Path(temp_path).exists():
        os.unlink(temp_path)


class TestGetKG:
    """Tests for get_kg factory function."""

    def test_get_graphml_kg(self, temp_file):
        """Test getting GraphML KG."""
        kg = get_kg(kg_type="graphml", file_path=temp_file)
        assert isinstance(kg, TomGraphGraphML)

    def test_get_rdf_kg(self, temp_file):
        """Test getting RDF KG."""
        # Change suffix to .ttl for RDF
        temp_path = temp_file.replace(".graphml", ".ttl")
        kg = get_kg(kg_type="rdf", file_path=temp_path)
        assert isinstance(kg, TomGraphRDF)

    def test_get_default_graphml(self, temp_file):
        """Test that default KG type is GraphML."""
        kg = get_kg(file_path=temp_file)
        assert isinstance(kg, TomGraphGraphML)

    def test_get_kg_with_username(self, temp_file):
        """Test getting KG with username."""
        kg = get_kg(kg_type="graphml", username="test_user")
        assert isinstance(kg, TomGraphGraphML)
        assert "test_user" in kg.file_path
