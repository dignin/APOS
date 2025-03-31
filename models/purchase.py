from datetime import datetime

class Purchase:
    def __init__(self, items):
        self.items = items
        self.timestamp = datetime.now()

    def total(self):
        return sum(item.price for item in self.items)

    def receipt(self):
        lines = [str(item) for item in self.items]
        lines.append(f"Total: €{self.total():.2f}")
        lines.append(f"Date: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)
