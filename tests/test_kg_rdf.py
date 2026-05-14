"""Tests for RDF Knowledge Graph implementation."""

import tempfile
import os
from pathlib import Path

import pytest

from mentis.kg.rdf import TomGraphRDF


# Test data for parametrized tests
TOM_ATTRIBUTES = ["beliefs", "desires", "intentions", "emotions", "plans"]
ENTITY_TYPES = [
    ("person", "Person"),
    ("organization", "Organization"),
    ("location", "Place"),
]


@pytest.fixture
def temp_rdf_graph():
    """Create a temporary RDF ToMGraph for testing (default, no SPARQL)."""
    with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
        temp_path = f.name

    kg = TomGraphRDF(temp_path)
    yield kg

    # Cleanup
    if Path(temp_path).exists():
        os.unlink(temp_path)


@pytest.fixture
def temp_sparql_graph():
    """Create a temporary RDF ToMGraph with SPARQL enabled."""
    with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
        temp_path = f.name

    kg = TomGraphRDF(temp_path, use_sparql=True)
    yield kg

    # Cleanup
    if Path(temp_path).exists():
        os.unlink(temp_path)


@pytest.fixture(params=[False, True])
def any_rdf_graph(request):
    """Parametrized fixture that yields both regular and SPARQL-enabled graphs."""
    with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
        temp_path = f.name

    kg = TomGraphRDF(temp_path, use_sparql=request.param)
    yield kg

    # Cleanup
    if Path(temp_path).exists():
        os.unlink(temp_path)


class TestRDFBasics:
    """Basic RDF KG tests - work with both SPARQL and non-SPARQL modes."""

    @pytest.mark.parametrize("use_sparql", [False, True])
    def test_add_entity(self, use_sparql):
        """Test adding entities to RDF graph."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        assert kg.add_entity("Alice")

        # Entity should be in the graph
        info = kg.get_entity_info("Alice")
        assert info["type"] == "Person"  # RDF uses schema.org which capitalizes

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("entity_type,expected_type", ENTITY_TYPES)
    def test_add_entity_with_type(self, entity_type, expected_type):
        """Test adding entities with custom types."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path)
        assert kg.add_entity("TestEntity", entity_type=entity_type)
        info = kg.get_entity_info("TestEntity")
        assert info["type"] == expected_type

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("tom_key", TOM_ATTRIBUTES)
    def test_update_tom(self, tom_key):
        """Test updating ToM attributes in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path)
        kg.add_entity("Bob")
        kg.update_tom("Bob", tom_key, [f"{tom_key} value"])

        values = kg.query_tom("Bob", tom_key)
        assert f"{tom_key} value" in values

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("rel_type", ["FRIENDS", "COLLEAGUES", "KNOWS"])
    def test_add_relationship(self, rel_type):
        """Test adding relationships in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path)
        kg.add_entity("Alice")
        kg.add_entity("Bob")
        kg.add_relationship("Alice", "Bob", rel_type)

        relationships = kg.query_relationships("Alice")
        assert len(relationships) == 1
        assert relationships[0]["target"] == "Bob"
        assert relationships[0]["type"] == rel_type

        if Path(temp_path).exists():
            os.unlink(temp_path)

    def test_save_and_load(self, temp_rdf_graph):
        """Test saving and loading RDF graph."""
        temp_rdf_graph.add_entity("Alice")
        temp_rdf_graph.update_tom("Alice", "beliefs", ["test"])
        temp_rdf_graph.save()

        # Create new graph and load
        kg2 = TomGraphRDF(temp_rdf_graph.file_path)
        info = kg2.get_entity_info("Alice")
        assert "Alice" in kg2.get_all_entities()


