class Tab:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def clear(self):
        self.items = []

    def list_items(self):
        for item in self.items:
            print(item)