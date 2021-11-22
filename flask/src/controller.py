"""
Definition of our API interface - Endpoints query the AGR database
"""

from flask_restx import Namespace, Resource, fields, abort, reqparse
from database import SessionLocal
from models import Algorithm, Ortholog, Gene, Species, OrthologAlgorithms, \
    Geneweaver_Species, Geneweaver_Gene, Geneweaver_GeneDB, Homology

NS = Namespace('agr-service', description='Endpoints to query database')
db = SessionLocal()

parser = reqparse.RequestParser()

# MODELS - correspond with models in models.py file, allow for output in JSON format
algorithm_model = NS.model('algorithms', {
    'alg_id': fields.Integer(),
    'alg_name': fields.String()
})

ortholog_model = NS.model('orthologs', {
    'ort_id': fields.Integer(),
    'from_gene': fields.Integer(),
    'to_gene': fields.Integer(),
    'ort_is_best': fields.Boolean(),
    'ort_is_best_revised': fields.Boolean(),
    'ort_is_best_adjusted': fields.Boolean(),
    'ort_num_possible_match_algorithms': fields.Integer()
})

gene_model = NS.model('genes', {
    'gn_id': fields.Integer(),
    'gn_ref_id': fields.String(),
    'gn_prefix': fields.String(),
    'sp_id': fields.Integer()
})

species_model = NS.model('species', {
    'sp_id': fields.Integer(),
    'sp_name': fields.String(),
    'sp_taxon_id': fields.Integer()
})

ortholog_algorithms_model = NS.model('ortholog_algorithms', {
    'ora_id': fields.Integer(),
    'alg_id': fields.Integer(),
    'ort_id': fields.Integer()
})

gw_gene_model = NS.model('geneweaver_genes', {
    'ode_gene_id': fields.Integer(),
    'ode_ref_id': fields.String(),
    'gdb_id': fields.Integer(),
    'sp_id': fields.Integer(),
    'ode_pref': fields.Boolean(),
    'ode_date': fields.Date(),
    'old_ode_gene_ids': fields.Integer()
})

homology_model = NS.model('homologs', {
    'hom_id': fields.Integer(),
    'gn_id': fields.Integer(),
    'sp_id': fields.Integer(),
    'hom_source_name': fields.String()
})


# CONVERTER FUNCTIONS - convert parameters to communicate between databases
def convertODEtoAGR(ode_ref, gdb_id):
    # convert the ref_ids into how the agr ref ids are stored, same values but formatted
    #    slightly different in each database
    '''
        :description: converts into agr gene_id using the ode_ref_id and ode_gene_id
            (both used as primary key in geneweaver.gene table)
        :param ode_ref - ode_ref_id of gene
               ode_gene_id - ode_gene_id of gene
        :return: agr ref id (gn_ref_id from gn_gene table)
    '''
    ref = ode_ref
    gdb_id = int(gdb_id)
    # in agr database, each species only comes from one gdb_id, so these can be used
    #    to differentiate how the ref id should be modified
    if gdb_id in [10, 11, 12, 13, 14, 15, 16]:
        if gdb_id == 15:
            prefix = "WB"
            ref = prefix + ":" + ode_ref
        if gdb_id == 14:
            prefix = "FB"
            ref = prefix + ":" + ode_ref
        if gdb_id == 16:
            prefix = "SGD"
            ref = prefix + ":" + ode_ref
        if gdb_id == 13:
            prefix = "ZFIN"
            ref = prefix + ":" + ode_ref
        if gdb_id == 12:
            ref = ode_ref[:3] + ":" + ode_ref[3:]
    return ref


def convertAGRtoODE(gn_id):
    '''
        :description: converts an agr gene_id into the ode gene object
        :param gn_id - integer gene id from gn_gene table in agr database
        :return: ode_gene_id - integer gene id from gene table in geneweaver database
    '''
    agr_gene = db.query(Gene).filter(Gene.gn_id == gn_id).first()
    ref = agr_gene.gn_ref_id
    prefix = agr_gene.gn_prefix
    # convert the ref ids into the format they are stored in the geneweaver gene table
    if prefix == "RGD":
        ref = ref.replace(":", "")
    elif prefix == "WB" or prefix == "FB" or prefix == "SGD" or prefix == "ZFIN":
        ind = ref.find(":") + 1
        ref = ref[ind:]

    ode_gene_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_ref_id == ref).first()).ode_gene_id
    return ode_gene_id


# alg_algorithm Table Endpoints
@NS.route('/get_algorithm_by_name/<alg_name>')
class get_algorithm_by_name(Resource):
    '''
    :param alg_name: string of full species name, case sensitive
    :return: alg_id and alg_name for selected algorithm
    '''

    @NS.doc('returns algorithm object with specified name')
    @NS.marshal_with(algorithm_model)
    def get(self, alg_name):
        result = db.query(Algorithm).filter(Algorithm.alg_name == alg_name).first()
        return result


@NS.route('/all_algorithms')
class all_algorithms(Resource):
    '''
    :return: alg_id and alg_name for each algorithm
    '''

    @NS.doc('returns all algorithms')
    @NS.marshal_with(algorithm_model)
    def get(self):
        return db.query(Algorithm).all()


# ort_ortholog Table Endpoints
@NS.route('/all_orthologs')
class all_orthologs(Resource):
    '''
    :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised,
             ort_is_best_adjusted, and ort_num_possible_match_algorithms)
    '''

    @NS.doc('returns all orthologs')
    @NS.marshal_with(ortholog_model)
    def get(self):
        return db.query(Ortholog).all()


@NS.route('/get_orthologs_by_from_gene/<ode_ref_id>/<ode_gene_id>')
class get_orthologs_by_from_gene(Resource):
    '''
    :param ode_ref_id - ode_ref_id of from gene
           ode_gene_id - ode_gene_id of from gene
    :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for any ortholog with specified from_gene
    '''

    @NS.doc('returns orthologs from a specified gene')
    @NS.marshal_with(ortholog_model)
    def get(self, ode_ref_id, ode_gene_id):
        # find gene and search orthologs based on gene_id
        gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == ode_gene_id,
                                                   Geneweaver_Gene.ode_ref_id == ode_ref_id).first()).gdb_id
        gn_ref_id = convertODEtoAGR(ode_ref_id, gdb_id)
        gn_id = db.query(Gene.gn_id).filter(Gene.gn_ref_id == gn_ref_id).first()
        result = db.query(Ortholog).filter(Ortholog.from_gene == gn_id).all()
        if not result:
            abort(404, message="Could not find any orthologs from the specified gene")
        return result


