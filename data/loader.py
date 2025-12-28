from lxml import etree
from collections import defaultdict, Counter

class OSMData:
    def __init__(self):
        self.root = None
        self.file_path = None

    # ---------- Load OSM File as root ----------
    def load_file(self, file_path):
        self.file_path = file_path
        self.tree = etree.parse(file_path)
        self.root = self.tree.getroot()

    # ---------- Save root as OSM File ----------
    def save_file(self, file_path):
        self.tree.write(file_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

    # ---------- Count all Elements on root ----------
    def count_elements(self):
        if self.root is None:
            return {"nodes": 0, "ways": 0, "relations": 0}

        return {
            "nodes": len(self.root.findall(".//node")),
            "ways": len(self.root.findall(".//way")),
            "relations": len(self.root.findall(".//relation")),
        }

    # ---------- Count all tags on root ----------
    def count_tags(self):
        if self.root is None:
            return {}

        tag_counts = defaultdict(int)
        for tag in self.root.findall(".//tag"):
            k = tag.get("k")
            if k:
                tag_counts[k] += 1
        return tag_counts

    # ---------- Remove tags based on filter ----------
    def remove_tags(self, rules):
        """
        For every element:
        I. Check every rule for every category, if childrule, check childrules. Protect allowed tags.
        II. Remove all tags that are not protected.
        """
        print("Remove tags")
        for elem in self.root.xpath(".//node | .//way | .//relation"):
            tag_elems = list(elem.findall("tag"))
            allowed_tags = set()

            def check_rule(rule):
                for tag in tag_elems:
                    k = tag.get("k")
                    v = tag.get("v")
                    if k == rule[0]:
                        if rule[1] is None:
                            allowed_tags.add(tag)
                        else:
                            if v in rule[1]:
                                allowed_tags.add(tag)
                            else:
                                return
                        if rule[2] is not None:
                            for child_rule in rule[2]:
                                check_rule(child_rule)

            # Check Rules
            for category in rules:
                for rule in category[1]:
                    check_rule(rule)

            # Remove Tags
            for tag in tag_elems:
                if tag not in allowed_tags:
                    elem.remove(tag)

    # ---------- Remove elements without tags ----------
    def remove_elements(self):
        """
        First all relations/ways/nodes with tags protect themself and their members.
        Then all relations/ways/nodes that are not protected are removed.
        """
        print("Remove elements")
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
                protected_ways.add(way.get("id"))
                for node in way.findall("nd"):
                    protected_nodes.add(node.get("ref"))

        # Node protecting
        for node in self.root.findall(".//node"):
            if node.findall("tag"):
                protected_nodes.add(node.get("id"))

        # Relation removal
        for rel in self.root.findall(".//relation"):
            if rel.get("id") not in protected_relations:
                self.root.remove(rel)
        
        # Way removal
        for way in self.root.findall(".//way"):
            if way.get("id") not in protected_ways:
                self.root.remove(way)

        # Node removal
        for node in self.root.findall(".//node"):
            if node.get("id") not in protected_nodes:
                self.root.remove(node)

