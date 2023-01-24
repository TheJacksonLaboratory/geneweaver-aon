"""
Creates AGR tables algorithm, species, gene, ortholog, and ortholog_algorithms.
These tables will be filled from the AGR file by running service.py

Revision ID: 4297df5638d7
Revises: 
Create Date: 2020-12-16 19:27:45.142317

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4297df5638d7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('alg_algorithm',
    sa.Column('alg_id', sa.Integer(), nullable=False),
    sa.Column('alg_name', sa.String()),
    sa.PrimaryKeyConstraint('alg_id'),
    sa.UniqueConstraint('alg_name')
    )
    op.create_table('sp_species',
    sa.Column('sp_id', sa.Integer(), nullable=False),
    sa.Column('sp_name', sa.String(), nullable=False),
    sa.Column('sp_taxon_id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('sp_id')
    )
    op.create_table('gn_gene',
    sa.Column('gn_id', sa.Integer(), nullable=False),
    sa.Column('gn_ref_id', sa.String()),
    sa.Column('gn_prefix', sa.String()),
    sa.Column('sp_id', sa.Integer()),
    sa.ForeignKeyConstraint(['sp_id'], ['sp_species.sp_id'], ),
    sa.PrimaryKeyConstraint('gn_id'),
    sa.UniqueConstraint('gn_ref_id')
    )
    op.create_table('ort_ortholog',
    sa.Column('ort_id', sa.Integer(), nullable=False),
    sa.Column('from_gene', sa.Integer()),
    sa.Column('to_gene', sa.Integer()),
    sa.Column('ort_is_best', sa.Boolean()),
    sa.Column('ort_is_best_revised', sa.Boolean()),
    sa.Column('ort_is_best_is_adjusted', sa.Boolean()),
    sa.Column('ort_num_possible_match_algorithms', sa.Integer()),
    sa.Column('ort_source_name', sa.VARCHAR()),
    sa.ForeignKeyConstraint(['from_gene'], ['gn_gene.gn_id'], ),
    sa.ForeignKeyConstraint(['to_gene'], ['gn_gene.gn_id'], ),
    sa.PrimaryKeyConstraint('ort_id')
    )
    op.create_table('ora_ortholog_algorithms',
    sa.Column('ora_id', sa.Integer(), primary_key=True),
    sa.Column('alg_id', sa.Integer()),
    sa.Column('ort_id', sa.Integer()),
    sa.ForeignKeyConstraint(['alg_id'], ['alg_algorithm.alg_id'], ),
    sa.ForeignKeyConstraint(['ort_id'], ['ort_ortholog.ort_id'], )
    )
    op.create_table('hom_homology',
    sa.Column('hom_id', sa.Integer()),
    sa.Column('gn_id', sa.Integer()),
    sa.Column('sp_id', sa.Integer()),
    sa.Column('hom_source_name', sa.VARCHAR()),
    sa.ForeignKeyConstraint(['gn_id'], ['gn_gene.gn_id'], ),
    sa.ForeignKeyConstraint(['sp_id'], ['sp_species.sp_id'], ),
    sa.UniqueConstraint('hom_id', 'gn_id', name='unique_homolog')
    )

def downgrade():
    op.drop_table('ora_ortholog_algorithms')
    op.drop_table('ort_ortholog')
    op.drop_table('gn_gene')
    op.drop_table('sp_species')
    op.drop_table('alg_algorithm')
    op.drop_table('hom_homology')