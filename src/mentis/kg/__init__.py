"""Knowledge Graph implementations for Mentis."""

from mentis.kg.base import TomGraph
from mentis.kg.graphml import TomGraphGraphML
from mentis.kg.rdf import TomGraphRDF


def get_kg(
    kg_type: str = "graphml", file_path: str | None = None, username: str | None = None
) -> TomGraph:
    """Factory function to get the appropriate KG implementation.

    Args:
        kg_type: Either "graphml" or "rdf"
        file_path: Optional explicit file path
        username: Optional username for default path construction

    Returns:
        TomGraph instance (either GraphML or RDF based)
    """
    if kg_type == "rdf":
        return TomGraphRDF(file_path=file_path, username=username)
    else:
        return TomGraphGraphML(file_path=file_path, username=username)
