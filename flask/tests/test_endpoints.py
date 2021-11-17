"""
Tests every endpoint

Endpoints that return many items are compared to json file in the results directory to
confirm correct output. This can be done by directly comparing the output and the file,
or comparing the IDs of both.

Endpoints that return a couple items or less information are directly compared in a single
assertion.

All endpoints are checked for a '200 OK' status. If the query was unsuccessful, this assertion
will not pass in the first place.
"""
import unittest
import xmlrunner

import sys, os

sys.path.append(os.path.abspath(os.path.join('..', 'src')))

from wsgi import application

class testEndpoints(unittest.TestCase):

    def setUp(self):
        # initialize logic for test method, is run before each test
        application.app.config['DEBUG'] = True
        application.app.config['TESTING'] = True
        self.app = application.app.test_client()

    def tearDown(self):
        # take down anything we've specifically created for each test method
        self.app = None

    def test_app_root(self):
        rv = self.app.get('/')
        # then expect a 200...
        assert '200 OK' in rv.status

    def test_get_algorithm_by_name(self):
        rv = self.app.get('/agr-service/get_algorithm_by_name/ZFIN')
        assert (b'12' in rv.data and b'ZFIN' in rv.data)
        assert '200 OK' in rv.status

    def test_all_algorithms(self):
        rv = self.app.get('/agr-service/all_algorithms')
        assert len(rv.json) == 12


    def test_all_orthologs(self):
        rv = self.app.get('/agr-service/all_orthologs')
        assert len(rv.json) == 558386

    def test_get_orthologs_by_from_gene(self):
        rv = self.app.get('/agr-service/get_orthologs_by_from_gene/ZDB-GENE-040426-960/181874')
        data = rv.json
        ids = [element['ort_id'] for element in data]
        assert len(data) == 6
        assert 25183 in ids and 425204 in ids

    def test_get_orthologs_by_to_gene(self):
        rv = self.app.get('/agr-service/get_orthologs_by_to_gene/S000000004/366222')
        assert len(rv.json) == 32
        assert (rv.json)[0]['ort_id'] == 3546

    def test_get_ortholog_by_id(self):
        rv = self.app.get('/agr-service/get_ortholog_by_id/1')
        ortholog = rv.json
        assert ortholog[0]['ort_id'] == 1
        assert '200 OK' in rv.status

    def test_get_orthologs_by_to_and_from_gene(self):
        rv = self.app.get('/agr-service/get_orthologs_by_to_and_from_gene/WBGene00019900/336853/FBgn0260453/254551')
        assert (rv.json)[0]['from_gene'] == 12620 and (rv.json)[0]['to_gene'] == 12635

    def test_get_orthologs_by_from_gene_and_best(self):
        rv = self.app.get('/agr-service/get_orthologs_by_from_gene_and_best/HGNC:3211/78104/T')
        assert len(rv.json) == 7

    def test_get_orthologs_by_from_to_gene_and_best(self):
        rv = self.app.get('/agr-service/get_orthologs_by_from_to_gene_and_best/RGD620664/91714/S000000004/366222/true')
        assert (rv.json)[0]['from_gene'] == 3793 and (rv.json)[0]['to_gene'] == 3786 and (rv.json)[0]['ort_is_best'] == True

    def test_get_orthologs_by_from_to_gene_and_revised(self):
        rv = self.app.get('/agr-service/get_orthologs_by_from_to_gene_and_revised/RGD620664/91714/S000000004/366222/false')
        assert len(rv.json) == 1
        assert (rv.json)[0]['ort_id'] == 3553

    def test_get_from_gene_of_ortholog_by_id(self):
        rv = self.app.get('/agr-service/get_from_gene_of_ortholog_by_id/1')
        assert (rv.json)['gn_id'] == 1 and (rv.json)['gn_ref_id'] == 'WB:WBGene00011502'

    def test_get_to_gene_of_ortholog_by_id(self):
        rv = self.app.get('/agr-service/get_to_gene_of_ortholog_by_id/112199')
        assert rv.json['gn_id'] == 65603 and rv.json['gn_ref_id'] == 'ZFIN:ZDB-GENE-010309-3'

    def test_all_genes(self):
        rv = self.app.get('/agr-service/all_genes')
        assert len(rv.json) == 100430

    def test_get_genes_by_prefix(self):
        rv = self.app.get('/agr-service/get_genes_by_prefix/MGI')
        assert len(rv.json) == 20670

    def test_get_genes_by_ode_gene_id(self):
        rv = self.app.get('/agr-service/get_genes_by_ode_gene_id/HGNC%3A3211/78104')
        assert rv.json['gn_id'] == 3781 and rv.json['gn_ref_id'] == 'HGNC:3211'

    def test_get_genes_by_species(self):
        rv = self.app.get('/agr-service/get_genes_by_species/Danio%20rerio')
        assert len(rv.json) == 18660

    def test_get_gene_species_name(self):
        rv = self.app.get('/agr-service/get_gene_species_name/FBgn0013275/267529')
        assert (b'Drosophila melanogaster' in rv.data)
        assert '200 OK' in rv.status

    def test_all_species(self):
        rv = self.app.get('/agr-service/all_species')
        assert len(rv.json) == 7

    def test_get_species_by_id(self):
        rv = self.app.get('/agr-service/get_species_by_id/3')
        assert (b'Saccharomyces cerevisiae' in rv.data and b'559292' in rv.data)
        assert '200 OK' in rv.status

    def test_get_orthologs_by_num_algoritms(self):
        rv = self.app.get('/agr-service/get_orthologs_by_num_algoritms/11')
        assert len(rv.json) == 160862

    def test_get_ortholog_by_algorithm(self):
        rv = self.app.get('/agr-service/get_ortholog_by_algorithm/HGNC')
        data = rv.json
        ids = [element['ort_id'] for element in data]
        assert all(i in ids for i in [199869, 199959, 204513, 215632, 209234, 240617, 527434, 558257])
        assert len(data) == 70474

    def test_all_homology(self):
        rv = self.app.get('/agr-service/all_homology')
        assert len(rv.json) == 481484
        assert (rv.json)[0]['hom_id'] == 1

    def test_get_homology_by_id(self):
        rv = self.app.get('/agr-service/get_homolgy_by_id/14')
        assert len(rv.json) == 22
        assert (rv.json)[0]['gn_id'] == 128

    def test_get_homology_by_gene(self):
        rv = self.app.get('/agr-service/get_homology_by_gene/147')
        assert len(rv.json) == 6
        assert (rv.json)[0]['gn_id'] == 147 and (rv.json)[0]['hom_id'] == 14

    def test_get_homology_by_species(self):
        rv = self.app.get('/agr-service/get_homology_by_species/2')
        data = rv.json
        ids = [element['sp_id'] for element in data]
        assert len(data) == 84552
        assert list(set(ids))[0] == 2

    def test_get_homology_by_id_and_species(self):
        rv = self.app.get('/agr-service/get_homology_by_id_and_species/12/2')
        data = rv.json
        assert len(data) == 1
        assert data[0]['hom_id'] == 12 and data[0]['sp_id'] == 2

    def test_get_homology_by_id_and_source(self):
        rv = self.app.get('/agr-service/get_homology_by_id_and_source/6/AGR')
        data = rv.json
        assert len(data) == 12
        assert data[2]['hom_id'] == 6 and data[0]['hom_source_name'] == 'AGR'

    def test_get_homology_by_gene_and_source(self):
        rv = self.app.get('/agr-service/get_homology_by_gene_and_source/28220/AGR')
        data = rv.json
        assert len(data) == 10
        assert data[2]['gn_id'] == 28220 and data[0]['hom_source_name'] == 'AGR'

    def test_get_ortholog_by_from_species(self):
        rv = self.app.get('/agr-service/get_ortholog_by_from_species/Homo%20sapiens')
        assert len(rv.json) == 101329
        assert (rv.json)[0]['from_gene'] == 6

    def test_get_ortholog_by_to_species(self):
        rv = self.app.get('/agr-service/get_ortholog_by_to_species/Saccharomyces%20cerevisiae')
        assert len(rv.json) == 31859
        assert (rv.json)[0]['to_gene'] == 2

    def test_get_ortholog_by_to_and_from_species(self):
        rv = self.app.get('/agr-service/get_ortholog_by_to_and_from_species/Danio%20rerio/Mus%20musculus')
        data = list(rv.json)
        ids = [element['ort_id'] for element in data]
        assert len(rv.json) == 22707
        assert 178696 in ids and 106886 in ids and 108579 in ids

    def test_get_ortholog_by_to_from_species_and_algorithm(self):
        rv = self.app.get('/agr-service/get_ortholog_by_to_from_species_and_algorithm/Saccharomyces%20cerevisiae/Drosophila'
                          '%20melanogaster/PANTHER')
        assert len(rv.json) == 3680
        assert (rv.json)[0]['from_gene'] == 7 and (rv.json)[0]['to_gene'] == 2

    def test_agr_to_geneweaver_species(self):
        rv = self.app.get('/agr-service/agr_to_geneweaver_species/2')
        assert b'3' in rv.data
        assert '200 OK' in rv.status

    def test_id_convert_agr_to_ode(self):
        rv = self.app.get('/agr-service/id_convert_agr_to_ode/34387')
        assert rv.json == 270952

    def test_id_convert_ode_to_agr(self):
        rv = self.app.get('/agr-service/id_convert_ode_to_agr/366222/S000000004')
        assert rv.json == 3786

    def test_get_ode_gene_by_gdb_id(self):
        rv = self.app.get('/agr-service/get_ode_gene_by_gdb_id/13')
        data = list(rv.json)
        ode_gene_ids = [element['ode_gene_id'] for element in data]
        assert len(rv.json) == 111648
        assert all(ids in ode_gene_ids for ids in [163896, 165108, 165168, 139768, 141616, 143806])

    def test_get_ode_gene_by_gene_id(self):
        rv = self.app.get('/agr-service/get_ode_gene_by_gene_id/96483')
        assert b'LOC100363666' in rv.data and b'RGD2322584' in rv.data
        assert '200 OK' in rv.status

    def test_get_ode_gene_by_species(self):
        rv = self.app.get('/agr-service/get_ode_gene_by_species/96602/Rattus%20norvegicus')
        assert b'LOC100363817' in rv.data and b'RGD2322238' in rv.data
        assert '200 OK' in rv.status

    def test_get_ort_id_if_gene_is_ortholog(self):
        rv = self.app.get('/agr-service/get_ort_id_if_gene_is_ortholog/191876/ZDB-GENE-070112-1002')
        data = list(rv.json)
        assert len(data) == 14
        assert all(ids in data for ids in [[24382], [139827], [139830], [139832], [255497], [7]])

    def test_get_ortholog_by_from_gene_and_gdb(self):
        rv = self.app.get('/agr-service/get_ortholog_by_from_gene_and_gdb/12/11')
        data = list(rv.json)
        assert len(data) == 1
        assert data[0][0] == 'HGNC:88'

    def test_if_ode_gene_has_ortholog(self):
        rv = self.app.get('/agr-service/if_ode_gene_has_ortholog/133128')
        assert rv.json == 1

    def test_get_intersect_by_orthology(self):
        rv = self.app.get('/agr-service/get_intersect_by_orthology?gs1=329155&gs1=WBGene00011502&gs1'
                          '=vps-53&gs1=6264&gs1=366400&gs1=S000003566&gs1=VPS53&gs1=68774&gs2=366400&'
                          'gs2=S000003566&gs2=VPS53&gs2=68774&gs2=329155&gs2=WBGene00011502&gs2=vps-53'
                          '&gs2=6264')
        assert len(rv.json) == 2
        assert (rv.json)[0][0] == '366400' and (rv.json)[1][0] == '329155'

    def test_transpose_genes_by_homology(self):
        rv = self.app.get('/agr-service/transpose_genes_by_species?genes=AAG12&genes=PEMP&genes=DXS552'
                          'E&genes=EMP55&genes=4354&genes=HGNC%3A7219&genes=Hs.496984&genes=Hs.1861&ge'
                          'nes=Hs.372714&genes=Hs.422215&genes=Hs.322719&genes=Hs.376448&genes=Hs.3476'
                          '0&genes=Hs.75304&genes=ENSG00000130830&genes=MPP1&species=1')
        assert (rv.json)[0] == 'MGI:105941'

if __name__ == '__main__':
    unittest.main(testRunner=xmlrunner.XMLTestRunner(output='reports/test-application'))
