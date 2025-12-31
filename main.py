import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv

# ========================= DATABASE SETUP =========================
conn = sqlite3.connect("students.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE,
        name TEXT,
        maths REAL,
        science REAL,
        english REAL,
        history REAL,
        computer REAL,
        total REAL,
        average REAL,
        grade TEXT,
        gpa REAL,
        remarks TEXT
    )
""")
conn.commit()

# ========================= FUNCTIONS =========================
def calculate_grade(average):
    if average >= 90:
        return 'A+', 4.0
    elif average >= 85:
        return 'A', 3.7
    elif average >= 80:
        return 'A-', 3.5
    elif average >= 75:
        return 'B+', 3.0
    elif average >= 70:
        return 'B', 2.7
    elif average >= 65:
        return 'C+', 2.3
    elif average >= 60:
        return 'C', 2.0
    elif average >= 50:
        return 'D', 1.0
    else:
        return 'F', 0.0

def get_remarks(grade):
    return "Passed" if grade != "F" else "Failed"

def add_student():
    try:
        student_id = entry_id.get().strip().upper()
        name = entry_name.get().strip()
        marks = [float(e.get()) for e in [entry_maths, entry_science, entry_english, entry_history, entry_computer]]

        if not student_id or not name:
            messagebox.showwarning("Input Error", "Please enter Student ID and Name.")
            return

        cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        if cursor.fetchone():
            messagebox.showerror("Duplicate ID", f"Student ID '{student_id}' already exists.")
            return

        total = sum(marks)
        average = total / 5
        grade, gpa = calculate_grade(average)
        remarks = get_remarks(grade)

        cursor.execute("""
            INSERT INTO students (student_id, name, maths, science, english, history, computer, total, average, grade, gpa, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, name, *marks, total, average, grade, gpa, remarks))
        conn.commit()

        clear_fields()
        fetch_data()
        update_statistics()

    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numeric marks for all subjects.")

def start_update(event):
    selected = tree.focus()
    if not selected:
        return
    values = tree.item(selected, "values")

    entry_id.delete(0, tk.END)
    entry_id.insert(0, values[1])
    entry_name.delete(0, tk.END)
    entry_name.insert(0, values[2])
    entry_maths.delete(0, tk.END)
    entry_maths.insert(0, values[3])
    entry_science.delete(0, tk.END)
    entry_science.insert(0, values[4])
    entry_english.delete(0, tk.END)
    entry_english.insert(0, values[5])
    entry_history.delete(0, tk.END)
    entry_history.insert(0, values[6])
    entry_computer.delete(0, tk.END)
    entry_computer.insert(0, values[7])

    entry_id.config(state='disabled')
    btn_add.config(state='disabled')
    btn_delete.config(state='disabled')
    btn_update.config(state='normal')
    tree.selection_set(selected)
    tree.focus(selected)

def update_student():
    student_id = entry_id.get().strip().upper()
    try:
        name = entry_name.get().strip()
        marks = [float(e.get()) for e in [entry_maths, entry_science, entry_english, entry_history, entry_computer]]
        if not name:
            messagebox.showwarning("Input Error", "Please enter student name.")
            return

        total = sum(marks)
        average = total / 5
        grade, gpa = calculate_grade(average)
        remarks = get_remarks(grade)

        cursor.execute("""
            UPDATE students
            SET name=?, maths=?, science=?, english=?, history=?, computer=?, total=?, average=?, grade=?, gpa=?, remarks=?
            WHERE student_id=?
        """, (name, *marks, total, average, grade, gpa, remarks, student_id))
        conn.commit()

        # Update table instantly without full refresh
        for item in tree.get_children():
            row = tree.item(item, "values")
            if row[1] == student_id:
                new_values = (row[0], student_id, name, *marks, total, average, grade, gpa, remarks)
                tree.item(item, values=new_values, tags=('pass' if remarks == "Passed" else 'fail'))
                break

        clear_fields()
        entry_id.config(state='normal')
        btn_add.config(state='normal')
        btn_delete.config(state='normal')
        btn_update.config(state='disabled')
        update_statistics()

    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter valid numeric marks for all subjects.")

