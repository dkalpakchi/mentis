"""RDF-based Knowledge Graph with Theory of Mind attributes using SPARQL."""

from pathlib import Path
from typing import Any

from rdflib import Graph, Literal, URIRef, Namespace, RDF, RDFS, XSD

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

# Define namespaces
TOM_NS = Namespace("urn:tom:")
SCHEMA = Namespace("urn:schema:")


class TomGraphRDF(TomGraph):
    """RDF-based Knowledge Graph with Theory of Mind attributes.

    Uses proper RDF triples for structured storage and supports SPARQL queries.
    Each ToM attribute (belief, desire, emotion, etc.) is stored as an individual triple
    rather than JSON-encoded lists, enabling efficient querying.
    """

    def _get_file_extension(self) -> str:
        return "ttl"

    def __init__(
        self,
        file_path: str | None = None,
        username: str | None = None,
        use_sparql: bool = False,
    ):
        super().__init__(file_path=file_path, username=username)
        self.use_sparql = use_sparql
        self.store = None

        # Always use a regular Graph - RDFLib's Graph supports SPARQL queries
        # use_sparql flag controls whether to use SPARQL syntax in queries
        self.graph = Graph()

        # Bind namespaces for serialization
        self.graph.bind("tom", TOM_NS)
        self.graph.bind("schema", SCHEMA)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("xsd", XSD)
        self.load()

    def load(self):
        """Load graph from Turtle file."""
        if Path(self.file_path).exists():
            self.graph.parse(self.file_path, format="turtle")

    def save(self):
        """Save graph to Turtle file."""
        self.graph.serialize(destination=self.file_path, format="turtle")
        print_internal(f"RDF graph saved to {self.file_path}")

    def _get_node(self, name: str) -> URIRef:
        """Get or create a URIRef for an entity."""
        # Clean name for use in URI (replace spaces, special chars)
        safe_name = name.replace(" ", "_").replace("-", "_")
        return URIRef(f"http://example.org/entities/{safe_name}")

    def add_entity(self, name: str, entity_type: str = "person") -> bool:
        """Add a new entity node with RDF type."""
        node = self._get_node(name)

        # Check if entity already has a type
        if list(self.graph.objects(node, RDF.type)):
            return False

        # Map common types to schema.org or TOM namespace
        type_mapping = {
            "person": SCHEMA.Person,
            "organization": SCHEMA.Organization,
            "location": SCHEMA.Place,
            "concept": SCHEMA.Thing,
        }
        type_uri = type_mapping.get(entity_type, TOM_NS[entity_type])

        self.graph.add((node, RDF.type, type_uri))
        self.graph.add((node, RDFS.label, Literal(name, lang="en")))
        return True

    def update_tom(self, entity: str, attribute: str, values: list[str]):
        """Update Theory of Mind attributes for an entity.

        Stores each value as an individual triple:
        - entity tom:hasBelief "value"
        - entity tom:hasDesire "value"
        - etc.
        """
        if attribute not in get_tom_attributes():
            return

        node = self._get_node(entity)

        # Ensure entity exists
        if not list(self.graph.objects(node, RDF.type)):
            self.add_entity(entity)

        # Map attribute to predicate
        attr_predicate = getattr(TOM_NS, attribute, TOM_NS[attribute])

        # Add each value as a separate triple
        for value in set(values):
            # Store with language tag for text values
            self.graph.add((node, attr_predicate, Literal(value, lang="en")))

    def add_relationship(
        self, source: str, target: str, rel_type: str, context: str = ""
    ):
        """Add a relationship as RDF triples.

        Creates triples:
        - source tom:relationshipType target
        - source tom:relationshipContext "context" (if provided)
        """
        source_node = self._get_node(source)
        target_node = self._get_node(target)

        self.add_entity(source)
        self.add_entity(target)

        # Add the relationship
        rel_uri = TOM_NS[rel_type]
        self.graph.add((source_node, rel_uri, target_node))

        # Add context as a separate triple if provided
        if context:
            self.graph.add(
                (source_node, TOM_NS.relationshipContext, Literal(context, lang="en"))
            )

    def get_entity_info(self, entity: str) -> dict:
        """Get all ToM info for an entity using SPARQL if available."""
        node = self._get_node(entity)
        info: dict[str, Any] = {"type": "unknown"}
        for attr in get_tom_attributes():
            info[attr] = []

        # Get type
        for obj in self.graph.objects(node, RDF.type):
            type_str = str(obj)
            if "#" in type_str:
                info["type"] = type_str.split("#")[-1]
            elif "/" in type_str:
                info["type"] = type_str.split("/")[-1]
            else:
                info["type"] = type_str

        # Get ToM attributes - each is stored as individual triples
        for attr in get_tom_attributes():
            predicate = getattr(TOM_NS, attr, TOM_NS[attr])
            for obj in self.graph.objects(node, predicate):
                info[attr].append(str(obj))

        return info

    def get_all_entities(self) -> list[str]:
        """Get list of all entity names in the graph."""
        entities = set()
        for subj in self.graph.subjects(RDF.type, None):
            entity_name = str(subj).split("/")[-1].split("#")[-1]
            entities.add(entity_name)
        return list(entities)

    def set_tom(self, entity: str, attribute: str, values: list[str]):
        """Set Theory of Mind attributes for an entity (replaces existing values)."""
        if attribute not in get_tom_attributes():
            return

        node = self._get_node(entity)

        # Ensure entity exists
        if not list(self.graph.objects(node, RDF.type)):
            self.add_entity(entity)

        # Remove existing values for this attribute
        predicate = getattr(TOM_NS, attribute, TOM_NS[attribute])
        for _, _, obj in self.graph.triples((node, predicate, None)):
            self.graph.remove((node, predicate, obj))

        # Add new values
        for value in set(values):
            self.graph.add((node, predicate, Literal(value, lang="en")))

    def remove_relationship(self, source: str, target: str, rel_type: str) -> bool:
        """Remove a specific relationship."""
        source_node = self._get_node(source)
        target_node = self._get_node(target)
        rel_uri = TOM_NS[rel_type]

        # Check if relationship exists
        if (source_node, rel_uri, target_node) in self.graph:
            self.graph.remove((source_node, rel_uri, target_node))
            return True
        return False

    def query_tom(self, entity: str, attribute: str) -> list[str]:
        """Query ToM attributes using SPARQL (if store supports it)."""
        if not self.use_sparql:
            # Fall back to regular graph query
            info = self.get_entity_info(entity)
            return info.get(attribute, [])

        # Build SPARQL query
        node = self._get_node(entity)
        predicate = getattr(TOM_NS, attribute, TOM_NS[attribute])

        query = f"""
        SELECT ?value WHERE {{
            <{node}> <{predicate}> ?value .
        }}
        """
        results = self.graph.query(query)
        return [str(row.value) for row in results]

    def query_relationships(
        self, entity: str, rel_type: str | None = None
    ) -> list[dict]:
        """Query relationships for an entity using SPARQL."""
        node = self._get_node(entity)

        results = []

        if rel_type:
            predicate = getattr(TOM_NS, rel_type, TOM_NS[rel_type])
            query = f"""
            SELECT ?target ?context WHERE {{
                <{node}> <{predicate}> ?target .
                OPTIONAL {{ <{node}> <{TOM_NS.relationshipContext}> ?context }}
            }}
            """
            for row in self.graph.query(query):
                target = str(row.target).split("/")[-1].split("#")[-1]
                context = (
                    str(row.context) if hasattr(row, "context") and row.context else ""
                )
                results.append(
                    {
                        "source": entity,
                        "target": target,
                        "type": rel_type,
                        "context": context,
                    }
                )
        else:
            # Filter out RDF type and label predicates
            query = f"""
            SELECT ?predicate ?target ?context WHERE {{
                <{node}> ?predicate ?target .
                FILTER(?predicate != <{RDF.type}>)
                FILTER(?predicate != <{RDFS.label}>)
                OPTIONAL {{ <{node}> <{TOM_NS.relationshipContext}> ?context }}
            }}
            """
            for row in self.graph.query(query):
                rel = str(row.predicate).split("/")[-1].split("#")[-1]
                target = str(row.target).split("/")[-1].split("#")[-1]
                context = (
                    str(row.context) if hasattr(row, "context") and row.context else ""
                )
                results.append(
                    {
                        "source": entity,
                        "target": target,
                        "type": rel,
                        "context": context,
                    }
                )

        return results

    def query_by_attribute(self, attribute: str, value: str) -> list[str]:
        """Find all entities that have a specific ToM attribute value.

        For example: find all entities that have belief "the sky is blue"
        """
        predicate = getattr(TOM_NS, attribute, TOM_NS[attribute])

        query = f"""
        SELECT ?entity WHERE {{
            ?entity <{predicate}> ?val .
            FILTER(?val = "{value}"@en)
        }}
        """
        results = []
        for row in self.graph.query(query):
            entity_uri = str(row.entity)
            entity_name = entity_uri.split("/")[-1].split("#")[-1]
            results.append(entity_name)

        return results

    def print_graph(self):
        """Print the current graph state with SPARQL-style formatting."""
        print_header(" RDF Knowledge Graph (Triple Store) ")

        # Print entities with ToM attributes
        print(colorize("\n  Entities:", Colors.BRIGHT_WHITE, Colors.BOLD))
        print_separator(Colors.GRAY)

        # Get all entities (subjects with types)
        entities = set()
        for subj in self.graph.subjects(RDF.type, None):
            entities.add(subj)

        for subj in entities:
            entity_name = str(subj).split("/")[-1].split("#")[-1]
            info = self.get_entity_info(entity_name)
            entity_type = info.get("type", "unknown")
            print_entity(entity_name, entity_type)

            for attr in get_tom_attributes():
                values = info.get(attr, [])
                if values:
                    print_tom_label(attr, values)

        # Print relationships as triples
        print(
            colorize("\n  Relationships (Triples):", Colors.BRIGHT_WHITE, Colors.BOLD)
        )
        print_separator(Colors.GRAY)

        # Get all non-type, non-attribute triples (actual relationships)
        rels = []
        for subj, pred, obj in self.graph:
            pred_str = str(pred)
            # Skip type statements and ToM attribute statements
            if pred == RDF.type:
                continue
            if any(
                attr in pred_str
                for attr in get_tom_attributes() + ["relationshipContext"]
            ):
                continue
            source = str(subj).split("/")[-1].split("#")[-1]
            target = str(obj).split("/")[-1].split("#")[-1]
            rel_type = str(pred).split("/")[-1].split("#")[-1]
            rels.append((source, target, rel_type))

        if rels:
            for source, target, rel_type in rels:
                print_relationship(source, target, rel_type)
        else:
            print(colorize("  (No relationships yet)", Colors.GRAY))

        # Print raw triples count
        triple_count = len(self.graph)
        print(colorize(f"\n  Total triples: {triple_count}", Colors.DIM))
        print()
