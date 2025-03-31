from models import Item
from models import Purchase
from models import TabsManager

class Tab:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def list_items(self):
        for item in self.items:
            print(f"{item.name}: €{item.price:.2f}")

    def clear(self):
        self.items = []

def menu():
    print("\nPoint-of-Sale Menu:")
    print("1. Create a new tab")
    print("2. Switch to an existing tab")
    print("3. Add Item to current tab")
    print("4. View current tab")
    print("5. Checkout current tab")
    print("6. Exit")

def main():
    # Initialize the TabsManager
    tabs_manager = TabsManager()
    current_user_id = None
    current_tab = None  # Ensure current_tab is initialized

    while True:
        menu()
        choice = input("Select option: ")

        if choice == "1":
            print("Each user can only have one tab. A new tab will be automatically created if it doesn't exist.")
            user_id = input("Enter user ID: ")
            if tabs_manager.get_tabs(user_id):  # Check if the user already has a tab
                print(f"User {user_id} already has a tab.")
            else:
                tabs_manager.add_tab(user_id)  # Removed the extra argument
                print(f"Created a new tab for user {user_id}.")

        elif choice == "2":
            user_id = input("Enter user ID to switch to: ")
            tabs = tabs_manager.get_tabs(user_id)  # Use get_tabs to fetch tabs
            if not tabs:
                print(f"No tab found for user {user_id}. A new tab will be created.")
                tabs_manager.add_tab(user_id)  # Removed the extra argument
                tabs = tabs_manager.get_tabs(user_id)
            current_user_id = user_id
            current_tab = tabs[0]  # Use the first tab for the user
            print(f"Switched to the tab for user {user_id}.")

        elif choice == "3":
            if current_tab is None:  # Check if current_tab is set
                print("No tab selected. Please create or switch to a tab first.")
            else:
                name = input("Item name: ")
                price = float(input("Item price (in euros): "))
                item = Item(name, price)
                current_tab.add_item(item)  # Add item to the current tab
                print(f"Added {item.name} to the current tab.")

        elif choice == "4":
            if current_user_id is None:
                print("No tab selected. Please create or switch to a tab first.")
            else:
                print("Current Tab:")
                current_tab.list_items()

        elif choice == "5":
            if current_user_id is None:
                print("No tab selected. Please create or switch to a tab first.")
            else:
                purchase = Purchase(current_tab.items)
                print("\nReceipt:\n")
                print(purchase.receipt())
                current_tab.clear()
                print("Checked out and cleared the current tab.")

        elif choice == "6":
            print("Exiting POS...")
            break

        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
