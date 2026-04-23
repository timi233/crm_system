"""Create entity_products table."""

from alembic import op


revision = "entity_products_001"
down_revision = "target_uniqueness_001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS entity_products (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(20) NOT NULL,
            entity_id INTEGER NOT NULL,
            product_type_id INTEGER REFERENCES dict_items(id),
            brand_id INTEGER REFERENCES dict_items(id),
            model_id INTEGER REFERENCES dict_items(id),
            quantity INTEGER DEFAULT 1,
            unit_price NUMERIC(10, 2) DEFAULT 0.00,
            created_at DATE NOT NULL DEFAULT CURRENT_DATE
        )
        """
    )
    op.execute(
        """
        ALTER TABLE entity_products
        ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1
        """
    )
    op.execute(
        """
        ALTER TABLE entity_products
        ADD COLUMN IF NOT EXISTS unit_price NUMERIC(10, 2) DEFAULT 0.00
        """
    )
    op.execute(
        """
        ALTER TABLE entity_products
        ADD COLUMN IF NOT EXISTS created_at DATE NOT NULL DEFAULT CURRENT_DATE
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_entity_products_entity
        ON entity_products(entity_type, entity_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_entity_products_product_type
        ON entity_products(product_type_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_entity_products_brand
        ON entity_products(brand_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_entity_products_model
        ON entity_products(model_id)
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_entity_products_model")
    op.execute("DROP INDEX IF EXISTS idx_entity_products_brand")
    op.execute("DROP INDEX IF EXISTS idx_entity_products_product_type")
    op.execute("DROP INDEX IF EXISTS idx_entity_products_entity")
    op.execute("DROP TABLE IF EXISTS entity_products")
