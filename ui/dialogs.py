import tkinter as tk
from collections import defaultdict
from collections import Counter
from tkinter import ttk

# ---------- Input Dialog, returns Input ----------
class InputDialog(tk.Toplevel):
    def __init__(self, parent, title, label_text):
        super().__init__(parent)
        self.result = None

        self.title(title)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=label_text).pack(padx=10, pady=5)
        self.entry = tk.Entry(self)
        self.entry.pack(padx=10, pady=5)
        self.entry.focus()

        tk.Button(self, text="OK", command=self.confirm).pack(pady=10)       
        self.bind("<Return>", self.confirm)
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
    def confirm(self, event=None):
        key = self.entry.get().strip()
        if key:
            self.result = key
        self.destroy()

# ---------- Shows associated tags, returns selected tags ----------
class AssociatedTagDialog(tk.Toplevel):
    def __init__(self, parent, tag_key, file_tree_root, mode=False):
        """
        mode=False: browse
        mode=True: select
        """
        super().__init__(parent)
        self.result = None
        self.mode = mode
        self.listbox = None
        self.title(f"Associated Tags @'{tag_key}'")
        self.transient(parent)
        self.grab_set()
        self.geometry("400x300")

        #Count associated tags
        assoc_counts = Counter()
        for elem in file_tree_root.xpath(".//node | .//way | .//relation"):
            tags = [t.get("k") for t in elem.findall("tag")]
            if tag_key not in tags:
                continue

            for k in tags:
                if k != tag_key:
                    assoc_counts[k] += 1

        #Frame & Listbox
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        listbox_type = "none"
        if self.mode is True:
            listbox_type = "multiple"
        self.listbox = tk.Listbox(frame, selectmode=listbox_type)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        #Sort tags based on count
        for tag, count in assoc_counts.most_common():
            self.listbox.insert("end", f"{tag} ({count})")
        
        tk.Button(self, text="OK", command=self.confirm).pack(pady=5)
        
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def confirm(self, event=None):
        if self.mode:
            selected_indices = self.listbox.curselection()
            selected_values = [self.listbox.get(i) for i in selected_indices]
            if selected_values:
                selected_values = [value.split(" ")[0] for value in selected_values]
                self.result = selected_values
        self.destroy()

# ---------- Show elements with tag ----------
class TagElementDialog(tk.Toplevel):
    def __init__(self, parent, tag_key, file_tree_root):
        super().__init__(parent)
        self.tag_key = tag_key
        self.title(f"Elements mit Tag '{self.tag_key}'")
        self.transient(parent)
        self.grab_set()
        self.geometry("700x500")

        #Frame & Treeview
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(frame)
        tree.pack(side="left", fill="both", expand=True)
        tree.heading("#0", text="OSM-Struktur")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

        #Search through all elements, add elements with tag to treeview
        sections = {"Nodes": ".//node", "Ways": ".//way", "Relations": ".//relation"}
        for section_name, xpath in sections.items():
            section_item = None
            for elem in file_tree_root.findall(xpath):
                if not any(t.get("k") == self.tag_key for t in elem.findall("tag")):
                    continue

                if section_item is None:
                    section_item = tree.insert("", "end", text=section_name, open=True)

                elem_id = elem.get("id")
                elem_item = tree.insert(section_item, "end", text=f"{section_name[:-1]} {elem_id}", open=False)

                for tag in elem.findall("tag"):
                    k = tag.get("k")
                    v = tag.get("v")
                    tree.insert(elem_item, "end", text=f"{k} = {v}")

        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

# ---------- Shows tag values for tag, returns selected values ----------
class TagValueDialog(tk.Toplevel):
    def __init__(self, parent, tag_key, tree, mode=None, tag_values=""):
        """
        mode=None: browse
        mode=False: browse and select
        mode=True: select and edit
        """
        super().__init__(parent)
        self.result = None
        self.listbox = None
        self.mode = mode
        self.tag_key = tag_key
        self.tree = tree
        self.tag_values = ""
        if tag_values:
            self.tag_values = sorted(v.strip() for v in tag_values[0].split(",") if v.strip())

        self.title(f"Values für '{tag_key}'")
        self.transient(parent)
        self.grab_set()
        self.geometry("400x300")

        #Count values for selected tags
        if self.mode is None or self.mode is False:
            if self.tree is not None:
                values = [tag.get("v") for tag in self.tree.findall(".//tag") if tag.get("k") == tag_key]
                value_counts = Counter(values)

        #Frame, listbox & scrollbar
        frame_list = tk.Frame(self)
        frame_list.pack(fill="both", expand=True, padx=10, pady=10)

        listbox_type = "none"
        if self.mode is not None:
            listbox_type = "multiple"
        self.listbox = tk.Listbox(frame_list, selectmode=listbox_type)
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        #Add values to listbox
        if self.mode is True:
            for value in self.tag_values:
                value = value.strip()
                self.listbox.insert("end", f"{value}")
        else:
            for value, count in value_counts.most_common():
                self.listbox.insert("end", f"{value} ({count})")
        
        #Buttons
        frame_buttons = tk.Frame(self)
        frame_buttons.pack(pady=5)

        if self.mode:
            tk.Button(frame_buttons, text="Browse Values", command=self.browse).pack(side="left", padx=5)  
            tk.Button(frame_buttons, text="New Value", command=self.new).pack(side="left", padx=5)
            tk.Button(frame_buttons, text="Delete Value", command=self.delete).pack(side="left", padx=5)
        tk.Button(frame_buttons, text="OK", command=self.confirm).pack(side="left", padx=5)     

        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def browse(self, event=None):
        dialog = TagValueDialog(self, self.tag_key, self.tree, mode=False)
        self.wait_window(dialog)
        if dialog.result:
            for value in dialog.result:
                self.listbox.insert("end", f"{value}")
            items = list(self.listbox.get(0, "end"))
            items.sort()
            self.listbox.delete(0, "end")
            for item in items:
                self.listbox.insert("end", item)

    def new(self, event=None):
        dialog = InputDialog(self, "New Value", "New Value:")
        self.wait_window(dialog)
        if dialog.result:
            self.listbox.insert("end", dialog.result)

    def delete(self, event=None):
        selected_indices = self.listbox.curselection()
        for i in reversed(selected_indices):
            self.listbox.delete(i)

    def confirm(self, event=None):
        if self.mode is False:
            selected_indices = self.listbox.curselection()
            selected_values = [self.listbox.get(i) for i in selected_indices]
            if selected_values:
                selected_values = [value.split(" ")[0] for value in selected_values]
                self.result = selected_values
        if self.mode is True:
            values = self.listbox.get(0, "end")
            if values:
                self.result = str(", ".join(values))
        self.destroy()

