from tkinter import ttk

def clear_tree(tree: ttk.Treeview):
    """Löscht alle Items aus einem Treeview"""
    tree.delete(*tree.get_children())

def insert_tree_item(tree: ttk.Treeview, parent, text, values=None, open=False):
    """Fügt ein Item in einen Treeview ein"""
    values = values or ()
    return tree.insert(parent, "end", text=text, values=values, open=open)

def copy_item(source: ttk.Treeview, target: ttk.Treeview, item, parent=""):
    """
    Verschiebt ein Item samt allen Unterelementen von source zu target.
    Liefert das neue Ziel-Item zurück.
    """
    text = source.item(item, "text")
    #values = source.item(item, "values")
    new_item = target.insert(parent, "end", text=text, tags=("tag",))#, values=values)

    for child in source.get_children(item):
        copy_item(source, target, child, parent=new_item)
    return new_item

def get_selected_text(tree: ttk.Treeview):
    """
    Gibt die Texte der aktuell selektierten Items als Liste zurück
    """
    return [tree.item(i, "text") for i in tree.selection()]

def expand_all(tree: ttk.Treeview, item=""):
    """Alle Unterelemente eines Treeview-Items aufklappen"""
    children = tree.get_children(item)
    for c in children:
        tree.item(c, open=True)
        expand_all(tree, c)

def delete_item(tree: ttk.Treeview, item):
    """Löscht Item aus einem Treeview"""
    tree.delete(item)

def tree_to_dict(tree, item=""):
    result = []
    for child in tree.get_children(item):
        node = {
            "text": tree.item(child, "text"),
            "values": tree.item(child, "values"),
            "tags": list(tree.item(child, "tags")),
            "children": tree_to_dict(tree, child)
        }
        result.append(node)
    return result

def dict_to_tree(tree, data, parent=""):
    for node in data:
        item = tree.insert(
            parent,
            "end",
            text=node["text"],
            values=node.get("values", ()),
            tags=node.get("tags", ())
        )
        dict_to_tree(tree, node.get("children", []), item)

def tree_to_whitelist(tree):
    keep_tags = {}

    # Categories
    for category_item in tree.get_children(""):
        # Tags per Category
        for tag_item in tree.get_children(category_item):

            tag_key = tree.item(tag_item, "text").strip()
            if not tag_key:
                continue

            raw_values = tree.item(tag_item, "values")
            raw = raw_values[0] if raw_values else ""

            if raw:
                values = {
                    v.strip()
                    for v in raw.split(",")
                    if v.strip()
                }
                keep_tags[tag_key] = values if values else None
            else:
                keep_tags[tag_key] = None

            # children von tag_item not evaluatee
    print(keep_tags)
    return keep_tags

def tree_to_rules(tree):
    rules = []

    def parse_item(item):
        key = tree.item(item, "text").strip()
        if not key:
            return

        raw_values = tree.item(item, "values")
        raw = raw_values[0] if raw_values else ""
        values = {v.strip() for v in raw.split(",") if v.strip()} or None

        child_rules = None

        #recurse
        if tree.get_children(item):
            child_rules = []
            for child in tree.get_children(item):
                child_rule= parse_item(child)
                child_rules.append(child_rule)

        return [key, values, child_rules]

    for category in tree.get_children(""):
        key = tree.item(category, "text").strip()
        rule = []
        for tag in tree.get_children(category):
            rule.append(parse_item(tag))
        rules.append([key ,rule])

    return rules