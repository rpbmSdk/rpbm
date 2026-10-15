"""Crée les colonnes du prix fournisseur des lignes de devis avant la mise à jour. Idempotent.

Une colonne déjà présente n'est pas recalculée par l'ORM (_auto_init) : les ~137 000 lignes
historiques restent vides au lieu d'être recalculées pendant la mise à jour ; seules les lignes
neuves, ou dont l'article change, reçoivent le prix fournisseur.
"""


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE sale_order_line
            ADD COLUMN IF NOT EXISTS rpbm_supplier_price numeric,
            ADD COLUMN IF NOT EXISTS rpbm_supplier_id int4
    """)