@NS.route('/get_orthologs_by_to_gene/<ode_ref_id>/<ode_gene_id>')
class get_orthologs_by_to_gene(Resource):
    '''
    :param ode_ref_id - ode_ref_id of to gene
           ode_gene_id - ode_gene_id of to gene
    :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for any ortholog with specified to_gene
    '''

    @NS.doc('returns orthologs to a specified gene')
    @NS.marshal_with(ortholog_model)
    def get(self, ode_ref_id, ode_gene_id):
        gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == ode_gene_id,
                                                   Geneweaver_Gene.ode_ref_id == ode_ref_id).first()).gdb_id
        gn_ref_id = convertODEtoAGR(ode_ref_id, gdb_id)
        gn_id = (db.query(Gene).filter(Gene.gn_ref_id == gn_ref_id).first()).gn_id
        result = db.query(Ortholog).filter(Ortholog.to_gene == gn_id).all()
        if not result:
            abort(404, message="Could not find any orthologs to the specified gene")
        return result


@NS.route('/get_ortholog_by_id/<ort_id>')
class get_ortholog_by_id(Resource):
    '''
    :param ort_id - ort_id from ort_ortholog table
    :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for any ortholog with specified ort_i
    '''

    @NS.doc('returns orthologs with specified id')
    @NS.marshal_with(ortholog_model)
    def get(self, ort_id):
        result = db.query(Ortholog).filter(Ortholog.ort_id == ort_id).all()
        if not result:
            abort(404, message="Could not find any orthologs with that ortholog id")
        return result


@NS.route('/get_orthologs_by_to_and_from_gene/<from_ode_ref_id>/<from_ode_gene_id>/<to_ode_ref_id>/<to_ode_gene_id>')
class get_orthologs_by_to_and_from_gene(Resource):
    '''
    :param from_ode_ref_id - ode_ref_id of from gene
           from_ode_gene_id - ode_gene_id of from gene
           to_ode_ref_id - ode_ref_id of to gene
           to_ode_gene_id - ode_gene_id of to gene
    :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for any ortholog with specified from_gene and to_gene
    '''

    @NS.doc('returns all orthologs to and from the specified genes')
    @NS.marshal_with(ortholog_model)
    def get(self, from_ode_ref_id, from_ode_gene_id, to_ode_ref_id, to_ode_gene_id):
        to_gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == to_ode_gene_id,
                                                      Geneweaver_Gene.ode_ref_id == to_ode_ref_id).first()).gdb_id
        from_gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == from_ode_gene_id,
                                                        Geneweaver_Gene.ode_ref_id == from_ode_ref_id).first()).gdb_id

        # converting geneweaver refs to query gn_gene table
        from_gn_ref = convertODEtoAGR(from_ode_ref_id, from_gdb_id)
        to_gn_ref = convertODEtoAGR(to_ode_ref_id, to_gdb_id)

        to_agr_gn_id = (db.query(Gene).filter(Gene.gn_ref_id == to_gn_ref).first()).gn_id
        from_agr_gn_id = (db.query(Gene).filter(Gene.gn_ref_id == from_gn_ref).first()).gn_id

        result = db.query(Ortholog).filter(Ortholog.from_gene == from_agr_gn_id,
                                           Ortholog.to_gene == to_agr_gn_id).all()
        if not result:
            abort(404, message="Could not find any orthologs with that from and to gene")
        return result


@NS.route('/get_orthologs_by_from_gene_and_best/<from_ode_ref_id>/<from_ode_gene_id>/<best>')
class get_orthologs_by_from_gene_and_best(Resource):
    '''
    :param from_ode_ref_id - ode_ref_id of from gene
           from_ode_gene_id - ode_gene_id of from gene
           best - boolean to query the ort_is_best column in ortholog table
    :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for any ortholog from a specific gene and T or F for
             the ort_is_best column
    '''

    @NS.doc('returns all orthologs from specified gene and by the best variable')
    @NS.marshal_with(ortholog_model)
    def get(self, from_ode_ref_id, from_ode_gene_id, best):
        # best variable is a string, must convert it to a bool to use in query
        best = best.upper()
        if best == "FALSE" or best == "F":
            modified_best = False
        else:
            modified_best = True
        gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == from_ode_gene_id,
                                                   Geneweaver_Gene.ode_ref_id == from_ode_ref_id).first()).gdb_id
        gn_ref = convertODEtoAGR(from_ode_ref_id, gdb_id)
        agr_gn_id = (db.query(Gene).filter(Gene.gn_ref_id == gn_ref).first()).gn_id
        result = db.query(Ortholog).filter(Ortholog.from_gene == agr_gn_id,
                                           Ortholog.ort_is_best == modified_best).all()
        if not result:
            abort(404, message="Could not find any orthologs with that from gene and ort_is_best value")
        return result


@NS.route('/get_orthologs_by_from_to_gene_and_best/<from_ode_ref_id>/<from_ode_gene_id>/<to_ode_ref_id>/<to_ode_gene_id>/<best>')
class get_orthologs_by_from_to_gene_and_best(Resource):
    '''
    :param from_ode_ref_id - ode_ref_id of from gene
           from_ode_gene_id - ode_gene_id of from gene
           to_ode_ref_id - ode_ref_id of to gene
           to_ode_gene_id - ode_gene_id of to gene
           best - boolean to query the ort_is_best column in ortholog table
    :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for any ortholog with specified from_gene and to_gene
             and T or F for the ort_is_best column
    '''

    @NS.doc('returns all orthologs from and to specified gene and by the best variable')
    @NS.marshal_with(ortholog_model)
    def get(self, from_ode_ref_id, from_ode_gene_id, to_ode_ref_id, to_ode_gene_id, best):
        # best variable is a string, must convert it to a bool to use in query
        best = best.upper()
        if best == "FALSE" or best == "F":
            modified_best = False
        else:
            modified_best = True
        # find from and to gene objects using given information
        to_gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == to_ode_gene_id,
                                                      Geneweaver_Gene.ode_ref_id == to_ode_ref_id).first()).gdb_id
        from_gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == from_ode_gene_id,
                                                        Geneweaver_Gene.ode_ref_id == from_ode_ref_id).first()).gdb_id
        from_gn_ref = convertODEtoAGR(from_ode_ref_id, from_gdb_id)
        to_gn_ref = convertODEtoAGR(to_ode_ref_id, to_gdb_id)

        to_agr_gn_id = (db.query(Gene).filter(Gene.gn_ref_id == to_gn_ref).first()).gn_id
        from_agr_gn_id = (db.query(Gene).filter(Gene.gn_ref_id == from_gn_ref).first()).gn_id

        result = db.query(Ortholog).filter(Ortholog.from_gene == from_agr_gn_id,
                                           Ortholog.to_gene == to_agr_gn_id,
                                           Ortholog.ort_is_best == modified_best).all()
        if not result:
            abort(404, message="Could not find any orthologs with that "
                               "from_gene, to_gene and ort_is_best value")
        return result


