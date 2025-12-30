import os
from lxml import etree
from collections import defaultdict, Counter

class OSMData:
    def __init__(self):
        self.root = None
        self.file_path = None

        self.relation_cnt = 0
        self.way_cnt = 0
        self.node_cnt = 0

        self.relations_by_id = None
        self.ways_by_id = None
        self.nodes_by_id = None

    # ---------- Load OSM File as root ----------
    #def load_file2(self, file_path):
    #    self.file_path = file_path
    #    self.tree = etree.parse(file_path)
    #    self.root = self.tree.getroot()

    def load_file(self, file_path, progressbar):
        file_size = os.path.getsize(file_path)

        context = etree.iterparse(
            file_path,
            events=("end",),
            huge_tree=True
        )

        progressbar.set_state_message("Parse tree...")
        progressbar.set_progress(0, 100)

        root = None
        update = 0

        for event, elem in context:
            if root is None:
                root = elem.getroottree().getroot()

            update += 1

            if (update % 10000) == 0:
                percent = int(update * 6000 / file_size)
                if percent >= 100:
                    percent = 100
                progressbar.set_progress(percent, 100)

        self.tree = root.getroottree()
        self.root = root
        progressbar.set_state_message("Process tree...")
        progressbar.set_progress(100, 100)

        #Index
        self.relations_by_id = {rel.get("id"): rel for rel in self.root.findall(".//relation")}
        self.ways_by_id = {way.get("id"): way for way in self.root.findall(".//way")}
        self.nodes_by_id = {node.get("id"): node for node in self.root.findall(".//node")}


    # ---------- Save root as OSM File ----------
    def save_file(self, file_path):
        self.tree.write(file_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

    # ---------- Count all Elements on root ----------
    def count_elements(self):
        if self.root is not None:
            self.relation_cnt =  len(self.relations_by_id)
            self.way_cnt = len(self.ways_by_id)
            self.node_cnt = len(self.nodes_by_id)

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
    def remove_tags(self, rules, progressbar):
        """
        For every element:
        I. Check every rule for every category, if childrule, check childrules. Protect allowed tags.
        II. Remove all tags that are not protected.
        """
        to_check_cnt = self.relation_cnt + self.way_cnt + self.node_cnt
        elem_cnt = 0
        progressbar.set_state_message("Remove tags...")
        progressbar.set_progress(0, to_check_cnt)
        for elem in self.root.xpath(".//node | .//way | .//relation"):
            elem_cnt += 1
            if (elem_cnt % 1000) == 0:
                progressbar.set_progress(elem_cnt, to_check_cnt)
            tag_elems = list(elem.findall("tag"))
            tag_dict = {tag.get("k"): tag for tag in tag_elems}
            allowed_tags = set()

            def check_rule(rule):
                key, values, child_rules = rule
                tag = tag_dict.get(key)
                if tag is None:
                    return

                if values is None or tag.get("v") in values:
                    allowed_tags.add(tag)
                    if child_rules:
                        for child_rule in child_rules:
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
    def remove_elements(self, progressbar):
        """
        First all relations/ways/nodes with tags protect themself and their members.
        Then all relations/ways/nodes that are not protected are removed.
        """
        #"Protect elements
        self.protected_relations = set()
        self.protected_ways = set()
        self.protected_nodes = set()

        # Relation protecting
        progressbar.set_state_message("Protect relations...")
        progressbar.set_progress(0, self.relation_cnt)
        for i, (rel_id, rel) in enumerate(self.relations_by_id.items(), 1):
            if rel.findall("tag"):
                self.protect_relation(rel_id)
            if i % 100 == 0:
                progressbar.set_progress(i, self.relation_cnt)
                
        # Way protecting
        progressbar.set_state_message("Protect ways...")
        progressbar.set_progress(0, self.way_cnt)
        for i, (way_id, way) in enumerate(self.ways_by_id.items(), 1):
            if way.findall("tag"):
                self.protect_way(way_id)
            if i % 1000 == 0:
                progressbar.set_progress(i, self.way_cnt)

        # Node protecting
        progressbar.set_state_message("Protect nodes...")
        progressbar.set_progress(0, self.node_cnt)
        for i, (node_id, node) in enumerate(self.nodes_by_id.items(), 1):
            if node.findall("tag"):
                self.protect_node(node_id)
            if i % 10000 == 0:
                progressbar.set_progress(i, self.node_cnt)

        #Remove elements
        to_delete_relation_cnt = self.relation_cnt - len(self.protected_relations)
        to_delete_way_cnt = self.way_cnt - len(self.protected_ways)
        to_delete_node_cnt = self.node_cnt - len(self.protected_nodes)

        deleted_relation_cnt = 0
        deleted_way_cnt = 0
        deleted_node_cnt = 0

        # Relation removal
        progressbar.set_state_message("Remove relations...")
        progressbar.set_progress(0, to_delete_relation_cnt)
        to_delete_relations = [rel_id for rel_id in self.relations_by_id if rel_id not in self.protected_relations]
        for i, rel_id in enumerate(to_delete_relations, 1):
            self.root.remove(self.relations_by_id[rel_id])
            if i % 1000 == 0:
                progressbar.set_progress(i, len(to_delete_relations))
                
        # Way removal
        progressbar.set_state_message("Remove ways...")
        progressbar.set_progress(0, to_delete_way_cnt)
        to_delete_ways = [way_id for way_id in self.ways_by_id if way_id not in self.protected_ways]
        for i, way_id in enumerate(to_delete_ways, 1):
            self.root.remove(self.ways_by_id[way_id])
            if i % 1000 == 0:
                progressbar.set_progress(i, len(to_delete_ways))

        # Node removal
        progressbar.set_state_message("Remove nodes...")
        progressbar.set_progress(0, to_delete_node_cnt)
        to_delete_nodes = [node_id for node_id in self.nodes_by_id if node_id not in self.protected_nodes]
        for i, node_id in enumerate(to_delete_nodes, 1):
            self.root.remove(self.nodes_by_id[node_id])
            if i % 10000 == 0:
                progressbar.set_progress(i, len(to_delete_nodes))

    def protect_relation(self, rel_id, visited_relations=None):
        if rel_id in self.protected_relations:
            return
        
        #Prevent circular calls
        if visited_relations is None:
            visited_relations = set()

        if rel_id in visited_relations:
            return

        visited_relations.add(rel_id)
        self.protected_relations.add(rel_id)

        #Get relation element from id
        rel = self.relations_by_id.get(rel_id)
        if rel is None:
            return

        for member in rel.findall("member"):
            m_type = member.get("type")
            m_ref = member.get("ref")

            if m_type == "relation":
                self.protect_relation(m_ref, visited_relations)

            elif m_type == "way":
                self.protect_way(m_ref)

            elif m_type == "node":
                self.protect_node(m_ref)
    
    def protect_way(self, way_id):
        if way_id in self.protected_ways:
            return

        self.protected_ways.add(way_id)

        #Get way element from id
        way = self.ways_by_id.get(way_id)
        if way is None:
            return

        for nd in way.findall("nd"):
            self.protect_node(nd.get("ref"))

    def protect_node(self, node_id):
        self.protected_nodes.add(node_id)

