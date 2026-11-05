import os
import re
import sqlite3
from datetime import datetime

APP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "GeradorCodigoBarras")
os.makedirs(APP_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DIR, "dados.db")


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _columns(conn, table):
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def init_db():
    """Create the current schema and migrate databases from previous versions safely."""
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                width_mm REAL NOT NULL,
                height_mm REAL NOT NULL
            )
        """)
        for name, width, height in [
            ("50 x 30 mm", 50, 30),
            ("80 x 40 mm", 80, 40),
            ("100 x 50 mm", 100, 50),
        ]:
            conn.execute(
                "INSERT OR IGNORE INTO templates(name,width_mm,height_mm) VALUES(?,?,?)",
                (name, width, height),
            )

        if "products" not in {
            row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }:
            conn.execute("""
                CREATE TABLE products (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE COLLATE NOCASE NOT NULL,
                    template_id INTEGER REFERENCES templates(id),
                    last_number INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

        product_cols = _columns(conn, "products")
        if "normalized_name" in product_cols:
            # Older database required this extra field on every product insert.
            pass
        if "last_number" not in product_cols:
            conn.execute("ALTER TABLE products ADD COLUMN last_number INTEGER NOT NULL DEFAULT 0")
        if "template_id" not in product_cols:
            conn.execute("ALTER TABLE products ADD COLUMN template_id INTEGER REFERENCES templates(id)")
        if "created_at" not in product_cols:
            conn.execute("ALTER TABLE products ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")

        label_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='labels'"
        ).fetchone()
        if not label_exists:
            conn.execute("""
                CREATE TABLE labels (
                    id INTEGER PRIMARY KEY,
                    product_id INTEGER NOT NULL REFERENCES products(id),
                    sequence INTEGER NOT NULL,
                    barcode TEXT UNIQUE NOT NULL,
                    template_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(product_id, sequence)
                )
            """)
        else:
            label_cols = _columns(conn, "labels")
            if not {"sequence", "barcode", "template_name"}.issubset(label_cols):
                # Preserve IDs, products, barcode values, timestamps and template names.
                sequence_col = "sequence_number" if "sequence_number" in label_cols else "sequence"
                barcode_col = "barcode_value" if "barcode_value" in label_cols else "barcode"
                if sequence_col not in label_cols or barcode_col not in label_cols:
                    raise RuntimeError("Estrutura antiga do histórico não reconhecida. O banco foi preservado.")
                conn.execute("DROP TABLE IF EXISTS labels_migration")
                conn.execute("""
                    CREATE TABLE labels_migration (
                        id INTEGER PRIMARY KEY,
                        product_id INTEGER NOT NULL REFERENCES products(id),
                        sequence INTEGER NOT NULL,
                        barcode TEXT UNIQUE NOT NULL,
                        template_name TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        UNIQUE(product_id, sequence)
                    )
                """)
                if "template_name" in label_cols:
                    template_expr = "l.template_name"
                elif "template_id" in label_cols:
                    template_expr = "COALESCE((SELECT t.name FROM templates t WHERE t.id=l.template_id), 'Modelo antigo')"
                else:
                    template_expr = "'Modelo antigo'"
                conn.execute(f"""
                    INSERT INTO labels_migration(id, product_id, sequence, barcode, template_name, created_at)
                    SELECT l.id, l.product_id, l.{sequence_col}, l.{barcode_col},
                           {template_expr}, l.created_at
                    FROM labels l
                """)
                conn.execute("DROP TABLE labels")
                conn.execute("ALTER TABLE labels_migration RENAME TO labels")

        conn.execute("""
            UPDATE products
            SET last_number = MAX(
                COALESCE(last_number, 0),
                COALESCE((SELECT MAX(sequence) FROM labels WHERE labels.product_id=products.id), 0)
            )
        """)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def templates():
    init_db()
    with connect() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM templates ORDER BY width_mm")]


def products():
    init_db()
    with connect() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM products ORDER BY name COLLATE NOCASE")]


def create_product(name, template_id):
    name = " ".join(name.split())
    if not name:
        raise ValueError("Informe o produto.")
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        cols = _columns(conn, "products")
        if "normalized_name" in cols:
            conn.execute(
                """INSERT OR IGNORE INTO products(name, normalized_name, template_id, created_at)
                   VALUES(?,?,?,?)""",
                (name, name.casefold(), template_id, now),
            )
        else:
            conn.execute(
                """INSERT OR IGNORE INTO products(name, template_id, created_at)
                   VALUES(?,?,?)""",
                (name, template_id, now),
            )
        conn.execute("UPDATE products SET template_id=? WHERE name=? COLLATE NOCASE", (template_id, name))
        row = conn.execute("SELECT id FROM products WHERE name=? COLLATE NOCASE", (name,)).fetchone()
        if not row:
            raise RuntimeError("Não foi possível cadastrar o produto.")
        return row["id"]


def next_label(product_id, template_id):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        template = conn.execute("SELECT * FROM templates WHERE id=?", (template_id,)).fetchone()
        if not product or not template:
            raise ValueError("Produto ou modelo inválido.")
        number = int(product["last_number"] or 0) + 1
        prefix = re.sub(r"[^A-Z0-9]+", "-", product["name"].upper()).strip("-") or "PRODUTO"
        barcode = f"{prefix}-{number:06d}"
        conn.execute(
            "UPDATE products SET last_number=?, template_id=? WHERE id=?",
            (number, template_id, product_id),
        )
        conn.execute(
            """INSERT INTO labels(product_id,sequence,barcode,template_name,created_at)
               VALUES(?,?,?,?,?)""",
            (product_id, number, barcode, template["name"], datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
        )
        return {"barcode": barcode, "product": product["name"], "template": dict(template), "sequence": number}


def history(limit=150):
    init_db()
    with connect() as conn:
        return [dict(row) for row in conn.execute(
            """SELECT p.name product,l.barcode,l.template_name,l.created_at
               FROM labels l JOIN products p ON p.id=l.product_id
               ORDER BY l.id DESC LIMIT ?""",
            (limit,),
        )]


init_db()
