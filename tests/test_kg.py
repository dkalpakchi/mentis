"""Tests for TomGraph knowledge graph."""

import tempfile
import os
from pathlib import Path

import pytest

from mentis.kg.graphml import TomGraphGraphML as TomGraph


@pytest.fixture
def temp_graph():
    """Create a temporary TomGraph for testing."""
    with tempfile.NamedTemporaryFile(suffix=".graphml", delete=False) as f:
        temp_path = f.name
    
    kg = TomGraph(temp_path)
    yield kg
    
    # Cleanup
    if Path(temp_path).exists():
        os.unlink(temp_path)


def test_add_entity(temp_graph):
    """Test adding entities to the graph."""
    assert temp_graph.add_entity("Alice")
    assert "Alice" in temp_graph.graph.nodes
    assert temp_graph.graph.nodes["Alice"]["type"] == "person"
    
    # Adding same entity again should return False
    assert not temp_graph.add_entity("Alice")


def test_add_entity_with_type(temp_graph):
    """Test adding entities with custom types."""
    assert temp_graph.add_entity("Google", entity_type="organization")
    assert temp_graph.graph.nodes["Google"]["type"] == "organization"


def test_tom_attributes(temp_graph):
    """Test ToM attribute initialization."""
    temp_graph.add_entity("Bob")
    node = temp_graph.graph.nodes["Bob"]
    
    for attr in ["beliefs", "desires", "intentions", "emotions", "plans"]:
        assert attr in node
        assert node[attr] == "[]"


def test_update_tom(temp_graph):
    """Test updating ToM attributes."""
    temp_graph.add_entity("Charlie")
    temp_graph.update_tom("Charlie", "beliefs", ["the sky is blue"])
    
    info = temp_graph.get_entity_info("Charlie")
    # get_entity_info now returns parsed lists
    beliefs = info["beliefs"]
    assert "the sky is blue" in beliefs


def test_add_relationship(temp_graph):
    """Test adding relationships between entities."""
    temp_graph.add_relationship("Alice", "Bob", "FRIENDS")
    
    assert temp_graph.graph.has_node("Alice")
    assert temp_graph.graph.has_node("Bob")
    assert temp_graph.graph.has_edge("Alice", "Bob")
    
    edge_data = temp_graph.graph.get_edge_data("Alice", "Bob")
    assert edge_data["type"] == "FRIENDS"


def test_get_entity_info(temp_graph):
    """Test getting entity info."""
    temp_graph.add_entity("Dave")
    temp_graph.update_tom("Dave", "emotions", ["happy"])
    
    info = temp_graph.get_entity_info("Dave")
    assert info["type"] == "person"
    assert "emotions" in info
    
    # Non-existent entity
    assert temp_graph.get_entity_info("NonExistent") == {}


def test_save_and_load(temp_graph):
    """Test saving and loading the graph."""
    temp_graph.add_entity("Eve")
    temp_graph.update_tom("Eve", "plans", ["take over the world"])
    temp_graph.save()
    
    # Create new graph and load
    kg2 = TomGraph(temp_graph.file_path)
    assert "Eve" in kg2.graph.nodes


# Tests for new KG methods


def test_get_all_entities(temp_graph):
    """Test getting all entities from the graph."""
    temp_graph.add_entity("Alice")
    temp_graph.add_entity("Bob")
    
    entities = temp_graph.get_all_entities()
    assert isinstance(entities, list)
    assert "Alice" in entities
    assert "Bob" in entities


def test_set_tom_replaces_values(temp_graph):
    """Test that set_tom replaces existing values."""
    temp_graph.add_entity("Charlie")
    temp_graph.update_tom("Charlie", "beliefs", ["old belief"])
    
    # Verify old value is there
    info = temp_graph.get_entity_info("Charlie")
    beliefs = info["beliefs"]  # get_entity_info returns parsed lists
    assert "old belief" in beliefs
    
    # Set new values (should replace)
    temp_graph.set_tom("Charlie", "beliefs", ["new belief"])
    
    # Verify old value is gone, new value is there
    info = temp_graph.get_entity_info("Charlie")
    beliefs = info["beliefs"]
    assert "old belief" not in beliefs
    assert "new belief" in beliefs


