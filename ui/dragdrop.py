from utils import tree_helpers

class TreeDragDrop:
    def __init__(self, tree_left, tree_right):
        self.drag = False
        self.tree_left = tree_left
        self.tree_right = tree_right
        self.dragged_item = None
        self.dragged_text = None

        self.tree_left.bind("<ButtonPress-1>", self.on_drag_start)
        self.tree_left.bind("<B1-Motion>", self.on_drag_motion)
        self.tree_left.bind("<ButtonRelease-1>", self.on_drag_stop)
        

    def on_drag_start(self, event):
        self.drag = True
        item = self.tree_left.identify_row(event.y)
        if not item:
            return
        self.dragged_item = item
        #self.dragged_text = self.tree_left.item(item, "text")

    def on_drag_motion(self, event):
        if self.drag:
            self.tree_left.master.config(cursor="hand2")

    def on_drag_stop(self, event):
        x, y = event.x_root, event.y_root
        rx = self.tree_right.winfo_rootx()
        ry = self.tree_right.winfo_rooty()
        rw = self.tree_right.winfo_width()
        rh = self.tree_right.winfo_height()
        if rx <= x <= rx + rw and ry <= y <= ry + rh:
            if not self.dragged_item:
                return
            target_item = self.tree_right.selection()
            if target_item:
                parent = target_item
                
            #else:
            #    parent = ""

            #existing = [self.tree_right.item(c, "text") for c in self.tree_right.get_children(parent)]
            #if self.dragged_text in existing:
            #    self.reset_drag()
            #    return
                tree_helpers.copy_item(self.tree_left, self.tree_right, self.dragged_item, parent)
        self.reset_drag()


    def reset_drag(self):
        self.drag = False
        self.dragged_item = None
        self.dragged_text = None
        self.tree_left.master.config(cursor="arrow")