"""
Student Record Management System
Python + Tkinter GUI (enhanced)
- Linked List (custom) for storing student records
- Hash Map (dict) for quick lookup by roll number (normalized)
- Quick Sort for sorting (kept)
- Persistent storage using JSON file (atomic save)
- GUI: Add, Update (including roll change), Delete, Search, Sort, View All, Export CSV.
- Table with scrollbar. Double-click to edit row.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import tempfile
import csv

JSON_FILE = os.path.join(os.path.dirname(__file__), "students.json")


# -------------------------
# Data model / DSA classes
# -------------------------

class Student:
    """Simple Student data container."""
    def __init__(self, roll: str, name: str, gpa: float):
        self.roll = str(roll)
        self.name = str(name)
        self.gpa = float(gpa)

    def to_dict(self):
        return {"roll": self.roll, "name": self.name, "gpa": self.gpa}

    @staticmethod
    def from_dict(d):
        return Student(d["roll"], d["name"], d["gpa"])


class Node:
    """Node for singly linked list."""
    def __init__(self, student: Student):
        self.student = student
        self.next = None


class LinkedList:
    """Singly linked list implementation that stores Student nodes."""
    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, student: Student):
        node = Node(student)
        if not self.head:
            self.head = node
        else:
            cur = self.head
            while cur.next:
                cur = cur.next
            cur.next = node
        self.size += 1
        return node

    def to_list(self):
        """Return Python list of Student objects (order of linked list)."""
        arr = []
        cur = self.head
        while cur:
            arr.append(cur.student)
            cur = cur.next
        return arr

    def rebuild_from_list(self, students_list):
        """Clear and rebuild linked list from a list of Student objects."""
        self.head = None
        self.size = 0
        for s in students_list:
            self.append(s)

    def remove_by_roll(self, roll):
        """Remove node with matching roll. Return True if removed."""
        prev = None
        cur = self.head
        while cur:
            if cur.student.roll == roll:
                if prev is None:
                    # remove head
                    self.head = cur.next
                else:
                    prev.next = cur.next
                self.size -= 1
                return True
            prev = cur
            cur = cur.next
        return False

    def find_node_by_roll(self, roll):
        cur = self.head
        while cur:
            if cur.student.roll == roll:
                return cur
            cur = cur.next
        return None


# -------------------------
# Sorting: Quick Sort
# -------------------------

def quicksort_students(arr, key):
    """In-place quicksort on list of Student objects.
       key is a callable that maps Student -> comparable value.
    """
    def _quicksort(a, lo, hi):
        if lo >= hi:
            return
        pivot = key(a[(lo + hi) // 2])
        i, j = lo, hi
        while i <= j:
            while key(a[i]) < pivot:
                i += 1
            while key(a[j]) > pivot:
                j -= 1
            if i <= j:
                a[i], a[j] = a[j], a[i]
                i += 1
                j -= 1
        if lo < j:
            _quicksort(a, lo, j)
        if i < hi:
            _quicksort(a, i, hi)

    if len(arr) <= 1:
        return arr
    _quicksort(arr, 0, len(arr) - 1)
    return arr


# -------------------------
# Persistence (JSON) - atomic save
# -------------------------

def load_students_from_file():
    if not os.path.exists(JSON_FILE):
        return []
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        students = [Student.from_dict(d) for d in data]
        return students
    except Exception as e:
        # If GUI isn't ready yet, printing/exception is safe; still show a messagebox if possible
        try:
            messagebox.showerror("Load Error", f"Failed to load {JSON_FILE}: {e}")
        except Exception:
            print(f"Load Error: Failed to load {JSON_FILE}: {e}")
        return []


def save_students_to_file(students_list):
    # atomic write via tempfile + rename
    try:
        dirpath = os.path.dirname(JSON_FILE) or "."
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=dirpath) as tf:
            json.dump([s.to_dict() for s in students_list], tf, indent=2)
            tempname = tf.name
        os.replace(tempname, JSON_FILE)
    except Exception as e:
        try:
            messagebox.showerror("Save Error", f"Failed to save {JSON_FILE}: {e}")
        except Exception:
            print(f"Save Error: Failed to save {JSON_FILE}: {e}")


# -------------------------
# GUI Application
# -------------------------

def normalize_roll(roll: str) -> str:
    """Normalize roll for consistent keys (strip and upper)."""
    return roll.strip().upper()


class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Record Management System")
        self.root.geometry("760x540")
        self.root.resizable(False, False)

        # DSA containers
        self.linked_list = LinkedList()
        self.hash_map = {}  # roll -> Node

        # Load data from file
        self.load_data()

        # GUI widgets
        self.create_widgets()
        self.refresh_table()

    def load_data(self):
        students = load_students_from_file()
        self.linked_list.rebuild_from_list(students)
        self.rebuild_hash_map()

    def rebuild_hash_map(self):
        self.hash_map = {}
        cur = self.linked_list.head
        while cur:
            key = normalize_roll(cur.student.roll)
            self.hash_map[key] = cur
            cur = cur.next

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Top input form
        form = ttk.LabelFrame(frame, text="Student Details", padding=10)
        form.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(form, text="Roll No:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        self.roll_entry = ttk.Entry(form, width=20)
        self.roll_entry.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(form, text="Name:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=3)
        self.name_entry = ttk.Entry(form, width=30)
        self.name_entry.grid(row=0, column=3, padx=5, pady=3)

        ttk.Label(form, text="GPA:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=3)
        self.gpa_entry = ttk.Entry(form, width=10)
        self.gpa_entry.grid(row=0, column=5, padx=5, pady=3)

        # Buttons: Add, Update, Delete, Search, Clear
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=1, column=0, columnspan=6, pady=8)

        add_btn = ttk.Button(btn_frame, text="Add Student", command=self.add_student)
        add_btn.grid(row=0, column=0, padx=4)
        update_btn = ttk.Button(btn_frame, text="Update Student", command=self.update_student)
        update_btn.grid(row=0, column=1, padx=4)
        delete_btn = ttk.Button(btn_frame, text="Delete Student", command=self.delete_student)
        delete_btn.grid(row=0, column=2, padx=4)
        search_btn = ttk.Button(btn_frame, text="Search by Roll", command=self.search_student)
        search_btn.grid(row=0, column=3, padx=4)
        clear_btn = ttk.Button(btn_frame, text="Clear Fields", command=self.clear_inputs)
        clear_btn.grid(row=0, column=4, padx=4)
        
        

        # Sorting options
        sort_frame = ttk.LabelFrame(frame, text="Sort & View", padding=10)
        sort_frame.pack(fill=tk.X, padx=5, pady=5)

        self.sort_var = tk.StringVar(value="roll")
        ttk.Radiobutton(sort_frame, text="By Roll", variable=self.sort_var, value="roll").grid(row=0, column=0, padx=6)
        ttk.Radiobutton(sort_frame, text="By Name", variable=self.sort_var, value="name").grid(row=0, column=1, padx=6)
        ttk.Radiobutton(sort_frame, text="By GPA", variable=self.sort_var, value="gpa").grid(row=0, column=2, padx=6)

        sort_btn = ttk.Button(sort_frame, text="Sort", command=self.sort_and_refresh)
        sort_btn.grid(row=0, column=3, padx=8)

        view_all_btn = ttk.Button(sort_frame, text="View All", command=self.refresh_table)
        view_all_btn.grid(row=0, column=4, padx=8)

        # Table area
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("roll", "name", "gpa")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=16)
        self.tree.heading("roll", text="Roll No")
        self.tree.column("roll", width=110, anchor=tk.CENTER)
        self.tree.heading("name", text="Name")
        self.tree.column("name", width=420, anchor=tk.W)
        self.tree.heading("gpa", text="GPA")
        self.tree.column("gpa", width=100, anchor=tk.CENTER)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind selection to populate fields and double-click to edit
        self.tree.bind("<<TreeviewSelect>>", self.on_row_selected)
        self.tree.bind("<Double-1>", self.on_row_double_click)

    # -------------------------
    # GUI Action Handlers
    # -------------------------
    def validate_inputs(self, require_roll=True):
        roll_raw = self.roll_entry.get()
        name = self.name_entry.get().strip()
        gpa_str = self.gpa_entry.get().strip()

        roll = normalize_roll(roll_raw) if roll_raw is not None else ""
        if require_roll and not roll:
            messagebox.showwarning("Validation", "Please provide Roll number.")
            return None

        if not name:
            messagebox.showwarning("Validation", "Please provide Name.")
            return None

        if not gpa_str:
            messagebox.showwarning("Validation", "Please provide GPA.")
            return None

        try:
            gpa = float(gpa_str)
            if gpa < 0 or gpa > 4.0:
                messagebox.showwarning("Validation", "GPA should be between 0 and 4.0.")
                return None
        except ValueError:
            messagebox.showwarning("Validation", "GPA should be a number (e.g., 3.2).")
            return None

        return roll, name, gpa

    def add_student(self):
        validated = self.validate_inputs(require_roll=True)
        if not validated:
            return
        roll, name, gpa = validated
        if roll in self.hash_map:
            messagebox.showerror("Duplicate", f"A student with roll '{roll}' already exists.")
            return
        student = Student(roll, name, gpa)
        node = self.linked_list.append(student)
        self.hash_map[roll] = node
        self.persist_and_refresh()
        messagebox.showinfo("Success", f"Student {name} ({roll}) added.")
        self.clear_inputs()

    def update_student(self):
        # Support changing roll: compare original selection vs entered roll
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "Select a student row to update (or search first).")
            return

        # get original roll from selected row
        original_vals = self.tree.item(sel[0], "values")
        if not original_vals:
            messagebox.showerror("Error", "Could not read selected row.")
            return
        original_roll = normalize_roll(original_vals[0])

        validated = self.validate_inputs(require_roll=True)
        if not validated:
            return
        new_roll, name, gpa = validated

        # if roll changed and collides, block
        if new_roll != original_roll and new_roll in self.hash_map:
            messagebox.showerror("Duplicate", f"Cannot change roll to '{new_roll}': another student has this roll.")
            return

        # find node by original roll
        node = self.hash_map.get(original_roll)
        if not node:
            messagebox.showerror("Not Found", f"No student found with roll '{original_roll}'.")
            return

        # update (possibly change roll)
        node.student.name = name
        node.student.gpa = gpa
        node.student.roll = new_roll  # update value

        # if roll changed, update hash_map key
        if new_roll != original_roll:
            self.hash_map.pop(original_roll, None)
            self.hash_map[new_roll] = node

        self.persist_and_refresh()
        messagebox.showinfo("Updated", f"Student {new_roll} updated.")
        self.clear_inputs()

    def delete_student(self):
        roll_raw = self.roll_entry.get().strip()
        if not roll_raw:
            messagebox.showwarning("Validation", "Please enter Roll number to delete (or select a row).")
            return
        roll = normalize_roll(roll_raw)
        if roll not in self.hash_map:
            messagebox.showerror("Not Found", f"No student found with roll '{roll}'.")
            return
        result = messagebox.askyesno("Confirm Delete", f"Delete student with roll '{roll}'?")
        if not result:
            return
        removed = self.linked_list.remove_by_roll(self.hash_map[roll].student.roll)
        self.hash_map.pop(roll, None)
        if removed:
            self.persist_and_refresh()
            messagebox.showinfo("Deleted", f"Student {roll} deleted.")
            self.clear_inputs()
        else:
            messagebox.showerror("Error", "Failed to remove student from list (internal error).")

    def search_student(self):
        roll_raw = self.roll_entry.get().strip()
        if not roll_raw:
            messagebox.showwarning("Validation", "Please enter Roll number to search.")
            return
        roll = normalize_roll(roll_raw)
        node = self.hash_map.get(roll)
        if not node:
            messagebox.showinfo("Search Result", f"No student found with roll '{roll}'.")
            return
        s = node.student
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, s.name)
        self.gpa_entry.delete(0, tk.END)
        self.gpa_entry.insert(0, str(s.gpa))
        # highlight in table
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            if normalize_roll(str(vals[0])) == roll:
                self.tree.selection_set(iid)
                self.tree.see(iid)
                break

    def clear_inputs(self):
        self.roll_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.gpa_entry.delete(0, tk.END)
        try:
            self.tree.selection_remove(self.tree.selection())
        except Exception:
            pass

    def on_row_selected(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if vals:
            self.roll_entry.delete(0, tk.END)
            self.roll_entry.insert(0, vals[0])
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, vals[1])
            self.gpa_entry.delete(0, tk.END)
            self.gpa_entry.insert(0, vals[2])

    def on_row_double_click(self, event):
        # same as selection behavior but ensure user can edit
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.on_row_selected(None)

    def refresh_table(self, students_list=None):
        """Reload table. If students_list is provided (list of Student), use it; else from linked list."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        if students_list is None:
            students_list = self.linked_list.to_list()
        for s in students_list:
            self.tree.insert("", tk.END, values=(s.roll, s.name, "{:.2f}".format(s.gpa)))

    def persist_and_refresh(self):
        students_list = self.linked_list.to_list()
        save_students_to_file(students_list)
        # rebuild hash_map (in case of structural changes)
        self.rebuild_hash_map()
        self.refresh_table()

    def sort_and_refresh(self):
        key_name = self.sort_var.get()
        students = self.linked_list.to_list()

        if key_name == "roll":
            key_fn = lambda s: (normalize_roll(s.roll))
        elif key_name == "name":
            key_fn = lambda s: (s.name.lower())
        elif key_name == "gpa":
            key_fn = lambda s: (s.gpa)
        else:
            key_fn = lambda s: normalize_roll(s.roll)

        quicksort_students(students, key_fn)
        if key_name == "gpa":
            students.reverse()  # show highest GPA first

        # Rebuild linked list to reflect sorted order
        self.linked_list.rebuild_from_list(students)
        # rebuild hashmap
        self.rebuild_hash_map()
        # Persist sorted order
        save_students_to_file(self.linked_list.to_list())
        self.refresh_table()

    def export_csv(self):
        # ask user where to save
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            students = self.linked_list.to_list()
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Roll", "Name", "GPA"])
                for s in students:
                    writer.writerow([s.roll, s.name, "{:.2f}".format(s.gpa)])
            messagebox.showinfo("Exported", f"Exported {len(students)} students to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV: {e}")


# -------------------------
# Run the application
# -------------------------

def main():
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
