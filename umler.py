# umler_app.py
import sqlite3
import subprocess
from tkinter import Tk, filedialog, Button, Label, messagebox
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
jar_path = os.path.join(base_dir, "plantuml.jar")

def sqlite_to_plantuml(db_path, output="diag.uml"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # tables list
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
    """)
    tables = [t[0] for t in cur.fetchall()]

    entities = []
    relations = []
    destinations = []
    pairs = []

    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()

        pk = []
        other = []

        for c in cols:
            name = c[1]
            is_pk = c[5]
            if is_pk:
                pk.append(name)
            else:
                other.append(name)

        block = [f"entity {table} {{"]
        for i in pk:
            block.append(f"  {i}")
        if other:
            block.append("  ---")
        for i in other:
            block.append(f"  {i}")
        block.append("}")
        entities.append("\n".join(block))

        cur.execute(f"PRAGMA foreign_key_list({table})")
        fks = cur.fetchall()

        for fk in fks:
            from_col = fk[3]
            to_table = fk[2]
            to_col = fk[4]
            destinations.append(to_table)
            pairs.append((to_table, (f"{table}::{from_col}", f"{to_table}::{to_col}")))

    from collections import Counter
    for p in pairs:
        arrow = "->"
        count = Counter(destinations)[p[0]]
        if count > 1:
            arrow = "-" * count + ">"
        relations.append(f"{p[1][0]} {arrow} {p[1][1]}")

    conn.close()

    with open(output, "w") as f:
        f.write("@startuml\n\n")
        for e in entities:
            f.write(e + "\n\n")
        for r in relations:
            f.write(r + "\n")
        f.write("\n@enduml\n")

    try:
        subprocess.run(["java", "-jar", jar_path, output], check=True)
    except Exception as e:
        print(e)


def select_db_and_generate():
    db_path = filedialog.askopenfilename(
        title="Выберите SQLite DB",
        filetypes=[("SQLite DB", "*.db"), ("SQLite DB", "*.sqlite"), ("Все файлы", "*.*")]
    )
    if db_path:
        sqlite_to_plantuml(db_path)
        messagebox.showinfo("Готово", "Созданы файлы diag.uml и diag.png")


root = Tk()
root.title("UMler App")
root.geometry("300x100")

Label(root, text="Выберите базу данных и генерируйте UML").pack(pady=10)
Button(root, text="Выбрать DB и сгенерировать", command=select_db_and_generate).pack(pady=5)

root.mainloop()