@NS.route('/get_orthologs_by_from_to_gene_and_revised/<from_ode_ref_id>/<from_ode_gene_id>/<to_ode_ref_id>/<to_ode_gene_id>/<ort_best_revised>')
class get_orthologs_by_from_to_gene_and_revised(Resource):
    '''
        :param from_ode_ref_id - ode_ref_id of from gene
               from_ode_gene_id - ode_gene_id of from gene
               to_ode_ref_id - ode_ref_id of to gene
               to_ode_gene_id - ode_gene_id of to gene
               ort_best_revised - boolean to query the ort_is_best_revised column in ortholog table
        :return: all ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
                 and ort_num_possible_match_algorithms) for any ortholog with specified from_gene and to_gene
                 and T or F for the ort_is_best_revised column
    '''
    @NS.doc('returns all orthologs from and to specified gene and by the ort_best_revised variable')
    @NS.marshal_with(ortholog_model)
    def get(self, from_ode_ref_id, from_ode_gene_id, to_ode_ref_id, to_ode_gene_id, ort_best_revised):
        # convert string ort_best_revised into a bool to be used in later queries
        ort_best_revised = ort_best_revised.upper()
        if ort_best_revised == "FALSE" or ort_best_revised == "F":
            inp = False
        else:
            inp = True

        to_gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == to_ode_gene_id,
                                                      Geneweaver_Gene.ode_ref_id == to_ode_ref_id).first()).gdb_id
        from_gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == from_ode_gene_id,
                                                        Geneweaver_Gene.ode_ref_id == from_ode_ref_id).first()).gdb_id
        from_gn_ref = convertODEtoAGR(from_ode_ref_id, from_gdb_id)
        to_gn_ref = convertODEtoAGR(to_ode_ref_id, to_gdb_id)

        to_agr_gn_id = (db.query(Gene).filter(Gene.gn_ref_id == to_gn_ref).first()).gn_id
        from_agr_gn_id = (db.query(Gene).filter(Gene.gn_ref_id == from_gn_ref).first()).gn_id

        result = db.query(Ortholog).filter(Ortholog.from_gene == from_agr_gn_id,
                                           Ortholog.to_gene == to_agr_gn_id,
                                           Ortholog.ort_is_best_revised == inp).all()
        if not result:
            abort(404, message="Could not find any orthologs with that from_gene,"
                               " to_gene and ort_is_best_revised value")
        return result


@NS.route('/get_from_gene_of_ortholog_by_id/<ort_id>')
class get_from_gene_of_ortholog_by_id(Resource):
    '''
    :param ort_id: id from ortholog table
    :return: gene info (gn_id, gn_ref_id, gn_prefix, sp_id) of the from gene for that ortholog
    '''

    @NS.doc('return from_gene object of a ortholog')
    @NS.marshal_with(gene_model)
    def get(self, ort_id):
        ortholog = db.query(Ortholog).filter(Ortholog.ort_id == ort_id).first()
        result = db.query(Gene).filter(Gene.gn_id == ortholog.from_gene).first()
        if not ortholog:
            abort(404, message="Could not find any orthologs with the given parameters")
        return result


@NS.route('/get_to_gene_of_ortholog_by_id/<ort_id>')
class get_to_gene_of_ortholog_by_id(Resource):
    '''
    :param ort_id: id from ortholog table
    :return: gene info (gn_id, gn_ref_id, gn_prefix, sp_id) of the to gene for that ortholog
    '''

    @NS.doc('return to_gene object of a specific ortholog')
    @NS.marshal_with(gene_model)
    def get(self, ort_id):
        ortho = db.query(Ortholog).filter(Ortholog.ort_id == ort_id).first()
        result = db.query(Gene).filter(Gene.gn_id == ortho.to_gene).first()
        if not ortho:
            abort(404, message="Could not find any orthologs with the given parameters")
        return result


# gn_gene Table Endpoints
@NS.route('/all_genes')
class all_genes(Resource):
    '''
    :return: all gene info (id, ref_id, gn_prefix, species)
    '''

    @NS.doc('return all genes')
    @NS.marshal_with(gene_model)
    def get(self):
        return db.query(Gene).all()


@NS.route('/get_genes_by_prefix/<gn_prefix>')
class get_genes_by_prefix(Resource):
    '''
    :param: gn_prefix
    :return: gene info (id, ref_id, gn_prefix, species) for genes with given prefix
    '''

    @NS.doc('return all genes with specified prefix')
    @NS.marshal_with(gene_model)
    def get(self, gn_prefix):
        gn_prefix = gn_prefix.upper()
        result = db.query(Gene).filter(Gene.gn_prefix == gn_prefix).all()
        if not result:
            abort(404, message="Could not find any genes with that prefix")
        return result


