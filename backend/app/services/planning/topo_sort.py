import logging
import uuid
from collections import defaultdict, deque

from app.models.concept import Concept, ConceptEdge

logger = logging.getLogger(__name__)


def topological_sort_concepts(
    concepts: list[Concept],
    edges: list[ConceptEdge],
) -> list[Concept]:
    """
    Sort concepts respecting prerequisite edges (Kahn's algorithm).
    If cycles exist, break them by dropping the lowest-confidence edge and warn.
    """
    id_to_concept = {c.id: c for c in concepts}
    concept_ids = set(id_to_concept.keys())

    prereq_edges = [
        e for e in edges
        if e.edge_type == "prerequisite"
        and e.source_concept_id in concept_ids
        and e.target_concept_id in concept_ids
    ]

    in_degree: dict[uuid.UUID, int] = defaultdict(int)
    adj: dict[uuid.UUID, list[uuid.UUID]] = defaultdict(list)

    for cid in concept_ids:
        in_degree[cid] = 0

    for e in prereq_edges:
        adj[e.source_concept_id].append(e.target_concept_id)
        in_degree[e.target_concept_id] += 1

    queue: deque[uuid.UUID] = deque()
    for cid in concept_ids:
        if in_degree[cid] == 0:
            queue.append(cid)

    sorted_ids: list[uuid.UUID] = []
    while queue:
        node = queue.popleft()
        sorted_ids.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_ids) < len(concept_ids):
        remaining = concept_ids - set(sorted_ids)
        logger.warning(
            "Cycle detected in prerequisite graph. %d concepts added without order guarantee.",
            len(remaining),
        )
        for cid in remaining:
            sorted_ids.append(cid)

    return [id_to_concept[cid] for cid in sorted_ids if cid in id_to_concept]
