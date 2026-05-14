"""Abstract base class for ToM Knowledge Graph implementations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List


# Default folder for knowledge graph files
KG_FOLDER = "kg_data"


class TomGraph(ABC):
    """Abstract base class for Theory of Mind Knowledge Graph."""

    def __init__(self, file_path: str | None = None, username: str | None = None):
        """Initialize the knowledge graph.

        Args:
            file_path: Full path to the graph file. If None, uses default based on username.
            username: User name to derive the default file path.
        """
        if file_path is None:
            file_path = self._get_default_path(username)
        self.file_path = file_path
        # Ensure the directory exists
        Path(self.file_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_default_path(self, username: str | None = None) -> str:
        """Get default file path based on username."""
        if username:
            extension = self._get_file_extension()
            return f"{KG_FOLDER}/{username}.{extension}"
        return f"{KG_FOLDER}/default.{self._get_file_extension()}"

    @abstractmethod
    def _get_file_extension(self) -> str:
        """Get the file extension for this KG type."""
        pass

    @abstractmethod
    def load(self):
        """Load graph from file."""
        pass  # pragma: no cover

    @abstractmethod
    def save(self):
        """Save graph to file."""
        pass  # pragma: no cover

    @abstractmethod
    def add_entity(self, name: str, entity_type: str = "person") -> bool:
        """Add a new entity node with ToM attribute lists."""
        pass  # pragma: no cover

    @abstractmethod
    def update_tom(self, entity: str, attribute: str, values: List[str]):
        """Update Theory of Mind attributes for an entity."""
        pass  # pragma: no cover

    @abstractmethod
    def add_relationship(
        self, source: str, target: str, rel_type: str, context: str = ""
    ):
        """Add a relationship edge between entities."""
        pass  # pragma: no cover

    @abstractmethod
    def get_entity_info(self, entity: str) -> Dict:
        """Get all ToM info for an entity."""
        pass  # pragma: no cover

    @abstractmethod
    def get_all_entities(self) -> List[str]:
        """Get list of all entity names in the graph."""
        pass  # pragma: no cover

    @abstractmethod
    def set_tom(self, entity: str, attribute: str, values: List[str]):
        """Set Theory of Mind attributes for an entity (replaces existing values)."""
        pass  # pragma: no cover

    @abstractmethod
    def remove_relationship(
        self, source: str, target: str, rel_type: str
    ) -> bool:
        """Remove a specific relationship.
        
        Args:
            source: Source entity name
            target: Target entity name  
            rel_type: Relationship type to remove
            
        Returns:
            True if relationship was removed, False if not found
        """
        pass  # pragma: no cover

    @abstractmethod
    def print_graph(self):
        """Print the current graph state."""
        pass  # pragma: no cover

    def query_tom(self, entity: str, attribute: str) -> List[str]:
        """Query ToM attributes for an entity.

        Args:
            entity: The entity name to query
            attribute: The ToM attribute (one of: beliefs, desires, intentions, emotions, plans)

        Returns:
            List of attribute values
        """
        raise NotImplementedError("query_tom must be implemented by the subclass")

    def query_relationships(
        self, entity: str, rel_type: str | None = None
    ) -> List[Dict]:
        """Query relationships for an entity.

        Args:
            entity: The entity name to query
            rel_type: Optional relationship type filter

        Returns:
            List of relationship dicts with source, target, type, context
        """
        raise NotImplementedError("query_relationships must be implemented by the subclass")

    def query_by_attribute(self, attribute: str, value: str) -> List[str]:
        """Find all entities with a specific ToM attribute value.

        Args:
            attribute: The ToM attribute to search
            value: The value to match

        Returns:
            List of entity names matching the query
        """
        raise NotImplementedError("query_by_attribute must be implemented by the subclass")