@NS.route('/get_genes_by_ode_gene_id/<ode_ref_id>/<ode_gene_id>')
class get_genes_by_ode_gene_id(Resource):
    '''
    :param ode_ref_id - ode_ref_id of gene
           ode_gene_id - ode_gene_id of gene
    :return: gene info (gn_id, gn_ref_id, gn_prefix, sp_id) for agr gene, endpoint version of
            convertODEtoAGR()
    '''

    @NS.doc('return gene with specified ode_ref_id and ode_gene_id')
    @NS.marshal_with(gene_model)
    def get(self, ode_ref_id, ode_gene_id):
        # find gene gdb_id to use the convertODEtoAGR function that converts the
        #     geneweaver ode_ref_id into the agr gn_ref_id
        gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == ode_gene_id,
                                                   Geneweaver_Gene.ode_ref_id == ode_ref_id).first()).gdb_id
        gn_ref_id = convertODEtoAGR(ode_ref_id, gdb_id)
        gene = db.query(Gene).filter(Gene.gn_ref_id == gn_ref_id).first()
        if not gene:
            abort(404, message="Could not find any matching genes")
        return gene


@NS.route('/get_genes_by_species/<sp_name>')
class get_genes_by_species(Resource):
    '''
    :param: sp_name - string for species name, case sensitive
    :return: info (gn_id, gn_ref_id, gn_prefix, sp_id) for genes of given species
    '''

    @NS.doc('returns ode_gene_ids for genes of a certain species')
    @NS.marshal_with(gene_model)
    def get(self, sp_name):
        species = db.query(Species).filter(Species.sp_name == sp_name).first()
        genes = db.query(Gene).filter(Gene.sp_id == species.sp_id).all()
        if not genes:
            abort(404, message="Could not find any genes with that species")
        return genes


@NS.route('/get_gene_species_name/<ode_ref_id>/<ode_gene_id>')
class get_gene_species_name(Resource):
    '''
    :param ode_ref_id - ode_ref_id of gene
           ode_gene_id - ode_gene_id of gene
    :return: species name of gene
    '''

    @NS.doc('returns the species of a specified gene')
    def get(self, ode_ref_id, ode_gene_id):
        gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == ode_gene_id,
                                                   Geneweaver_Gene.ode_ref_id == ode_ref_id).first()).gdb_id
        gn_ref_id = convertODEtoAGR(ode_ref_id, gdb_id)
        agr_species = (db.query(Gene).filter(Gene.gn_ref_id == gn_ref_id).first()).sp_id
        result = db.query(Species.sp_name).filter(Species.sp_id == agr_species).first()
        if not result:
            abort(404, message="Species not found for that gn_ref_id")
        return result


# sp_species Table Endpoints
@NS.route('/all_species')
class all_species(Resource):
    '''
    :return: species info (id, name, sp_taxon_id) for all species
    '''

    @NS.doc('return all species')
    @NS.marshal_with(species_model)
    def get(self):
        return db.query(Species).all()


@NS.route('/get_species_by_id/<sp_id>')
class get_species_by_id(Resource):
    '''
    :param: sp_id
    :return: species info (sp_id, sp_name, sp_taxon_id) for species by id
    '''

    @NS.doc('return species specified by id')
    @NS.marshal_with(species_model)
    def get(self, sp_id):
        return db.query(Species).filter(Species.sp_id == sp_id).all()


# ora_ortholog_algorithms Table Endpoints
@NS.route('/get_orthologs_by_num_algoritms/<num>')
class get_orthologs_by_num_algoritms(Resource):
    '''
    :param: num - number of algoirthms
    :return: ortholog info ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for all orthologs with num_algorithms
    '''

    @NS.doc('return all orthologs with specified ort_num_possible_match_algorithms')
    @NS.marshal_with(ortholog_model)
    def get(self, num):
        result = db.query(Ortholog).filter(Ortholog.ort_num_possible_match_algorithms == num).all()
        if not result:
            abort(404, message="Could not find any orthologs with that number "
                               "of possible match algorithms")
        return result


@NS.route('/get_ortholog_by_algorithm/<alg_name>')
class get_ortholog_by_algorithm(Resource):
    '''
    :param: alg_name - str algorithm by name
    :return: ortholog info ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for all orthologs with that algorithm
    '''

    @NS.doc('return all orthologs for an algorithm')
    @NS.marshal_with(ortholog_algorithms_model)
    def get(self, alg_name):
        # get algorithm id from string of algorithm name
        alg_id = db.query(Algorithm.alg_id).filter(Algorithm.alg_name == alg_name).first()
        orthologs = db.query(OrthologAlgorithms).filter(OrthologAlgorithms.alg_id == alg_id).all()
        return orthologs


# hom_homology table endpoints
@NS.route('/all_homology')
class all_homology(Resource):
    '''
        :param: None
        :return: All rows in homology table
    '''

    @NS.doc('returns all rows of homology table')
    @NS.marshal_with(homology_model)
    def get(self):
        return db.query(Homology).all()


@NS.route('/get_homology_by_id/<hom_id>')
class get_homology_by_id(Resource):
    '''
        :param: hom_id - hom_id of set of desired homologs
            Note: hom_id is not the primary key, any set of genes with the same
                  hom_id are homologs.
        :return: All homology rows with given hom_id
    '''

    @NS.doc('returns all homology rows with given hom_id')
    @NS.marshal_with(homology_model)
    def get(self, hom_id):
        homologs = db.query(Homology).filter(Homology.hom_id == hom_id).all()
        if not homologs:
            abort(404, message="There are not homologs with given hom_id")
        else:
            return homologs


@NS.route('/get_homology_by_gene/<gn_id>')
class get_homology_by_gene(Resource):
    '''
        :param: gn_id - gene id from gn_gene table in agr database
        :return: All rows in homology table that have a matching gn_id to
                 the given gn_id
    '''

    @NS.doc('returns all homology rows with given gn_id')
    @NS.marshal_with(homology_model)
    def get(self, gn_id):
        homologs = db.query(Homology).filter(Homology.gn_id == gn_id).all()
        if not homologs:
            abort(404, message="There are not homologs with that gn_id")
        else:
            return homologs


@NS.route('/get_homology_by_species/<sp_id>')
class get_homology_by_species(Resource):
    '''
        :param: sp_id - species id from sp_species table in agr database
        :return: All rows in homology table that have a matching gn_id to
                 the given sp_id
    '''

    @NS.doc('returns all homology rows with given sp_id')
    @NS.marshal_with(homology_model)
    def get(self, sp_id):
        homologs = db.query(Homology).filter(Homology.sp_id == sp_id).all()
        if not homologs:
            abort(404, message="There are not homologs with that sp_id")
        else:
            return homologs


