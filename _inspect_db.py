import sqlite3, os
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "database", "qingli.db")
if not os.path.exists(db_path):
    cands = []
    for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
        for f in files:
            if f.endswith('.db'):
                cands.append(os.path.join(root, f))
    db_path = cands[0] if cands else None
print("DB:", db_path)
if db_path:
    c = sqlite3.connect(db_path)
    cur = c.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables:", cur.fetchall())
    cur.execute("SELECT COUNT(*) FROM subjects")
    print("subjects count:", cur.fetchone())
    cur.execute("SELECT COUNT(*) FROM knowledge_nodes")
    print("knowledge_nodes count:", cur.fetchone())
    cur.execute("SELECT id, name, education_level FROM subjects")
    for r in cur.fetchall(): print(" subject:", r)
    cur.execute("SELECT id, name, parent_id, education_level, grade FROM knowledge_nodes LIMIT 50")
    rows = cur.fetchall()
    for r in rows: print(r)
