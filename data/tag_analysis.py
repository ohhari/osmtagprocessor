from collections import defaultdict, Counter

class TagAnalysis:
    def __init__(self, osm_data):
        """
        osm_data: Instanz von OSMData aus loader.py
        """
        self.osm = osm_data

    # ---------- Tags gruppieren ----------
    def group_tags_by_prefix(self):
        """
        Gibt dict zurück: {prefix: [(full_tag, count), ...]}
        """
        tag_counts = self.osm.count_tags()
        prefix_groups = defaultdict(list)

        for k, count in tag_counts.items():
            if ":" in k:
                prefix, rest = k.split(":", 1)
                prefix_groups[prefix].append((k, count))
            else:
                prefix_groups[k].append((k, count))

        return prefix_groups

    # ---------- Alle Values für einen Tag zählen ----------
    def count_values(self, tag_key):
        """
        Gibt Counter zurück: {value: count, ...}
        """
        values = self.osm.get_values_for_tag(tag_key)
        return Counter(values)

    # ---------- Assoziierte Tags ----------
    def associated_tags(self, tag_key):
        """
        Gibt dict zurück: {"Nodes": {k: count, ...}, "Ways": {...}, "Relations": {...}}
        """
        return self.osm.get_associated_tags(tag_key)

    # ---------- Alle Tags mit gemeinsamen Elementen ----------
    def tags_together(self, tag_key):
        """
        Gibt dict zurück: {other_tag: count}, für alle Tags, die zusammen mit tag_key in einem Element vorkommen
        """
        assoc = self.associated_tags(tag_key)
        result = {}
        for section_counts in assoc.values():
            for k, count in section_counts.items():
                result[k] = result.get(k, 0) + count
        return result