@NS.route('/get_homology_by_id_and_species/<hom_id>/<sp_id>')
class get_homology_by_id_and_species(Resource):
    '''
        :param: hom_id - hom_id of set of desired homologs
                sp_id - species id from sp_species table in agr database
        :return: All rows in homology table that have a matching gn_id to
                 the given gn_id and a matching sp_id to the given sp_id
    '''

    @NS.doc('returns all homology rows with given gn_id and sp_id')
    @NS.marshal_with(homology_model)
    def get(self, hom_id, sp_id):
        homologs = db.query(Homology).filter(Homology.hom_id == hom_id,
                                             Homology.sp_id == sp_id).all()
        if not homologs:
            abort(404, message="There are not homologs with that hom_id and sp_id")
        else:
            return homologs


@NS.route('/get_homology_by_id_and_source/<hom_id>/<hom_source_name>')
class get_homology_by_id_and_source(Resource):
    '''
        :param: hom_id - hom_id of set of desired homologs
                hom_source_name - either 'AGR' or 'Homologene' to denote where the
                    homologous relationship came from
        :return: All homology rows with given hom_id and hom_source_name
    '''

    @NS.doc('returns all homology rows with given hom_id and hom_source_name')
    @NS.marshal_with(homology_model)
    def get(self, hom_id, hom_source_name):
        homologs = db.query(Homology).filter(Homology.hom_id == hom_id,
                                             Homology.hom_source_name == hom_source_name).all()
        if not homologs:
            abort(404, message="There are not homologs with given hom_id and hom_source_name")
        else:
            return homologs


@NS.route('/get_homology_by_gene_and_source/<gn_id>/<hom_source_name>')
class get_homology_by_gene_and_source(Resource):
    '''
        :param: gn_id - gene id from gn_gene table in agr database
                hom_source_name - either 'AGR' or 'Homologene' to denote where the
                    homologous relationship came from
        :return: All homology rows with given gn_id and hom_source_name
    '''

    @NS.doc('returns all homology rows with given gn_id and hom_source_name')
    @NS.marshal_with(homology_model)
    def get(self, gn_id, hom_source_name):
        homologs = db.query(Homology).filter(Homology.gn_id == gn_id,
                                             Homology.hom_source_name == hom_source_name).all()
        if not homologs:
            abort(404, message="There are not homologs with given gn_id and hom_source_name")
        else:
            return homologs

# ort_ortholog and sp_species table endpoints
@NS.route('/get_ortholog_by_from_species/<sp_name>')
class get_ortholog_by_from_species(Resource):
    '''
    :param: sp_name - str, case sensitive, from gene species
    :return: ortholog info ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for all orthologs from given species
    '''

    @NS.doc('return all orthologs from given species')
    @NS.marshal_with(ortholog_model)
    def get(self, sp_name):
        # get species id from sp_name string
        sp_id = db.query(Species.sp_id).filter(Species.sp_name == sp_name).first()
        # find all genes with specified species and make a list of all the gene ids
        genes = db.query(Gene).filter(Gene.sp_id == sp_id).all()
        gene_ids = []
        for g in genes:
            gene_ids.append(g.gn_id)
        # query orthologs for any from genes in the list of gene_ids
        from_orthos = db.query(Ortholog).filter(Ortholog.from_gene.in_(gene_ids)).all()
        if not from_orthos:
            abort(404, message="Could not find any matching orthologs")
        return from_orthos


@NS.route('/get_ortholog_by_to_species/<sp_name>')
class get_ortholog_by_to_species(Resource):
    '''
    :param: sp_name - str, case sensitive, to gene species
    :return: ortholog info ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for all orthologs to given species
    '''

    @NS.doc('return all orthologs to a given species')
    @NS.marshal_with(ortholog_model)
    def get(self, sp_name):
        # get sp_id from sp_name
        sp_id = db.query(Species.sp_id).filter(Species.sp_name == sp_name).first()
        genes = db.query(Gene).filter(Gene.sp_id == sp_id).all()
        gene_ids = []
        for g in genes:
            gene_ids.append(g.gn_id)
        to_orthos = db.query(Ortholog).filter(Ortholog.to_gene.in_(gene_ids)).all()
        if not to_orthos:
            abort(404, message="Could not find any matching orthologs")
        return to_orthos


@NS.route('/get_ortholog_by_to_and_from_species/<to_sp_name>/<from_sp_name>')
class get_ortholog_by_to_and_from_species(Resource):
    '''
    :param: to_sp_name - str, case sensitive, to gene species name
            from_sp_name - str, case sensitive, from gene species name
    :return: ortholog info ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for all orthologs to and from the given species
    '''

    @NS.doc('return all orthologs to and from given species')
    @NS.marshal_with(ortholog_model)
    def get(self, to_sp_name, from_sp_name):
        # get both species ids
        to_sp_id = db.query(Species.sp_id).filter(Species.sp_name == to_sp_name).first()
        from_sp_id = db.query(Species.sp_id).filter(Species.sp_name == from_sp_name).first()

        # create a list of all gene_ids to and from the species
        to_genes = db.query(Gene).filter(Gene.sp_id == to_sp_id).all()
        from_genes = db.query(Gene).filter(Gene.sp_id == from_sp_id).all()
        to_gn_ids = []
        from_gn_ids = []
        for g in to_genes:
            to_gn_ids.append(g.gn_id)
        for g in from_genes:
            from_gn_ids.append(g.gn_id)

        orthos = db.query(Ortholog).filter(Ortholog.to_gene.in_(to_gn_ids),
                                           Ortholog.from_gene.in_(from_gn_ids)).all()
        if not orthos:
            abort(404, message="Could not find any matching orthologs")
        return orthos


