"""Persistência local do Gerador de Código de Barras."""
from pathlib import Path
import os
import sqlite3
import re
import unicodedata

APP_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GeradorCodigoBarras"
APP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DIR / "dados.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def normalize_name(name):
    name = unicodedata.normalize("NFKC", name or "")
    return re.sub(r"\\s+", " ", name).strip().casefold()

def init_db():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            width_mm REAL NOT NULL,
            height_mm REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            template_id INTEGER NOT NULL REFERENCES templates(id),
            last_number INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS labels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            sequence_number INTEGER NOT NULL,
            barcode_value TEXT NOT NULL UNIQUE,
            template_id INTEGER NOT NULL REFERENCES templates(id),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product_id, sequence_number)
        );
        """)
        defaults = [("Etiqueta 50 x 30 mm", 50, 30),
                    ("Etiqueta 80 x 40 mm", 80, 40),
                    ("Etiqueta 100 x 50 mm", 100, 50)]
        for item in defaults:
            db.execute("INSERT OR IGNORE INTO templates(name,width_mm,height_mm) VALUES(?,?,?)", item)

def templates():
    with connect() as db:
        return db.execute("SELECT * FROM templates ORDER BY width_mm, height_mm").fetchall()

def products():
    with connect() as db:
        return db.execute("""SELECT p.*, t.name AS template_name
            FROM products p JOIN templates t ON t.id=p.template_id
            ORDER BY p.name COLLATE NOCASE""").fetchall()

def save_product(name, template_id):
    name = re.sub(r"\\s+", " ", (name or "")).strip()
    if not name:
        raise ValueError("Informe o nome do produto.")
    with connect() as db:
        db.execute("""INSERT INTO products(name,normalized_name,template_id)
            VALUES(?,?,?) ON CONFLICT(normalized_name) DO UPDATE SET
            name=excluded.name, template_id=excluded.template_id""",
            (name, normalize_name(name), int(template_id)))

def generate_label(product_id):
    # BEGIN IMMEDIATE serializa a atualização do contador entre instâncias.
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if product is None:
            raise ValueError("Produto não encontrado.")
        number = product["last_number"] + 1
        value = f"{slug(product['name'])}-{number:04d}"
        db.execute("UPDATE products SET last_number=? WHERE id=?", (number, product_id))
        db.execute("""INSERT INTO labels(product_id,sequence_number,barcode_value,template_id)
            VALUES(?,?,?,?)""", (product_id, number, value, product["template_id"]))
        return value

def slug(name):
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    text = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").upper()
    return text or "PRODUTO"

def recent_labels(limit=100):
    with connect() as db:
        return db.execute("""SELECT l.*, p.name AS product_name,
            t.name AS template_name FROM labels l
            JOIN products p ON p.id=l.product_id
            JOIN templates t ON t.id=l.template_id
            ORDER BY l.id DESC LIMIT ?""", (limit,)).fetchall()