def delete_student():
    selected = tree.focus()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a student to delete.")
        return
    values = tree.item(selected, "values")
    student_id = values[1]
    confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {values[2]}?")
    if confirm:
        cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        conn.commit()
        fetch_data()
        update_statistics()

def clear_fields():
    for entry in [entry_id, entry_name, entry_maths, entry_science, entry_english, entry_history, entry_computer]:
        entry.config(state='normal')
        entry.delete(0, tk.END)
    btn_add.config(state='normal')
    btn_delete.config(state='normal')
    btn_update.config(state='disabled')
    tree.selection_remove(tree.selection())  # remove row highlight

def fetch_data():
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM students")
    for row in cursor.fetchall():
        tag = "pass" if row[-1] == "Passed" else "fail"
        tree.insert("", tk.END, values=row, tags=(tag,))
    tree.tag_configure("pass", foreground="green")
    tree.tag_configure("fail", foreground="red")
    update_statistics()

def search_data(*args):
    query = search_var.get().lower()
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM students WHERE LOWER(name) LIKE ? OR LOWER(student_id) LIKE ?", 
                   ('%' + query + '%', '%' + query + '%'))
    results = cursor.fetchall()
    for row in results:
        tag = "pass" if row[-1] == "Passed" else "fail"
        tree.insert("", tk.END, values=row, tags=(tag,))
    tree.tag_configure("pass", foreground="green")
    tree.tag_configure("fail", foreground="red")
    update_statistics_live(results)

def sort_column(col):
    data = [(tree.set(k, col), k) for k in tree.get_children('')]
    try:
        data.sort(key=lambda t: float(t[0]), reverse=sort_order.get(col, False))
    except ValueError:
        data.sort(reverse=sort_order.get(col, False))
    for index, (val, k) in enumerate(data):
        tree.move(k, '', index)
    sort_order[col] = not sort_order.get(col, False)

def update_statistics():
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN remarks='Passed' THEN 1 ELSE 0 END), SUM(CASE WHEN remarks='Failed' THEN 1 ELSE 0 END), AVG(average) FROM students")
    total, passed, failed, avg = cursor.fetchone()
    total_label.config(text=f"Total Students: {total or 0}")
    passed_label.config(text=f"Passed: {passed or 0}")
    failed_label.config(text=f"Failed: {failed or 0}")
    avg_label.config(text=f"Overall Average: {avg:.2f}" if avg else "Overall Average: 0.00")

def update_statistics_live(data):
    total = len(data)
    passed = sum(1 for row in data if row[-1] == "Passed")
    failed = total - passed
    avg = sum(row[9] for row in data) / total if total > 0 else 0
    total_label.config(text=f"Total Students: {total}")
    passed_label.config(text=f"Passed: {passed}")
    failed_label.config(text=f"Failed: {failed}")
    avg_label.config(text=f"Overall Average: {avg:.2f}")