class TestRDFQueryMethods:
    """Tests for RDF query methods - work with both SPARQL and non-SPARQL modes."""

    @pytest.mark.parametrize("use_sparql", [False, True])
    def test_get_all_entities(self, use_sparql):
        """Test getting all entities from RDF graph."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        kg.add_entity("Alice")
        kg.add_entity("Bob")

        entities = kg.get_all_entities()
        assert "Alice" in entities
        assert "Bob" in entities

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("use_sparql", [False, True])
    def test_set_tom_replaces_values(self, use_sparql):
        """Test that set_tom replaces existing values in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        kg.add_entity("Charlie")
        kg.update_tom("Charlie", "beliefs", ["old belief"])

        # Verify old value is there
        beliefs = kg.query_tom("Charlie", "beliefs")
        assert "old belief" in beliefs

        # Set new values (should replace)
        kg.set_tom("Charlie", "beliefs", ["new belief"])

        # Verify old value is gone, new value is there
        beliefs = kg.query_tom("Charlie", "beliefs")
        assert "old belief" not in beliefs
        assert "new belief" in beliefs

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("use_sparql", [False, True])
    def test_remove_relationship(self, use_sparql):
        """Test removing a relationship in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        kg.add_entity("Alice")
        kg.add_entity("Bob")
        kg.add_relationship("Alice", "Bob", "FRIENDS")

        result = kg.remove_relationship("Alice", "Bob", "FRIENDS")
        assert result is True

        relationships = kg.query_relationships("Alice")
        assert len(relationships) == 0

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("use_sparql", [False, True])
    def test_remove_relationship_not_found(self, use_sparql):
        """Test removing non-existent relationship in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        result = kg.remove_relationship("Alice", "Bob", "FRIENDS")
        assert result is False

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("use_sparql", [False, True])
    def test_query_tom(self, use_sparql):
        """Test querying ToM attributes in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        kg.add_entity("Eve")
        kg.update_tom("Eve", "beliefs", ["belief1", "belief2"])

        beliefs = kg.query_tom("Eve", "beliefs")
        assert "belief1" in beliefs
        assert "belief2" in beliefs

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize("use_sparql", [False, True])
    def test_query_by_attribute(self, use_sparql):
        """Test finding entities by ToM attribute value in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        kg.add_entity("Alice")
        kg.add_entity("Bob")
        kg.update_tom("Alice", "beliefs", ["the sky is blue"])
        kg.update_tom("Bob", "beliefs", ["the sky is blue"])

        entities = kg.query_by_attribute("beliefs", "the sky is blue")
        assert "Alice" in entities
        assert "Bob" in entities

        if Path(temp_path).exists():
            os.unlink(temp_path)

    @pytest.mark.parametrize(
        "use_sparql,rel_type",
        [
            (False, "FRIENDS"),
            (False, "COLLEAGUES"),
            (True, "FRIENDS"),
            (True, "COLLEAGUES"),
        ],
    )
    def test_query_relationships_with_filter(self, use_sparql, rel_type):
        """Test querying relationships with type filter in RDF."""
        with tempfile.NamedTemporaryFile(suffix=".ttl", delete=False) as f:
            temp_path = f.name

        kg = TomGraphRDF(temp_path, use_sparql=use_sparql)
        kg.add_entity("Alice")
        kg.add_entity("Bob")
        kg.add_entity("Charlie")
        kg.add_relationship("Alice", "Bob", "FRIENDS")
        kg.add_relationship("Alice", "Charlie", "COLLEAGUES")

        filtered = kg.query_relationships("Alice", rel_type=rel_type)

        if rel_type == "FRIENDS":
            assert len(filtered) == 1
            assert filtered[0]["type"] == "FRIENDS"
            assert filtered[0]["target"] == "Bob"
        else:
            assert len(filtered) == 1
            assert filtered[0]["type"] == "COLLEAGUES"
            assert filtered[0]["target"] == "Charlie"

        if Path(temp_path).exists():
            os.unlink(temp_path)


class TestSPARQLSpecific:
    """Tests specifically for SPARQL-enabled mode."""

    def test_sparql_query_tom_complex(self, temp_sparql_graph):
        """Test complex SPARQL ToM queries."""
        temp_sparql_graph.add_entity("Alice")
        temp_sparql_graph.update_tom(
            "Alice", "beliefs", ["sky is blue", "grass is green"]
        )
        temp_sparql_graph.update_tom("Alice", "desires", ["be happy"])

        beliefs = temp_sparql_graph.query_tom("Alice", "beliefs")
        assert "sky is blue" in beliefs
        assert "grass is green" in beliefs

        desires = temp_sparql_graph.query_tom("Alice", "desires")
        assert "be happy" in desires

    def test_sparql_query_by_attribute_multiple_matches(self, temp_sparql_graph):
        """Test SPARQL query finding multiple entities with same attribute."""
        temp_sparql_graph.add_entity("Alice")
        temp_sparql_graph.add_entity("Bob")
        temp_sparql_graph.add_entity("Charlie")

        # All three share the same belief
        for name in ["Alice", "Bob", "Charlie"]:
            temp_sparql_graph.update_tom(name, "beliefs", ["shared belief"])

        entities = temp_sparql_graph.query_by_attribute("beliefs", "shared belief")
        assert "Alice" in entities
        assert "Bob" in entities
        assert "Charlie" in entities
        assert len(entities) == 3

    def test_sparql_no_relationships(self, temp_sparql_graph):
        """Test SPARQL query when no relationships exist."""
        temp_sparql_graph.add_entity("Alice")
        temp_sparql_graph.add_entity("Bob")

        relationships = temp_sparql_graph.query_relationships("Alice")
        assert relationships == []