@NS.route('/get_ortholog_by_to_from_species_and_algorithm/<to_sp_name>/<from_sp_name>/<alg_name>')
class get_ortholog_by_to_from_species_and_algorithm(Resource):
    '''
    :param: to_sp_name - str, case sensitive, to gene species name
            from_sp_name - str, case sensitive, from gene species name
            alg_name - str, algoirthm name
    :return: ortholog info ortholog info (ort_id, from_gene, to_gene, ort_is_best, ort_is_best_revised, ort_is_best_adjusted,
             and ort_num_possible_match_algorithms) for all orthologs to and from the given species
             and by algorithm
    '''

    @NS.doc('return all orthologs to and from given species with specific algorithm')
    @NS.marshal_with(ortholog_model)
    def get(self, to_sp_name, from_sp_name, alg_name):

        to_sp_id = db.query(Species.sp_id).filter(Species.sp_name == to_sp_name).first()
        from_sp_id = db.query(Species.sp_id).filter(Species.sp_name == from_sp_name).first()

        to_genes = db.query(Gene.gn_id).filter(Gene.sp_id == to_sp_id).all()
        from_genes = db.query(Gene.gn_id).filter(Gene.sp_id == from_sp_id).all()

        to_gn_ids = []
        from_gn_ids = []

        for g in to_genes:
            to_gn_ids.append(g)
        for g in from_genes:
            from_gn_ids.append(g)

        # get algorithm id from algorithm string
        algo_id = db.query(Algorithm.alg_id).filter(Algorithm.alg_name == alg_name).first()

        orthos_algorithm = db.query(OrthologAlgorithms).filter(OrthologAlgorithms.alg_id == algo_id).all()

        # get list of ortholog ids using the algorithm
        ort_ids = []
        for o in orthos_algorithm:
            ort_ids.append(o.ort_id)

        # filter for Orthologs with from and to genes with given species and orthologs
        # using specified algorithm
        orthos = db.query(Ortholog).filter(Ortholog.to_gene.in_(to_gn_ids),
                                           Ortholog.from_gene.in_(from_gn_ids),
                                           Ortholog.ort_id.in_(ort_ids)).all()

        if not orthos:
            abort(404, message="Could not find any matching orthologs")
        return orthos


#################################################
# AGR and Geneweaver Database Endpoints
# The following endpoints allow for connections to be made between the agr
#    database and the geneweweaver database by linking the species table and gene ids
#################################################

@NS.route('/agr_to_geneweaver_species/<sp_id>')
class agr_to_geneweaver_species(Resource):
    '''
    :param: sp_id - agr species id
    :return: geneweaver species id
    '''

    @NS.doc('translate an AGR species id to the corresponding species id in the geneweaver database')
    def get(self, sp_id):
        agr_sp_name = db.query(Species.sp_name).filter(Species.sp_id == sp_id).first()
        geneweaver_id = (db.query(Geneweaver_Species).filter(Geneweaver_Species.sp_name == agr_sp_name).first()).sp_id
        if not geneweaver_id:
            abort(404, message="No matching sp_id in the Geneweaver Species Table")
        return geneweaver_id


# similar to the convertAGRtoODE function
@NS.route('/id_convert_agr_to_ode/<gn_id>')
class id_convert_agr_to_ode(Resource):
    '''
    :param: gn_id - gene id from gn_gene table in agr database
    :return: ode_gene_id of corresponding gene in geneweaver database
    '''

    @NS.doc('converts an agr gene id to the corresponding ode_gene_id')
    def get(self, gn_id):
        agr_gene = db.query(Gene).filter(Gene.gn_id == gn_id).first()
        # edits the ref id to be in the format of the ode_ref_id, then search geneweaver.gene
        ref = agr_gene.gn_ref_id
        prefix = agr_gene.gn_prefix
        # different formatting based on prefix
        if prefix == "RGD":
            ref = ref.replace(":", "")
        elif prefix == "WB" or prefix == "FB" or prefix == "SGD" or prefix == "ZFIN":
            ind = ref.find(":") + 1
            ref = ref[ind:]
        # find matching ode_gene_id
        ode_gene_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_ref_id == ref).first()).ode_gene_id
        if not ode_gene_id:
            abort(404, message="matching ode_gene_id not found")
        return ode_gene_id


@NS.route('/id_convert_ode_to_agr/<ode_gene_id>/<ode_ref_id>')
class id_convert_ode_to_agr(Resource):
    '''
    :param: ode_ref_id - ode_ref_id of gene
            ode_gene_id - ode_gene_id of gene
    :return: agr gene id of corresponding gene
    '''

    @NS.doc('converts an ode gene id to the corresponding agr gene id')
    def get(self, ode_gene_id, ode_ref_id):
        gdb_id = (db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == ode_gene_id,
                                                   Geneweaver_Gene.ode_ref_id == ode_ref_id).first()).gdb_id
        gn_ref_id = convertODEtoAGR(ode_ref_id, gdb_id)
        gn_id = (db.query(Gene).filter(Gene.gn_ref_id == gn_ref_id).first()).gn_id
        if not gn_id:
            abort(404, message="No matching agr gene found")
        return gn_id


@NS.route('/get_ode_gene_by_gdb_id/<gdb_id>')
class get_ode_gene_by_gdb_id(Resource):
    '''
    :param: gdb_id
    :return: gene info (ode_gene_id, ode_ref_id, gdb_id, sp_id,
             ode_pref, ode_date, old_ode_gene_ids) of genes with
             gdb_id
    '''

    @NS.doc('return all ode_genes with the specified gdb_id')
    @NS.marshal_with(gw_gene_model)
    def get(self, gdb_id):
        genes = db.query(Geneweaver_Gene).filter(Geneweaver_Gene.gdb_id ==
                                                 gdb_id).all()
        if not genes:
            abort(404, message="No genes were found with specified gdb_id")
        return genes


@NS.route('/get_ode_gene_by_gene_id/<ode_gene_id>')
class get_ode_gene_by_gene_id(Resource):
    '''
    :param: ode_gene_id
    :return: gene info (ode_gene_id, ode_ref_id, gdb_id, sp_id,
             ode_pref, ode_date, old_ode_gene_ids) of genes with
             same ode_gene_id as given
    '''

    @NS.doc('return all ode_genes with the same ode_gene_id')
    @NS.marshal_with(gw_gene_model)
    def get(self, ode_gene_id):
        genes = db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id
                                                 == ode_gene_id).all()
        if not genes:
            abort(404, message="No genes were found matching that ode_gene_id")
        return genes


