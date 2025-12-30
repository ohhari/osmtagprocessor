from ui.main_window import MainWindow
from data.loader import OSMData

class App:
    def __init__(self):
        self.osm = OSMData()
        self.window = MainWindow(self)

    def run(self):
        self.window.mainloop()

    # ---------- Update UI ----------
    def update_ui(self):
        self.osm.count_elements()
        tags = self.osm.count_tags()
        self.window.update_counts()
        self.window.show_tags(tags)

    # ---------- Load File ----------
    def load_osm_file(self, path, progressbar):
        self.osm.load_file(path, progressbar)
        self.update_ui()

    # ---------- Process File ----------
    def process_file(self, rules, path, progressbar):
        self.osm.remove_tags(rules, progressbar)
        self.osm.remove_elements(progressbar)
        self.osm.save_file(path)
        self.update_ui()