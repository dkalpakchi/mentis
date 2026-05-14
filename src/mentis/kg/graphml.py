"""GraphML-based Knowledge Graph with Theory of Mind attributes."""

import json
from pathlib import Path
from typing import Dict, List

import networkx as nx

from mentis.states import get_tom_attributes
from mentis.kg.base import TomGraph
from mentis.colors import (
    print_internal,
    print_header,
    colorize,
    Colors,
    print_tom_label,
    print_entity,
    print_relationship,
    print_separator,
)


class TomGraphGraphML(TomGraph):
    """GraphML-based Knowledge Graph with Theory of Mind attributes."""

    def _get_file_extension(self) -> str:
        return "graphml"

    def __init__(self, file_path: str | None = None, username: str | None = None):
        super().__init__(file_path=file_path, username=username)
        self.graph = nx.Graph()
        self.load()

    def load(self):
        """Load graph from GraphML file."""
        if Path(self.file_path).exists() and Path(self.file_path).stat().st_size > 0:
            self.graph = nx.read_graphml(self.file_path)

    def save(self):
        """Save graph to GraphML file."""
        nx.write_graphml(self.graph, self.file_path)
        print_internal(f"Graph saved to {self.file_path}")

    def add_entity(self, name: str, entity_type: str = "person") -> bool:
        """Add a new entity node with ToM attribute lists."""
        if not self.graph.has_node(name):
            self.graph.add_node(name, type=entity_type)
            for key in get_tom_attributes():
                self.graph.nodes[name][key] = json.dumps([])
            return True
        return False

    def update_tom(self, entity: str, attribute: str, values: List[str]):
        """Update Theory of Mind attributes for an entity."""
        if entity not in self.graph:
            self.add_entity(entity)
        if attribute in get_tom_attributes():
            current = set(json.loads(self.graph.nodes[entity].get(attribute, [])))
            current.update(values)
            self.graph.nodes[entity][attribute] = json.dumps(list(current))

    def add_relationship(
        self, source: str, target: str, rel_type: str, context: str = ""
    ):
        """Add a relationship edge between entities."""
        self.add_entity(source)
        self.add_entity(target)
        self.graph.add_edge(source, target, type=rel_type, context=context)

    def get_entity_info(self, entity: str) -> Dict:
        """Get all ToM info for an entity.

        Parses JSON-encoded ToM attributes into lists for consistency with RDF backend.
        """
        if entity not in self.graph:
            return {}

        info = dict(self.graph.nodes[entity])
        # Parse JSON-encoded ToM attributes
        for attr in get_tom_attributes():
            if attr in info and isinstance(info[attr], str):
                info[attr] = json.loads(info[attr])
        return info

    def get_all_entities(self) -> List[str]:
        """Get list of all entity names in the graph."""
        return list(self.graph.nodes)

    def set_tom(self, entity: str, attribute: str, values: List[str]):
        """Set Theory of Mind attributes for an entity (replaces existing values)."""
        if entity not in self.graph:
            self.add_entity(entity)
        if attribute in get_tom_attributes():
            self.graph.nodes[entity][attribute] = json.dumps(list(set(values)))

    def remove_relationship(self, source: str, target: str, rel_type: str) -> bool:
        """Remove a specific relationship."""
        if self.graph.has_edge(source, target):
            edge_data = self.graph.get_edge_data(source, target)
            if edge_data.get("type") == rel_type:
                self.graph.remove_edge(source, target)
                return True
        # Try reverse direction
        if self.graph.has_edge(target, source):
            edge_data = self.graph.get_edge_data(target, source)
            if edge_data.get("type") == rel_type:
                self.graph.remove_edge(target, source)
                return True
        return False

    def query_tom(self, entity: str, attribute: str) -> List[str]:
        """Query ToM attributes for an entity."""
        info = self.get_entity_info(entity)
        values = info.get(attribute, "[]")
        if isinstance(values, str):
            return json.loads(values)
        return values if isinstance(values, list) else []

    def query_relationships(
        self, entity: str, rel_type: str | None = None
    ) -> List[Dict]:
        """Query relationships for an entity."""
        results = []
        if entity not in self.graph:
            return results

        for source, target, data in self.graph.edges(data=True):
            if source == entity or target == entity:
                edge_type = data.get("type", "MENTIONS")
                if rel_type is None or edge_type == rel_type:
                    results.append(
                        {
                            "source": source,
                            "target": target,
                            "type": edge_type,
                            "context": data.get("context", ""),
                        }
                    )
        return results

    def query_by_attribute(self, attribute: str, value: str) -> List[str]:
        """Find all entities with a specific ToM attribute value."""
        results = []
        for node in self.graph.nodes:
            info = self.get_entity_info(node)
            values = info.get(attribute, "[]")
            if isinstance(values, str):
                values = json.loads(values)
            if value in values:
                results.append(node)
        return results

    def print_graph(self):
        """Print the current graph state."""
        print_header(" Knowledge Graph ")

        # Print entities
        print(colorize("\n  Entities:", Colors.BRIGHT_WHITE, Colors.BOLD))
        print_separator(Colors.GRAY)

        for node in self.graph.nodes:
            attrs = self.graph.nodes[node]
            node_type = attrs.get("type", "unknown")
            print_entity(node, node_type)

            # Print ToM attributes for this entity
            for attr in get_tom_attributes():
                values = json.loads(attrs.get(attr, "[]"))
                if values:
                    print_tom_label(attr, values)

        # Print relationships
        print(colorize("\n  Relationships:", Colors.BRIGHT_WHITE, Colors.BOLD))
        print_separator(Colors.GRAY)

        if self.graph.edges():
            for source, target, data in self.graph.edges(data=True):
                rel_type = data.get("type", "")
                context = data.get("context", "")
                print_relationship(source, target, rel_type, context)
        else:
            print(colorize("  (No relationships yet)", Colors.GRAY))

        print()
