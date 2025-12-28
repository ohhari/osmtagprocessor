from ui.main_window import MainWindow
from data.loader import OSMData
from data.tag_analysis import TagAnalysis

class App:
    def __init__(self):
        # OSM-Daten und Analyse
        self.osm = OSMData()
        self.analysis = TagAnalysis(self.osm)

        # Hauptfenster
        self.window = MainWindow(self)

    def run(self):
        self.window.mainloop()

    # ---------- Datei laden ----------
    def load_osm_file(self, path):
        self.osm.load_file(path)
        self.update_ui()

    # ---------- UI aktualisieren ----------
    def update_ui(self):
        counts = self.osm.count_elements()
        tags = self.osm.count_tags()
        self.window.update_counts(counts)
        self.window.show_tags(tags)

    # ---------- Kategorien / Tags ----------
    def add_category(self):
        self.window.add_category()

    def add_custom_tag(self):
        self.window.add_custom_tag()

    def process_file(self, rules, path):
        #läuft für testfile durch
        self.osm.remove_tags(rules)
        self.osm.remove_elements()
        self.osm.save_file(path)
        self.update_ui()