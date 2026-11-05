import os, re, sqlite3
from datetime import datetime
APP_DIR=os.path.join(os.environ.get("LOCALAPPDATA",os.path.expanduser("~")),"GeradorCodigoBarras")
os.makedirs(APP_DIR,exist_ok=True)
DB_PATH=os.path.join(APP_DIR,"dados.db")
def connect():
 c=sqlite3.connect(DB_PATH,timeout=15); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def init_db():
 with connect() as c:
  c.executescript("""
  CREATE TABLE IF NOT EXISTS templates(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,width_mm REAL NOT NULL,height_mm REAL NOT NULL);
  CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT UNIQUE COLLATE NOCASE NOT NULL,template_id INTEGER REFERENCES templates(id),last_number INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS labels(id INTEGER PRIMARY KEY,product_id INTEGER NOT NULL REFERENCES products(id),sequence INTEGER NOT NULL,barcode TEXT UNIQUE NOT NULL,template_name TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(product_id,sequence));
  """)
  for row in [("50 x 30 mm",50,30),("80 x 40 mm",80,40),("100 x 50 mm",100,50)]:
   c.execute("INSERT OR IGNORE INTO templates(name,width_mm,height_mm) VALUES(?,?,?)",row)
def templates():
 init_db()
 with connect() as c:return [dict(x) for x in c.execute("SELECT * FROM templates ORDER BY width_mm")]
def products():
 init_db()
 with connect() as c:return [dict(x) for x in c.execute("SELECT * FROM products ORDER BY name COLLATE NOCASE")]
def create_product(name,template_id):
 name=" ".join(name.split())
 if not name: raise ValueError("Informe o produto.")
 with connect() as c:
  c.execute("INSERT OR IGNORE INTO products(name,template_id,created_at) VALUES(?,?,?)",(name,template_id,datetime.now().isoformat(timespec="seconds")))
  c.execute("UPDATE products SET template_id=? WHERE name=? COLLATE NOCASE",(template_id,name))
  return c.execute("SELECT id FROM products WHERE name=? COLLATE NOCASE",(name,)).fetchone()["id"]
def next_label(product_id,template_id):
 with connect() as c:
  c.execute("BEGIN IMMEDIATE")
  p=c.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
  t=c.execute("SELECT * FROM templates WHERE id=?",(template_id,)).fetchone()
  if not p or not t: raise ValueError("Produto ou modelo inválido.")
  n=p["last_number"]+1
  prefix=re.sub(r"[^A-Z0-9]+","-",p["name"].upper()).strip("-") or "PRODUTO"
  code=f"{prefix}-{n:06d}"
  c.execute("UPDATE products SET last_number=?,template_id=? WHERE id=?",(n,template_id,product_id))
  c.execute("INSERT INTO labels(product_id,sequence,barcode,template_name,created_at) VALUES(?,?,?,?,?)",(product_id,n,code,t["name"],datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
  return {"barcode":code,"product":p["name"],"template":dict(t),"sequence":n}
def history(limit=150):
 init_db()
 with connect() as c:return [dict(x) for x in c.execute("SELECT p.name product,l.barcode,l.template_name,l.created_at FROM labels l JOIN products p ON p.id=l.product_id ORDER BY l.id DESC LIMIT ?",(limit,))]
init_db()
