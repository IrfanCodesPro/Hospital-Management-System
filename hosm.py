import sqlite3
import pandas as pd
from tkinter import *
from tkinter import messagebox
from tkinter import ttk

# === DATABASE SETUP ===
conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

# ID is now TEXT so we can control the custom range, not INTEGER AUTOINCREMENT
cursor.execute('''CREATE TABLE IF NOT EXISTS doctors 
                  (id TEXT PRIMARY KEY, name TEXT, specialty TEXT, phone TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS patients 
                  (id TEXT PRIMARY KEY, name TEXT, age TEXT, illness TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS nurses 
                  (id TEXT PRIMARY KEY, name TEXT, shift TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS workers 
                  (id TEXT PRIMARY KEY, name TEXT, role TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS op 
                  (id TEXT PRIMARY KEY, patient_name TEXT, date TEXT, doctor TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS billing 
                  (id TEXT PRIMARY KEY, patient_name TEXT, amount TEXT, date TEXT)''')
conn.commit()

# === CUSTOM ID GENERATOR ===
id_start_map = {
    "doctors": 1,
    "patients": 101,
    "nurses": 201,
    "workers": 301,
    "op": 401,
    "billing": 501
}

def generate_custom_id(table):
    cursor.execute(f"SELECT id FROM {table}")
    ids = cursor.fetchall()
    numbers = [int(i[0]) for i in ids if i[0].isdigit()]
    next_id = max(numbers) + 1 if numbers else id_start_map[table]
    return str(next_id)

# === EXCEL EXPORT ===
excel_path = ("C:/Users/91934/Desktop/hospital_data.xlsx")

def export_to_excel():
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for table in ["doctors", "patients", "nurses", "workers", "op", "billing"]:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            df.to_excel(writer, sheet_name=table.capitalize(), index=False)

# === ADD ENTRY FUNCTION ===
def add_entry(table, values, fields, clear_funcs, tree, fetch_func):
    if all(v.get().strip() for v in values):
        typed_values = [v.get().strip() for v in values]
        new_id = generate_custom_id(table)

        try:
            cursor.execute(
                f"INSERT INTO {table} (id, {', '.join(fields)}) VALUES (?, {', '.join(['?'] * len(fields))})",
                (new_id, *typed_values)
            )
            conn.commit()
            for clear in clear_funcs:
                clear.set("")
            messagebox.showinfo("Success", f"{table[:-1].capitalize()} added successfully!")
            fetch_func()
            export_to_excel()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Database Error", str(e))
    else:
        messagebox.showerror("Error", "Please fill all fields")

# === DELETE ENTRY FUNCTION ===
def delete_entry(table, tree, fetch_func):
    selected_item = tree.selection()
    if selected_item:
        record_id = tree.item(selected_item, "values")[0]
        cursor.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
        conn.commit()
        tree.delete(selected_item)
        messagebox.showinfo("Success", f"{table[:-1].capitalize()} deleted successfully!")
        fetch_func()
        export_to_excel()
    else:
        messagebox.showerror("Error", f"Please select a {table[:-1]} to delete")

# === FETCH DATA FUNCTION ===
def fetch_data(table, tree):
    tree.delete(*tree.get_children())
    cursor.execute(f"SELECT * FROM {table}")
    for row in cursor.fetchall():
        tree.insert("", END, values=row)

# === GUI SETUP ===
root = Tk()
root.title("Hospital Management System")
root.geometry("900x720")
root.configure(bg="#e8f0fe")

trees = {}
pages = []

# === CREATE SECTION FUNCTION ===
def create_section(parent, title, table, fields, bg):
    lf = LabelFrame(parent, text=f"{title} Management", bg=bg, fg="#003366",
                    font=("Arial", 13, "bold"), padx=10, pady=10, relief=RIDGE, bd=3)
    lf.pack(padx=15, pady=10, fill="x")

    frame = Frame(lf, bg=bg)
    frame.pack(pady=5)

    vars_ = [StringVar() for _ in fields]
    for idx, (field, var) in enumerate(zip(fields, vars_)):
        field_name = field.replace("_", " ").title()
        Label(frame, text=field_name + ":", font=("Arial", 10, "bold"), bg=bg).grid(row=0, column=2*idx, sticky=W, padx=5, pady=4)
        Entry(frame, textvariable=var, width=18, font=("Arial", 10)).grid(row=0, column=2*idx+1, padx=5, pady=4)

    Button(frame, text=f"Add {title}", bg="#4caf50", fg="white", font=("Arial", 10),
           command=lambda: add_entry(table, vars_, fields, vars_, trees[table], lambda: fetch_data(table, trees[table]))).grid(row=1, column=0, columnspan=2, pady=6)

    Button(frame, text=f"Delete {title}", bg="#f44336", fg="white", font=("Arial", 10),
           command=lambda: delete_entry(table, trees[table], lambda: fetch_data(table, trees[table]))).grid(row=1, column=2, columnspan=2, pady=6)

    cols = ["ID"] + [f.replace("_", " ").title() for f in fields]

    tree_frame = Frame(lf, bg=bg)
    tree_frame.pack(padx=10, pady=6, fill="both", expand=True)

    tree_scroll = Scrollbar(tree_frame, orient=VERTICAL)
    tree_scroll.pack(side=RIGHT, fill=Y)

    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=8, yscrollcommand=tree_scroll.set)
    tree_scroll.config(command=tree.yview)
    tree.pack(side=LEFT, fill="both", expand=True)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=120, anchor="center")

    trees[table] = tree

# === CREATE PAGES ===
def create_pages():
    page1 = Frame(root, bg="#e8f0fe")
    create_section(page1, "Doctor", "doctors", ["name", "specialty", "phone"], bg="#f1f8e9")
    create_section(page1, "Patient", "patients", ["name", "age", "illness"], bg="#ffe0b2")
    pages.append(page1)

    page2 = Frame(root, bg="#e8f0fe")
    create_section(page2, "Nurse", "nurses", ["name", "shift"], bg="#f8bbd0")
    create_section(page2, "Worker", "workers", ["name", "role"], bg="#d1c4e9")
    pages.append(page2)

    page3 = Frame(root, bg="#e8f0fe")
    create_section(page3, "OP", "op", ["patient_name", "date", "doctor"], bg="#c8e6c9")
    create_section(page3, "Billing", "billing", ["patient_name", "amount", "date"], bg="#b2ebf2")
    pages.append(page3)

create_pages()

# === PAGE NAVIGATION ===
current_page = 0
def show_page(index):
    global current_page
    if 0 <= index < len(pages):
        pages[current_page].pack_forget()
        current_page = index
        pages[current_page].pack(fill="both", expand=True)

btn_frame = Frame(root, bg="#e8f0fe")
btn_frame.pack(pady=10)

Button(btn_frame, text="← Previous", font=("Arial", 11), bg="#2196f3", fg="white",
       command=lambda: show_page(current_page - 1)).grid(row=0, column=0, padx=20)

Button(btn_frame, text="Next →", font=("Arial", 11), bg="#2196f3", fg="white",
       command=lambda: show_page(current_page + 1)).grid(row=0, column=1, padx=20)

# === INITIALIZE DATA ===
for table in ["doctors", "patients", "nurses", "workers", "op", "billing"]:
    fetch_data(table, trees[table])

export_to_excel()
show_page(0)

root.mainloop()
