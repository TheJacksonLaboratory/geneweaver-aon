from typing import Optional
from geneweaver.aon.models import Homology
from sqlalchemy.orm import Session


def get_homologs(
        db: Session,
        homolog_id: Optional[int] = None,
        source_name: Optional[str] = None,
        species_id: Optional[int] = None,
        gene_id: Optional[int] = None,
):
    base_query = db.query(Homology)
    if homolog_id is not None:
        base_query = base_query.filter(Homology.hom_id == homolog_id)
    if source_name is not None:
        base_query = base_query.filter(Homology.hom_source_name == source_name)
    if species_id is not None:
        base_query = base_query.filter(Homology.sp_id == species_id)
    if gene_id is not None:
        base_query = base_query.filter(Homology.gn_id == gene_id)

    return base_query.all()


def homolog_sources(db: Session):
    results = db.query(Homology.hom_source_name).distinct().all()
    return [r.hom_source_name for r in results]