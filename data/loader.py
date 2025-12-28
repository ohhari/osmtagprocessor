from lxml import etree
from collections import defaultdict, Counter

class OSMData:
    def __init__(self):
        self.root = None
        self.file_path = None
        self.marked_elem = None

    def load_file(self, file_path):
        """OSM-Datei laden und Root speichern"""
        self.file_path = file_path
        self.tree = etree.parse(file_path)
        self.root = self.tree.getroot()

    def save_file(self, file_path):
        """OSM-Datei laden und Root speichern"""
        self.tree.write(file_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

    # ---------- Counts ----------
    def count_elements(self):
        if self.root is None:
            return {"nodes": 0, "ways": 0, "relations": 0}

        return {
            "nodes": len(self.root.findall(".//node")),
            "ways": len(self.root.findall(".//way")),
            "relations": len(self.root.findall(".//relation")),
        }

    # ---------- Alle Tags zählen ----------
    def count_tags(self):
        if self.root is None:
            return {}

        tag_counts = defaultdict(int)
        for tag in self.root.findall(".//tag"):
            k = tag.get("k")
            if k:
                tag_counts[k] += 1
        return tag_counts

    # ---------- Alle Values für ein Tag ----------
    def get_values_for_tag(self, tag_key):
        if not self.root:
            return []

        values = [tag.get("v") for tag in self.root.findall(".//tag") if tag.get("k") == tag_key]
        return values

    # ---------- Elemente mit einem Tag ----------
    def get_elements_with_tag(self, tag_key):
        """
        Gibt Dict zurück: {"Nodes": [...], "Ways": [...], "Relations": [...]}
        Jedes Element enthält dict(id=..., tags={k:v,...})
        """
        if not self.root:
            return {}

        sections = {"Nodes": ".//node", "Ways": ".//way", "Relations": ".//relation"}
        result = {}

        for section_name, xpath in sections.items():
            elements = []
            for elem in self.root.findall(xpath):
                tags = {t.get("k"): t.get("v") for t in elem.findall("tag")}
                if tag_key in tags:
                    elements.append({"id": elem.get("id"), "tags": tags})
            if elements:
                result[section_name] = elements

        return result

    # ---------- Assoziierte Tags ----------
    def get_associated_tags(self, tag_key):
        """
        Alle Tags, die zusammen mit tag_key in einem Element auftauchen
        Rückgabe: {"Nodes": {k: count, ...}, "Ways": {...}, "Relations": {...}}
        """
        if not self.root:
            return {}

        sections = {"Nodes": ".//node", "Ways": ".//way", "Relations": ".//relation"}
        result = {}

        for section_name, xpath in sections.items():
            assoc_counts = defaultdict(int)
            for elem in self.root.findall(xpath):
                keys = {t.get("k") for t in elem.findall("tag")}
                if tag_key not in keys:
                    continue
                for k in keys:
                    if k != tag_key:
                        assoc_counts[k] += 1
            if assoc_counts:
                result[section_name] = dict(assoc_counts)

        return result
    
    def remove_tags(self, rules):
        for elem in self.root.xpath(".//node | .//way | .//relation"):
            #print(f"next element {elem.get("id")}")
            tag_elems = list(elem.findall("tag"))
            allowed_tags = set()

            def check_rule(rule):
                for tag in tag_elems:
                    k = tag.get("k")
                    v = tag.get("v")
                    #print(f"    Check {k}: {v}")
                    if k == rule[0]:
                        #print(f"    Rule: {rule[0]}")
                        if rule[1] is None:
                            #print("     Value allowed None")
                            allowed_tags.add(tag)
                        else:
                            if v in rule[1]:
                                #print("     Value allowed v")
                                allowed_tags.add(tag)
                            else: 
                                #print("     Value not allowed")
                                return
                        if rule[2] is not None:
                            #print("     has child")
                            for child_rule in rule[2]:
                                check_rule(child_rule)
                    else:
                        pass
                        #print("     Tag not allowed")

            # Check Rules
            for category in rules:
                #print(f" Check next Category: {category[0]}")
                for rule in category[1]:
                    check_rule(rule)


            # Remove Tags
            #print(f"allowed tags {allowed_tags}")
            for tag in tag_elems:
                if tag not in allowed_tags:
                    #print(f"remove {tag.get("k")}")
                    elem.remove(tag)

    # ---------- Remove Tags ----------
    def remove_tags2(self, whitelist):
        for elem in self.root.findall(".//*"):  # node, way, relation
            for tag in list(elem.findall("tag")):
                k = tag.get("k")
                v = tag.get("v")
                if k not in whitelist:
                    elem.remove(tag)
                    continue

                allowed_values = whitelist[k]

                if allowed_values is None:
                    continue #bricht  schleifendurchlauf ab

                if v not in allowed_values:
                    elem.remove(tag)

    def remove_elements(self):
        print("remove elements")
        protected_relations = set()
        protected_ways = set()
        protected_nodes = set()

        # Relation protecting
        for rel in self.root.findall(".//relation"):
            if rel.findall("tag"):
                #print(f"Relation {rel.get("id")} protected")
                protected_relations.add(rel.get("id"))
                for member in rel.findall("member"):
                    if member.get("type") == "relation":
                        protected_relations.add(member.get("ref"))
                    if member.get("type") == "way":
                        protected_ways.add(member.get("ref"))
                    if member.get("type") == "node":
                        protected_nodes.add(member.get("ref"))
        
        # Way protecting
        for way in self.root.findall(".//way"):
            if way.findall("tag"):
                #print(f"Way {way.get("id")} protected")
                protected_ways.add(way.get("id"))
                for node in way.findall("nd"):
                    protected_nodes.add(node.get("ref"))

        # Node protecting
        for node in self.root.findall(".//node"):
            if node.findall("tag"):
                #print(f"Node {node.get("id")} protected")
                protected_nodes.add(node.get("id"))

        # Relation removal
        for rel in self.root.findall(".//relation"):
            #print(f"Relation {rel.get("id")} removed")
            if rel.get("id") not in protected_relations:
                self.root.remove(rel)
        
        # Way removal
        for way in self.root.findall(".//way"):
            if way.get("id") not in protected_ways:
                #print(f"Way {way.get("id")} removed")
                self.root.remove(way)

        # Node removal
        for node in self.root.findall(".//node"):
            if node.get("id") not in protected_nodes:
                #print(f"Node {node.get("id")} removed")
                self.root.remove(node)