def export_csv():
    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    if not rows:
        messagebox.showwarning("No Data", "No student records to export.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
    if not file_path:
        return

    headers = ["ID", "Student ID", "Name", "Maths", "Science", "English", "History", "Computer", "Total", "Average", "Grade", "GPA", "Remarks"]
    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    messagebox.showinfo("Export Successful", f"Data exported successfully to:\n{file_path}")

# ========================= UI SETUP =========================
root = tk.Tk()
root.title("Student Grading System")
root.geometry("1200x650")
root.resizable(False, False)

left_frame = tk.Frame(root, padx=15, pady=10)
left_frame.pack(side=tk.LEFT, fill=tk.Y)
right_frame = tk.Frame(root, padx=10, pady=10)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

tk.Label(left_frame, text="Student Grading Form", font=("Helvetica", 16, "bold")).pack(pady=10)

fields = [("Student ID:", "entry_id"),
          ("Student Name:", "entry_name"),
          ("Maths:", "entry_maths"),
          ("Science:", "entry_science"),
          ("English:", "entry_english"),
          ("History:", "entry_history"),
          ("Computer:", "entry_computer")]

entries = {}
for label, var_name in fields:
    tk.Label(left_frame, text=label, font=("Helvetica", 11)).pack(anchor="w", pady=4)
    e = tk.Entry(left_frame, width=30)
    e.pack(pady=2)
    entries[var_name] = e

entry_id = entries["entry_id"]
entry_name = entries["entry_name"]
entry_maths = entries["entry_maths"]
entry_science = entries["entry_science"]
entry_english = entries["entry_english"]
entry_history = entries["entry_history"]
entry_computer = entries["entry_computer"]

btn_add = tk.Button(left_frame, text="Add Student", command=add_student, bg="#4CAF50", fg="white", width=20, font=("Helvetica", 10, "bold"))
btn_add.pack(pady=6)
btn_update = tk.Button(left_frame, text="Update Student", command=update_student, bg="#2196F3", fg="white", width=20, font=("Helvetica", 10, "bold"), state='disabled')
btn_update.pack(pady=6)
btn_delete = tk.Button(left_frame, text="Delete Student", command=delete_student, bg="#f44336", fg="white", width=20, font=("Helvetica", 10, "bold"))
btn_delete.pack(pady=6)
tk.Button(left_frame, text="Clear", command=clear_fields, bg="#9E9E9E", fg="white", width=20, font=("Helvetica", 10, "bold")).pack(pady=6)
tk.Button(left_frame, text="Export to CSV", command=export_csv, bg="#FF9800", fg="white", width=20, font=("Helvetica", 10, "bold")).pack(pady=6)

tk.Label(right_frame, text="Student Records", font=("Helvetica", 16, "bold")).pack(pady=5)

search_frame = tk.Frame(right_frame)
search_frame.pack(fill=tk.X, pady=5)
tk.Label(search_frame, text="Search: ", font=("Helvetica", 11)).pack(side=tk.LEFT)
search_var = tk.StringVar()
search_var.trace("w", search_data)
tk.Entry(search_frame, textvariable=search_var, width=30).pack(side=tk.LEFT, padx=5)

columns = ("ID", "Student ID", "Name", "Maths", "Science", "English", "History", "Computer", "Total", "Average", "Grade", "GPA", "Remarks")
tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)
sort_order = {}

for col in columns:
    tree.heading(col, text=col, command=lambda c=col: sort_column(c))
    if col == "ID":
        tree.column(col, width=0, stretch=False)  # hide internal DB ID
    else:
        tree.column(col, width=85 if col not in ["Name", "Student ID"] else 120, anchor="center")

tree.pack(fill=tk.BOTH, expand=True)
tree.bind("<Double-1>", start_update)

scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

stats_frame = tk.Frame(right_frame, pady=10)
stats_frame.pack(fill=tk.X)
total_label = tk.Label(stats_frame, text="Total Students: 0", font=("Helvetica", 11, "bold"))
total_label.pack(side=tk.LEFT, padx=10)
passed_label = tk.Label(stats_frame, text="Passed: 0", font=("Helvetica", 11, "bold"), fg="green")
passed_label.pack(side=tk.LEFT, padx=20)
failed_label = tk.Label(stats_frame, text="Failed: 0", font=("Helvetica", 11, "bold"), fg="red")
failed_label.pack(side=tk.LEFT, padx=20)
avg_label = tk.Label(stats_frame, text="Overall Average: 0.00", font=("Helvetica", 11, "bold"))
avg_label.pack(side=tk.LEFT, padx=20)

fetch_data()
update_statistics()
root.mainloop()
