from flask import Flask, request, jsonify
from itertools import permutations
import copy

app = Flask(__name__)

# Distance between centers and L1
distances = {
    'C1': {'C2': 10, 'C3': 20, 'L1': 30},
    'C2': {'C1': 10, 'C3': 15, 'L1': 25},
    'C3': {'C1': 20, 'C2': 15, 'L1': 35},
    'L1': {'C1': 30, 'C2': 25, 'C3': 35}
}

# Stock available at each warehouse
warehouse_inventory = {
    'C1': {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1},
    'C2': {'F': 1, 'G': 2, 'H': 1},
    'C3': {'I': 3}
}

product_weight = 0.5  # in kg

@app.route('/calculate', methods=['POST'])
def calculate_min_cost():
    order = request.get_json()

    # Defensive check for input
    try:
        order = {k: int(v) for k, v in order.items()}
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid input. Make sure all values are integers.'}), 400

    min_cost = float('inf')

    for start in ['C1', 'C2', 'C3']:
        cost = find_best_cost(start, order)
        if cost is not None:
            min_cost = min(min_cost, cost)

    return jsonify(int(min_cost)) if min_cost != float('inf') else jsonify({'error': 'Cannot fulfill order'})

def find_best_cost(start, order):
    all_warehouses = ['C1', 'C2', 'C3']
    possible_sequences = permutations(all_warehouses)

    min_route_cost = float('inf')

    for sequence in possible_sequences:
        if sequence[0] != start:
            continue
        inventory_copy = copy.deepcopy(warehouse_inventory)
        order_copy = copy.deepcopy(order)

        cost = 0
        current_location = sequence[0]
        carried_items = {}

        for next_stop in sequence:
            picked = pick_from_warehouse(order_copy, inventory_copy[next_stop])
            if not picked:
                continue

            # Move to next warehouse or to L1 for delivery
            if current_location != next_stop:
                cost += travel_cost(current_location, next_stop, carried_items)

            # Pick up items
            for p, qty in picked.items():
                carried_items[p] = carried_items.get(p, 0) + qty

            # Deliver to L1 after each pickup
            cost += travel_cost(next_stop, 'L1', carried_items)
            carried_items = {}

            current_location = 'L1'  # now at customer

        if sum(order_copy.values()) == 0:
            min_route_cost = min(min_route_cost, cost)

    return min_route_cost if min_route_cost != float('inf') else None

def pick_from_warehouse(order, stock):
    picked = {}
    for item in order:
        qty_needed = int(order.get(item, 0)) if isinstance(order.get(item), (int, float)) else 0
        if qty_needed > 0 and item in stock:
            qty = min(qty_needed, stock[item])
            if qty > 0:
                picked[item] = qty
                order[item] = qty_needed - qty
                stock[item] -= qty
    return picked

def travel_cost(src, dest, items):
    weight = sum(qty for qty in items.values()) * product_weight
    return distances[src][dest] * weight

if __name__ == '__main__':
    app.run(debug=True)