@NS.route('/get_ode_gene_by_species/<ode_gene_id>/<sp_name>')
class get_ode_gene_by_species(Resource):
    '''
    :param: ode_gene_id
            sp_name - case sensitive
    :return: gene info (ode_gene_id, ode_ref_id, gdb_id, sp_id,
             ode_pref, ode_date, old_ode_gene_ids) of genes with
             same ode_gene_id as given and within same species
    '''

    @NS.doc('return all genes with matching ode_gene_id and species')
    @NS.marshal_with(gw_gene_model)
    def get(self, ode_gene_id, sp_name):
        sp_id = (db.query(Geneweaver_Species).filter(Geneweaver_Species.sp_name ==
                                                     sp_name).first()).sp_id
        genes = db.query(Geneweaver_Gene).filter(Geneweaver_Gene.ode_gene_id == ode_gene_id,
                                                 Geneweaver_Gene.sp_id == sp_id).all()
        if not genes:
            abort(404, message="No genes were found matching that ode_gene_id and species")
        return genes


#################################################
# GW-AGR Integration Endpoints
#################################################

# converter functions using first char - these functions improve efficiency and
#    are used here instead of convertODEtoAGR and convertAGRtoGW because they require
#    gdb_id and are used more broadly.
def convert_ode_ref_to_agr(ode_ref):
    ref = ode_ref
    if ode_ref[0] == 'W':
        prefix = "WB"
        ref = prefix + ":" + ode_ref
    if ode_ref[0] == 'F':
        prefix = "FB"
        ref = prefix + ":" + ode_ref
    if ode_ref[0] == 'S':
        prefix = "SGD"
        ref = prefix + ":" + ode_ref
    if ode_ref[0] == 'Z':
        prefix = "ZFIN"
        ref = prefix + ":" + ode_ref
    if ode_ref[0] == 'R':
        ref = ode_ref[:3] + ":" + ode_ref[3:]
    return ref


def convert_species_ode_to_agr(ode_sp_id):
    sp_dict = {1: 1, 2: 7, 3: 9, 4: 6, 5: 12, 8: 4, 9: 3, 6: 10, 11: 9, 10: 8}
    return sp_dict[ode_sp_id]


def convert_agr_ref_to_ode(gn_ref_id):
    ref = gn_ref_id
    remove_first_letters = ['W', 'F', 'S', 'Z']
    if gn_ref_id[0] == "R":
        ref = ref.replace(":", "")
    elif gn_ref_id[0] in remove_first_letters:
        ind = ref.find(":") + 1
        ref = ref[ind:]
    return ref


@NS.route('/get_ort_id_if_gene_is_ortholog/<ode_gene_id>/<ode_ref_id>')
class get_ort_id_if_gene_is_ortholog(Resource):
    '''
    :param ode_ref_id - ode_ref_id of to gene
           ode_gene_id - ode_gene_id of to gene
    :return: list of ortholog ids that have specified gene as the from_gene
    '''

    @NS.doc('returns the ortholog id filtering by the ortholog from gene, including the gdb_id')
    def get(self, ode_gene_id, ode_ref_id):
        ref = convert_ode_ref_to_agr(ode_ref_id)
        # find matching agr gene and filter the ortholog table with the agr gene id
        gn_id = db.query(Gene.gn_id).filter(Gene.gn_ref_id == ref).first()
        ort_id = (
            db.query(Ortholog.ort_id).filter(
                (Ortholog.from_gene == gn_id) | (Ortholog.to_gene == gn_id))).all()
        return ort_id


@NS.route('/get_ortholog_by_from_gene_and_gdb/<from_ode_gene_id>/<gdb_id>')
class get_ortholog_by_from_gene_and_gdb(Resource):
    '''
    :param ode_gene_id - ode_gene_id of from gene
           gdb_id - gdb_id of specified gene, this is the gdb_id we are filtering by
    :return: to gene info (ode_ref_id) for any ortholog that has the given from
             gene. the goal is to find info about the orthologous gene from the given gene.
    '''

    @NS.doc('returns to gene ode_gene_id and ode_ref_id of any ortholog with the from gene matching'
            'the given ode_gene_id and to gene matching the gdb_id')
    def get(self, from_ode_gene_id, gdb_id):
        # any gene with a gdb_id that is not in the agr_compatible_gdb_ids will not be found in the agr
        #    database, so it is filtered out in the search.
        agr_compatible_gdb_ids = [10, 11, 12, 13, 14, 15, 16]
        genes = db.query(Geneweaver_Gene.ode_ref_id).filter(Geneweaver_Gene.ode_gene_id == from_ode_gene_id,
                                                            Geneweaver_Gene.gdb_id.in_(agr_compatible_gdb_ids)).all()
        if not genes:
            abort(404, message="no genes found under that gene id")

        # the species from the geneweaver database is translated into the agr_species id so it can
        #   be used to filter by species (gdb_id) within the agr database.
        gdb_id = int(gdb_id)
        gdb_to_agr_species = {10: 1, 11: 7, 12: 2, 13: 6, 14: 5, 15: 11, 16: 3}
        agr_species = gdb_to_agr_species[gdb_id]

        # ode_ref_ids are translated into the agr format found in the ref_id column of the
        #   agr gene table
        from_gene_refs = []
        for g in genes:
            ref = convert_ode_ref_to_agr(str(g[0]))
            from_gene_refs.append(ref)

        # a list of agr gene ids that match the ref ids
        from_gene_ids = db.query(Gene.gn_id).filter(Gene.gn_ref_id.in_(from_gene_refs)).all()

        # a list of to_gene ids where the from_gene value is in the from_genes list of ids
        to_gene_ids = db.query(Ortholog.to_gene).filter(Ortholog.from_gene.in_(from_gene_ids)).all()

        # agr ref ids of to_genes
        to_gene_refs = db.query(Gene.gn_ref_id).filter(Gene.gn_id.in_(to_gene_ids), Gene.sp_id == agr_species).all()

        # translate the agr format ref_ids back to ode format
        to_gene_ode_refs = []
        for r in to_gene_refs:
            to_gene_ode_refs.append(convert_agr_ref_to_ode(r))

        return to_gene_ode_refs


