import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book import Book
from app.models.concept import Concept, ConceptEdge
from app.schemas.concept import ConceptRead

router = APIRouter(tags=["concepts"])


@router.post("/books/{book_id}/concepts/extract", response_model=list[ConceptRead])
async def extract_concepts(book_id: uuid.UUID, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = db.query(Concept).filter(Concept.book_id == book_id).all()
    if existing:
        return existing

    from app.services.concept_extraction.concept_extractor import ConceptExtractor

    extractor = ConceptExtractor()
    concepts = await extractor.extract_from_book(db, book_id)
    return concepts


@router.get("/books/{book_id}/concepts", response_model=list[ConceptRead])
def list_concepts(book_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(Concept)
        .filter(Concept.book_id == book_id)
        .order_by(Concept.difficulty, Concept.name)
        .all()
    )


@router.post("/books/{book_id}/graph/build")
async def build_graph(book_id: uuid.UUID, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = db.query(ConceptEdge).filter(ConceptEdge.book_id == book_id).all()
    if existing:
        return {"concepts": len(db.query(Concept).filter(Concept.book_id == book_id).all()),
                "edges": len(existing)}

    from app.services.graph.concept_graph_builder import ConceptGraphBuilder

    builder = ConceptGraphBuilder()
    edges = await builder.build_graph(db, book_id)
    concepts = db.query(Concept).filter(Concept.book_id == book_id).all()
    return {"concepts": len(concepts), "edges": len(edges)}


@router.get("/books/{book_id}/graph")
def get_graph(book_id: uuid.UUID, db: Session = Depends(get_db)):
    concepts = db.query(Concept).filter(Concept.book_id == book_id).all()
    edges = db.query(ConceptEdge).filter(ConceptEdge.book_id == book_id).all()

    return {
        "concepts": [
            {"id": str(c.id), "name": c.name, "type": c.concept_type,
             "difficulty": c.difficulty, "importance": c.importance}
            for c in concepts
        ],
        "edges": [
            {"source": str(e.source_concept_id), "target": str(e.target_concept_id),
             "type": e.edge_type, "confidence": e.confidence}
            for e in edges
        ],
    }
