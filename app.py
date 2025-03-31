from flask import Flask, request, jsonify, render_template
from models import TabsManager

app = Flask(__name__)
tabs_manager = TabsManager()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create_tab", methods=["POST"])
def create_tab():
    user_id = request.form.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    tabs_manager.add_tab(user_id)
    return jsonify({"message": f"Tab created or updated for user {user_id}."})

@app.route("/get_tabs/<user_id>", methods=["GET"])
def get_tabs(user_id):
    tabs = tabs_manager.get_tabs(user_id)
    return jsonify({"tabs": [tabs[0]["name"]] if tabs else []})

@app.route("/add_item_to_tab/<user_id>", methods=["POST"])
def add_item_to_tab(user_id):
    """Add an item to the user's tab."""
    item_name = request.form.get("item_name")
    item_price = float(request.form.get("item_price", 0))
    if not item_name or item_price <= 0:
        return jsonify({"error": "Invalid item details"}), 400
    if not tabs_manager.has_tab(user_id):
        return jsonify({"error": "No tab found for this user"}), 400
    tabs_manager.user_tabs[user_id]["items"].append({"name": item_name, "price": item_price})
    return jsonify({"message": f"Item '{item_name}' added to the tab."})

@app.route("/remove_item_from_tab/<user_id>", methods=["POST"])
def remove_item_from_tab(user_id):
    """Remove an item from the user's tab."""
    item_index = int(request.form.get("item_index", -1))
    if item_index < 0:
        return jsonify({"error": "Invalid item index"}), 400
    if not tabs_manager.has_tab(user_id):
        return jsonify({"error": "No tab found for this user"}), 400
    success = tabs_manager.remove_item(user_id, item_index)
    if success:
        return jsonify({"message": f"Item at position {item_index + 1} removed from the tab."})
    return jsonify({"error": "Failed to remove item."}), 400

@app.route("/total_tab/<user_id>", methods=["GET"])
def total_tab(user_id):
    """Calculate the total of the user's tab."""
    if not tabs_manager.has_tab(user_id):
        return jsonify({"error": "No tab found for this user"}), 400
    total = sum(item["price"] for item in tabs_manager.user_tabs[user_id]["items"])
    return jsonify({"total": total})

@app.route("/close_tab/<user_id>", methods=["POST"])
def close_tab(user_id):
    """Close the user's tab."""
    if not tabs_manager.has_tab(user_id):
        return jsonify({"error": "No tab found for this user"}), 400
    tabs_manager.close_tab(user_id)
    return jsonify({"message": f"Tab for user {user_id} has been closed."})

@app.route("/tab_details/<user_id>", methods=["GET"])
def tab_details(user_id):
    """Display details of a specific tab."""
    if not tabs_manager.has_tab(user_id):
        return jsonify({"error": "No tab found for this user"}), 400
    tab = tabs_manager.user_tabs[user_id]
    return render_template("tab_details.html", user_id=user_id, tab=tab)

if __name__ == "__main__":
    app.run(debug=True)