@NS.route('/if_ode_gene_has_ortholog/<ode_gene_id>')
class if_ode_gene_has_ortholog(Resource):
    '''
    :param ode_gene_id
    :return: boolean, if gene is an ortholog
    '''

    @NS.doc('check if ode gene is an ortholog')
    def get(self, ode_gene_id):
        is_ortholog = 1
        # any gene with a gdb_id that is not in the agr_compatible_gdb_ids will not be found in the agr
        #    database, so it is filtered out in the search.
        agr_compatible_gdb_ids = [10, 11, 12, 13, 14, 15, 16]
        ode_refs = db.query(Geneweaver_Gene.ode_ref_id).filter(Geneweaver_Gene.ode_gene_id == ode_gene_id,
                                                               Geneweaver_Gene.gdb_id.in_(agr_compatible_gdb_ids)).all()

        # ode_ref_ids are translated into the agr format found in the ref_id column of the
        #   agr gene table
        gn_ref_ids = []
        for g in ode_refs:
            ref = str(g[0])
            gn_ref_ids.append(convert_ode_ref_to_agr(ref))

        # find ortholog ids that are from the gene with given ode_gene_id
        gn_ids = db.query(Gene.gn_id).filter(Gene.gn_ref_id.in_(gn_ref_ids)).all()
        from_gene = db.query(Ortholog.ort_id).filter(Ortholog.from_gene.in_(gn_ids)).all()

        # if the gn_ids are not in any of the ortholog's from_gene or to_gene columns,
        #   the gene is not an ortholog
        if (len(from_gene) == 0):
            to_gene = db.query(Ortholog.ort_id).filter(Ortholog.to_gene.in_(gn_ids)).all()
            if (len(to_gene) == 0):
                is_ortholog = 0

        return is_ortholog


@NS.route('/get_intersect_by_orthology', methods=['GET', 'POST'])
class get_intersect_by_orthology(Resource):
    @NS.expect(parser)
    def get(self):
        '''
        :param: gs1 - taken from parser, list of gene info in geneset 1
                gs2 - taken from parser, list of gene info in geneset 2
        :return: gene info (gi_symbol, ode_gene_id, and ort_id) of
                 genes that intersect both genesets
        '''

        # gets list of genes for each geneset
        parser.add_argument('gs1', type=str, action="append")
        parser.add_argument('gs2', type=str, action="append")
        data = parser.parse_args()
        gs1 = data['gs1']
        gs2 = data['gs2']

        # each geneset is iterpreted as a list of strings, so every 5 strings is one
        #   gene's info. The following code determines the number of genes in each geneset
        gs1_len = int((len(gs1)) / 4)
        gs2_len = int((len(gs2)) / 4)
        genes = []

        for i in range(1, gs1_len):
            # find current index in list of strings to parse out gene1's info
            ndx = i * 4
            # format = [ ode_gene_id, ode_ref_id, gi_symbol, hom_id ]
            gene1_info = [gs1[ndx - 4], gs1[ndx - 3], gs1[ndx - 2], gs1[ndx - 1]]

            # get agr id of gene 1
            ref1 = str(gene1_info[1])
            gene_1_ref = convert_ode_ref_to_agr(ref1)
            gene1_id = (db.query(Gene).filter(Gene.gn_ref_id == gene_1_ref).first()).gn_id

            for j in range(1, gs2_len):
                ndx2 = j * 4
                gene2_info = [gs2[ndx2 - 4], gs2[ndx2 - 3], gs2[ndx2 - 2], gs2[ndx2 - 1]]
                gene_1_ortho = False

                # get agr id of gene 2
                ref2 = str(gene2_info[1])
                gene_2_ref = convert_ode_ref_to_agr(ref2)
                gene2_id = (db.query(Gene).filter(Gene.gn_ref_id == gene_2_ref).first()).gn_id

                # check orthologs with gene1 as from_gene and gene2 as to_gene
                ortho_1_2 = db.query(Ortholog.ort_id).filter(Ortholog.from_gene == gene1_id,
                                                             Ortholog.to_gene == gene2_id).all()

                if len(ortho_1_2) != 0:
                    gene_1_ortho = True
                    genes.append([gene2_info[0], gene2_info[2], gene2_info[3]])
                else:
                    # check orthologs with gene2 as from_gene and gene1 as to_gene
                    ortho_2_1 = db.query(Ortholog.ort_id).filter(Ortholog.from_gene == gene2_id,
                                                                 Ortholog.to_gene == gene1_id).all()
                    if len(ortho_2_1) != 0:
                        gene_1_ortho = True
                        genes.append([gene2_info[0], gene2_info[2], gene2_info[3]])

            # if any orthologs are found, add gene1
            if gene_1_ortho:
                genes.append([gene1_info[0], gene1_info[2], gene1_info[3]])
        return genes


@NS.route('/transpose_genes_by_species', methods=['GET', 'POST'])
class transpose_genes_by_homology(Resource):
    '''
    :params: genes - taken through parser, list of ode_ref_ids to be tranposed
             species - newSpecies that genes will be transposed to through orthology
    :return: list of ode_ref_ids of transposed genes, genes that are orthologs to the
             original genes but are of the specified newSpecies
    '''

    @NS.expect(parser)
    def get(self):
        parser.add_argument('genes', type=str, action="append")
        parser.add_argument('species', type=int)
        data = parser.parse_args()
        # sp contains the new species that the genes will be transposed to
        sp = data['species']

        # checking if sp is in the available agr species
        if sp not in [1, 2, 3, 4, 5, 8, 9]:
            abort(404, message="No matching genes with that species")
        else:
            sp = convert_species_ode_to_agr(sp)

        # store all converted refs in a parallel list to genes
        refs = []
        for g in data['genes']:
            refs.append(convert_ode_ref_to_agr(g))

        # get all from_gene_ids using list of ref ids
        from_gene_ids = db.query(Gene.gn_id).filter(Gene.gn_ref_id.in_(refs)).all()
        # get all to_gene_ids from ort_ortholog based on the from_gene_ids
        to_gene_ids = db.query(Ortholog.to_gene).filter(Ortholog.from_gene.in_(from_gene_ids)).all()
        # filter the to_gene_ids to only be genes that are of the given new species
        to_gene_filtered_refs = db.query(Gene.gn_ref_id).filter(Gene.gn_id.in_(to_gene_ids),
                                                                Gene.sp_id == sp).all()

        # convert the transposed genes back into geneweaver ode_ref_id format and return
        ode_refs = []
        for r in to_gene_filtered_refs:
            ode_refs.append(convert_agr_ref_to_ode(r[0]))

        return ode_refs