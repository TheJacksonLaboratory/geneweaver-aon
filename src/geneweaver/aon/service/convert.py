from sqlalchemy.orm import Session

from geneweaver.aon.models import (
    Species,
    Geneweaver_Species,
    Geneweaver_Gene,
)


# converter functions using first char - these functions improve efficiency and
#    are used here instead of convertODEtoAGR and convertAGRtoGW because they require
#    gdb_id and are used more broadly.
def ode_ref_to_agr(db: Session, ode_ref):
    # AGR only contains data from some gene data sources geneewaver has and the format is
    #     slightly different for the reference ids, so this fuction adds prefixes to the ids
    #     where necessary for the AGR format.
    ref = ode_ref
    gdb_id = (
        db.query(Geneweaver_Gene.gdb_id)
        .filter(Geneweaver_Gene.ode_ref_id == ode_ref)
        .first()
    )
    if gdb_id:
        gdb_id = gdb_id[0]

    if gdb_id == 15:
        ref = "WB:" + ode_ref
    elif gdb_id == 16:
        ref = "SGD:" + ode_ref
    elif gdb_id == 14:
        ref = "FB:" + ode_ref
    elif gdb_id == 13:
        ref = "ZFIN:" + ode_ref
    elif gdb_id == 12:
        ref = ode_ref[:3] + ":" + ode_ref[3:]

    return ref


def agr_ref_to_ode(gn_ref_id):
    # All gene ref ids in AGR contain the gene source database prefix followed by a colon,
    #     but geneweaver only has some genes in this format. This function adjusts
    #     the ref ids to match the geneweaver format
    ref = gn_ref_id
    prefix = ref[0 : ref.find(":")]

    # genes with this prefix will have the prefix removed
    gdb_to_remove_prefix = ["WB", "FB", "SGD", "ZFIN"]

    # RGD only requires removing the colon
    if prefix == "RGD":
        ref = ref.replace(":", "")
    elif prefix in gdb_to_remove_prefix:
        ind = ref.find(":") + 1
        ref = ref[ind:]

    # all other gene ref ids will be returned the same if not altered in the above steps
    return ref


def species_ode_to_agr(db: Session, ode_sp_id):
    # find the species name, return None if not found in the geneweaver db
    species_name = (
        db.query(Geneweaver_Species.sp_name)
        .filter(Geneweaver_Species.sp_id == ode_sp_id)
        .first()
    )
    if species_name:
        species_name = species_name[0]
    else:
        return None
    # get the AGR-normalizer species id from the species name
    agr_sp_id = db.query(Species.sp_id).filter(Species.sp_name == species_name).first()
    if agr_sp_id:
        agr_sp_id = agr_sp_id[0]
    return agr_sp_id


def species_agr_to_ode(db: Session, agr_sp_id):
    # find the species name, return None if not found in the AGR-normalizer db
    species_name = db.query(Species.sp_name).filter(Species.sp_id == agr_sp_id).first()
    if species_name:
        species_name = species_name[0]
    else:
        return None
    # get the geneweaver species id
    ode_sp_id = (
        db.query(Geneweaver_Species.sp_id)
        .filter(Geneweaver_Species.sp_name == species_name)
        .first()
    )
    if ode_sp_id:
        ode_sp_id = ode_sp_id[0]
    return ode_sp_id