def compare(op, x, y):
    if op == 'eq':
        return x == y
    elif op == 'gt':
        return x > y
    elif op == 'lt':
        return x < y
    elif op == 'ne':
        return x != y

def apply_operator(op, x, y):
    if op == "OR":
        return x or y
    elif op == "AND":
        return x and y