def test_set_tom_adds_entity_if_not_exists(temp_graph):
    """Test that set_tom creates entity if it doesn't exist."""
    temp_graph.set_tom("NewPerson", "beliefs", ["belief"])
    assert "NewPerson" in temp_graph.graph.nodes


def test_set_tom_invalid_attribute(temp_graph):
    """Test that set_tom with invalid attribute does nothing."""
    temp_graph.add_entity("Dave")
    temp_graph.set_tom("Dave", "invalid_attr", ["value"])
    
    info = temp_graph.get_entity_info("Dave")
    assert "invalid_attr" not in info


def test_remove_relationship(temp_graph):
    """Test removing a relationship."""
    temp_graph.add_relationship("Alice", "Bob", "FRIENDS")
    assert temp_graph.graph.has_edge("Alice", "Bob")
    
    result = temp_graph.remove_relationship("Alice", "Bob", "FRIENDS")
    assert result is True
    assert not temp_graph.graph.has_edge("Alice", "Bob")


def test_remove_relationship_not_found(temp_graph):
    """Test removing a non-existent relationship returns False."""
    result = temp_graph.remove_relationship("Alice", "Bob", "FRIENDS")
    assert result is False


def test_query_tom(temp_graph):
    """Test querying ToM attributes."""
    
    temp_graph.add_entity("Eve")
    temp_graph.update_tom("Eve", "beliefs", ["belief1", "belief2"])
    
    beliefs = temp_graph.query_tom("Eve", "beliefs")
    assert isinstance(beliefs, list)
    assert "belief1" in beliefs
    assert "belief2" in beliefs


def test_query_tom_empty(temp_graph):
    """Test querying ToM for non-existent attribute."""
    temp_graph.add_entity("Frank")
    
    emotions = temp_graph.query_tom("Frank", "emotions")
    assert emotions == []


def test_query_tom_nonexistent_entity(temp_graph):
    """Test querying ToM for non-existent entity."""
    beliefs = temp_graph.query_tom("NonExistent", "beliefs")
    assert beliefs == []


def test_query_relationships(temp_graph):
    """Test querying relationships for an entity."""
    temp_graph.add_relationship("Alice", "Bob", "FRIENDS")
    temp_graph.add_relationship("Alice", "Charlie", "COLLEAGUES")
    
    relationships = temp_graph.query_relationships("Alice")
    assert len(relationships) == 2
    
    # Check structure
    for rel in relationships:
        assert "source" in rel
        assert "target" in rel
        assert "type" in rel
        assert "context" in rel


def test_query_relationships_with_type_filter(temp_graph):
    """Test querying relationships with type filter."""
    temp_graph.add_relationship("Alice", "Bob", "FRIENDS")
    temp_graph.add_relationship("Alice", "Charlie", "COLLEAGUES")
    
    friends = temp_graph.query_relationships("Alice", rel_type="FRIENDS")
    assert len(friends) == 1
    assert friends[0]["type"] == "FRIENDS"


def test_query_relationships_nonexistent_entity(temp_graph):
    """Test querying relationships for non-existent entity."""
    relationships = temp_graph.query_relationships("NonExistent")
    assert relationships == []


def test_query_by_attribute(temp_graph):
    """Test finding entities by ToM attribute value."""
    
    temp_graph.add_entity("Alice")
    temp_graph.add_entity("Bob")
    temp_graph.update_tom("Alice", "beliefs", ["the sky is blue"])
    temp_graph.update_tom("Bob", "beliefs", ["the sky is blue"])
    temp_graph.update_tom("Bob", "beliefs", ["grass is green"])
    
    # Find entities with "the sky is blue" belief
    entities = temp_graph.query_by_attribute("beliefs", "the sky is blue")
    assert "Alice" in entities
    assert "Bob" in entities
    
    # Find entities with "grass is green" belief
    entities = temp_graph.query_by_attribute("beliefs", "grass is green")
    assert "Bob" in entities
    assert "Alice" not in entities


def test_query_by_attribute_not_found(temp_graph):
    """Test query_by_attribute when no entities match."""
    temp_graph.add_entity("Alice")
    
    entities = temp_graph.query_by_attribute("beliefs", "nonexistent")
    assert entities == []
