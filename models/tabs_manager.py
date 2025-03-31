class TabsManager:
    def __init__(self):
        # Dictionary to store a single tab for each user
        self.user_tabs = {}

    def add_tab(self, user_id):
        """Add or overwrite a tab for a specific user."""
        tab_name = f"Tab for User {user_id}"
        self.user_tabs[user_id] = {"name": tab_name, "items": []}

    def get_tabs(self, user_id):
        """Retrieve the tab for a specific user."""
        return [self.user_tabs[user_id]] if user_id in self.user_tabs else []

    def close_tab(self, user_id):
        """Close the tab for a user."""
        if user_id in self.user_tabs:
            del self.user_tabs[user_id]

    def list_users(self):
        """List all users with active tabs."""
        return list(self.user_tabs.keys())

    def clear_tabs(self, user_id):
        """Clear all items in the user's tab."""
        if user_id in self.user_tabs:
            self.user_tabs[user_id]["items"] = []

    def has_tab(self, user_id):
        """Check if a user has a tab."""
        return user_id in self.user_tabs

    def get_all_tabs(self):
        """Retrieve all tabs for all users."""
        return {user_id: self.user_tabs[user_id]["name"] for user_id in self.user_tabs}

    def update_item(self, user_id, item_index, new_name, new_price):
        """Update an item in the user's tab."""
        if user_id in self.user_tabs:
            tab = self.user_tabs[user_id]["items"]
            if 0 <= item_index < len(tab):
                tab[item_index]["name"] = new_name
                tab[item_index]["price"] = new_price
                return True
        return False

    def remove_item(self, user_id, item_index):
        """Remove an item from the user's tab."""
        if user_id in self.user_tabs:
            tab = self.user_tabs[user_id]["items"]
            if 0 <= item_index < len(tab):
                tab.pop(item_index)
                return True
        return False
