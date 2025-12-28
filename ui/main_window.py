import tkinter as tk
import json
from tkinter import ttk, filedialog, font
from ui.dragdrop import TreeDragDrop
from ui.dialogs import (
    TagValueDialog,
    AssociatedTagDialog,
    TagElementDialog,
    InputDialog
)
from utils import tree_helpers

class MainWindow(tk.Tk):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.title("OSM Tag Processor")
        self.minsize(1200, 600)
        self.resizable(True, True)

        self._init_state
        self._build_ui()

    def _init_state(self):
        self.selected_tag_key = None
        self.item_clipboard = None

    def _build_ui(self):
        # ---------- Menu ----------
        menubar = tk.Menu(self)
        menubar.add_command(label="Open File", command=self.load_osm_file)
        self.config(menu=menubar)

        # ---------- Labels ----------
        frame_labels = tk.Frame(self)
        frame_labels.pack(pady=5)

        self.lb_rel = tk.Label(frame_labels, text="Relations: 0")
        self.lb_rel.pack(side="left", padx=10)
        self.lb_way = tk.Label(frame_labels, text="Ways: 0")
        self.lb_way.pack(side="left", padx=10)
        self.lb_node = tk.Label(frame_labels, text="Nodes: 0")
        self.lb_node.pack(side="left", padx=10)

        # ---------- Mainframe ----------
        frame_main = tk.Frame(self)
        frame_main.pack(fill="both", expand=True, padx=10, pady=10)

        # ---------- Left Treeview (Loaded OSM) ----------
        self.tree_left = ttk.Treeview(frame_main, columns=("count",))
        self.tree_left.heading("#0", text="Tag")
        self.tree_left.column("#0", width=80, anchor="center")
        self.tree_left.heading("count", text="Anzahl")
        self.tree_left.column("count", width=20, anchor="center")
        self.tree_left.pack(side="left", fill="both", expand=True)
        self.tree_left.bind("<Double-1>", lambda event: self.on_tag_double_click(self.tree_left, None, event))
        self.tree_left.bind("<Button-3>", lambda event: self.on_tag_right_click(self.tree_left, False, event))

        # ---------- Right Frame ----------
        frame_right = tk.Frame(frame_main)
        frame_right.pack(side="left", fill="both", expand=True, padx=(5, 0))

        # ---------- Right Treeview (Filter) ----------
        self.tree_right = ttk.Treeview(frame_right, columns=("values",))
        self.tree_right.heading("#0", text="Category / Tags")
        self.tree_right.column("#0", width=80, anchor="center")
        self.tree_right.heading("values", text="Values")
        self.tree_right.column("values", width=80, anchor="center")
        self.tree_right.pack(fill="both", expand=True)
        self.tree_right.tag_configure("drop_target", background="#d0ebff")
        self.tree_right.bind("<Double-1>", lambda event: self.on_tag_double_click(self.tree_right, True, event))
        self.tree_right.bind("<Button-3>", lambda event: self.on_tag_right_click(self.tree_right, True, event))
        self.tree_right.bind("<Delete>", lambda event: self.on_element_delete(self.tree_right, event))

        # ---------- Category Style ----------
        base_font = font.nametofont("TkDefaultFont")  
        bold_font = base_font.copy()
        bold_font.configure(weight="bold")
        self.tree_right.tag_configure("bold", font=bold_font, foreground="#3333aa")

        # ---------- Button Frame and Buttons ----------
        frame_buttons = tk.Frame(frame_right)
        frame_buttons.pack(padx=5)
        tk.Button(frame_buttons, text="New Categorie", command=self.add_category).pack(side="left", fill="x", pady=2)
        tk.Button(frame_buttons, text="New Tag", command=self.add_tag).pack(side="left", fill="x", pady=2)
        tk.Button(frame_buttons, text="Remove Element", command=lambda: self.on_element_delete(self.tree_right)).pack(side="left", fill="x", pady=2)
        tk.Button(frame_buttons, text="Edit Tag Values", command=lambda: self.on_tag_double_click(self.tree_right, True)).pack(side="left", fill="x", pady=2)
        tk.Button(frame_buttons, text="Load Filter", command=self.load_filter).pack(side="left", fill="x", pady=2)
        tk.Button(frame_buttons, text="Save Filter", command=self.save_filter).pack(side="left", fill="x", pady=2)
        tk.Button(frame_buttons, text="Apply Filter", command=self.apply_filter).pack(side="left", fill="x", pady=2)

        # ---------- Drag & Drop ----------
        self.dragdrop = TreeDragDrop(self.tree_left, self.tree_right)

    # ---------- Update UI ----------
    def update_counts(self, counts):
        self.lb_node.config(text=f"Nodes: {counts['nodes']}")
        self.lb_way.config(text=f"Ways: {counts['ways']}")
        self.lb_rel.config(text=f"Relations: {counts['relations']}")

    def show_tags(self, tag_counts):
        from collections import defaultdict
        # links gruppieren nach Prefix
        for item in self.tree_left.get_children():
            self.tree_left.delete(item)

        prefix_groups = defaultdict(list)
        for k, count in tag_counts.items():
            if ":" in k:
                prefix, rest = k.split(":", 1)
                prefix_groups[prefix].append((k, count))
            else:
                prefix_groups[k].append((k, count))

        for prefix, tags in sorted(prefix_groups.items()):
            if len(tags) == 1 and tags[0][0] == prefix:
                self.tree_left.insert("", "end", text=prefix, values=(tags[0][1],))
            else:
                parent = self.tree_left.insert("", "end", text=prefix, values=("",))
                for full_tag, count in sorted(tags):
                    self.tree_left.insert(parent, "end", text=full_tag, values=(count,))

    # ---------- Events ----------
    def on_tag_double_click(self, tree, mode, event=None):
        item = tree.selection()
        if not item:
            return
        tag_key = tree.item(item[0], "text")
        self.selected_tag_key = tag_key
        if not "category" in tree.item(item, "tags"):
            if mode:
                dialog = TagValueDialog(self, tag_key, self.app.osm.root, mode, tree.item(item, "values"))
                self.wait_window(dialog)
                if dialog.result:
                    self.tree_right.item(item, values=(dialog.result,))
            else:
                TagValueDialog(self, tag_key, self.app.osm.root, mode)

    def on_tag_right_click(self, tree, mode, event):
        item = tree.identify_row(event.y)
        menu = tk.Menu(self, tearoff=0)
        if not item:
            if mode:
                menu.add_command(label="Add category", command=self.add_category)
                menu.add_command(label="Add tag", command=self.add_tag)
        else:
            tree.selection_set(item)
            self.selected_tag_key = tree.item(item, "text")
            if "tag" in tree.item(item, "tags") or not mode:
                menu.add_command(label="Browse elements", command=lambda: TagElementDialog(self, self.selected_tag_key, self.app.osm.root))
                menu.add_command(label="Show associated elements", command=lambda: self.on_show_assoc_tag(mode))
            menu.add_command(label="Copy Element", command=lambda: self.on_tag_copy(item))
            if mode:
                menu.add_command(label="Add category", command=self.add_category)
                menu.add_command(label="Add tag", command=self.add_tag)
                menu.add_command(label="Remove element", command=lambda: self.on_element_delete(tree, event))
                if self.item_clipboard:
                    menu.add_command(label="Paste element", command=lambda: self.on_tag_paste(event))
        menu.tk_popup(event.x_root, event.y_root)

    def on_element_delete(self, tree, event=None):
        for item in tree.selection():
            tree.delete(item)
 
    def on_tag_copy(self, selected_item):
        self.item_clipboard = selected_item
    
    def on_tag_paste(self, event=None):
        if self.item_clipboard:
            parent = self.tree_right.selection()
            print(parent)
            if not parent:
                return
            tree_helpers.copy_item(self.tree_left, self.tree_right, self.item_clipboard, parent)

    def on_show_assoc_tag(self, mode):
        dialog = AssociatedTagDialog(self, self.selected_tag_key, self.app.osm.root, mode)
        self.wait_window(dialog)
        if dialog.result and mode:
            parent = self.tree_right.selection()
            for child in dialog.result:
                self.tree_right.insert(parent, "end", text=child, tags=("tag",))

    # ---------- Load osm file from path into treeview ----------
    def load_osm_file(self):
        path = filedialog.askopenfilename(
            title="Select File...",
            filetypes=[("OSM-File", "*.osm*")]
        )
        if path:
            self.app.load_osm_file(path)

     # ---------- Add tag to category/tag on filter tree ----------   
    def add_tag(self):
        sel = self.tree_right.selection()
        if not sel:
            return
        parent = sel[0]
        dialog = InputDialog(self, "New Tag-Key", "Tag-Key:")
        self.wait_window(dialog)
        if dialog.result:
            self.tree_right.insert(parent, "end", text=dialog.result, tags=("tag",))

    # ---------- Add catetgory on filter tree ----------
    def add_category(self):
        dialog = InputDialog(self, "New Category", "Category name:")
        self.wait_window(dialog)
        if dialog.result:
            self.tree_right.insert("", "end", text=dialog.result, tags=("category","bold"))

    # ---------- Load filter from JSON ----------
    def load_filter(self):
        path = filedialog.askopenfilename(
            title="Load File...",
            filetypes=[("JSON-File", "*.json*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tree_right.delete(*self.tree_right.get_children())
            tree_helpers.dict_to_tree(self.tree_right, data)

    # ---------- Save filter to JSON ----------
    def save_filter(self):
        path = filedialog.asksaveasfilename(
            title="Save File...",
            defaultextension=".json",
            filetypes=[("JSON-File", "*.json*")]
        )
        if path:
            data = tree_helpers.tree_to_dict(self.tree_right)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # ---------- Apply filter on OSM file ----------
    def apply_filter(self):
        path = filedialog.asksaveasfilename(
            title="Save File...",
            defaultextension=".osm",
            filetypes=[("OSM-File", "*.osm*")]
        )
        if path:
            rules = tree_helpers.tree_to_rules(self.tree_right)
            self.app.process_file(rules, path)
