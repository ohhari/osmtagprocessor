from tkinter import ttk

def copy_item(source: ttk.Treeview, target: ttk.Treeview, item, parent=""):
    """
    Copies item from source to target with all child items
    Returns new item
    """
    text = source.item(item, "text")
    #values = source.item(item, "values")
    new_item = target.insert(parent, "end", text=text, tags=("tag",))

    for child in source.get_children(item):
        copy_item(source, target, child, parent=new_item)
    return new_item

def tree_to_dict(tree: ttk.Treeview, item=""):
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

def dict_to_tree(tree: ttk.Treeview, data, parent=""):
    for node in data:
        item = tree.insert(
            parent,
            "end",
            text=node["text"],
            values=node.get("values", ()),
            tags=node.get("tags", ())
        )
        dict_to_tree(tree, node.get("children", []), item)

def tree_to_rules(tree: ttk.Treeview):
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