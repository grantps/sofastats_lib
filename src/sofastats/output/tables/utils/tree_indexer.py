"""
In a list the first item is the root, and the subsequent items are sub-trees.
The sub-trees follow the same pattern, so it is recursive.

Col (var metrics) trees do not include value details. So we reference "Country" but not "NZ" or "Japan".

Task 1 - generic tree:
                                   a
                                   |
              ---------------------------------------------
              |                    |                       |
              b                    c                       d
              |                    |                       |
              e                    f                       g
                                   |
                                   h
which is represented as:

col_tree = [
    'a',
    ['b', ['e', ]],
    ['c', ['f', ['h', ]]],
    ['d', ['g', ]],
]

[
    [('b', 0), ('e', 0)],
    [('c', 1), ('f', 0), ('h', 0)],
    [('d', 2), ('g', 0)],
]

Task 2 - col tree with usual gap-fillers so always same length:

                                  root
                                   |
              ---------------------------------------------
              |                    |                       |
          Age Group            Browser              Age Group Repeated
              |                    |                       |
          __blank__            Age Group               __blank__
              |                    |                       |
              |             ----------------               |
              |             |              |               |
          __blank__      Country         Gender        __blank__
              |             |              |               |
            freq          freq           freq            freq

which is represented as:

col_tree = [
    'root',
    ['Age Group', ['__blank__', ['__blank__', ['freq', ]]]],
    ['Browser', ['Age Group', ['Country', ['freq', ]], ['Gender', ['freq', ]]]],
    ['Age Group Repeated', ['__blank__', ['__blank__', ['freq', ]]]],
]

Goal: Capture the order so the order of the merged / joined dataframe can be restored
after pandas sorts everything alphabetically.

[
    [('Age Group', 0), ('__blank__', 0), ('__blank__', 0), ('freq', 0)],
    [('Browser', 1), ('Age Group', 0), ('Country', 0), ('freq', 0)],
    [('Browser', 1), ('Age Group', 0), ('Gender', 1), ('freq', 0)],
    [('Age Group Repeated', 2), ('__blank__', 0), ('__blank__', 0), ('freq', 0)],
]
"""

def update_orders(orders: list, tree: list, ancestors_with_orders: list, *, node_order: int = 0):
    """
    :param orders: the final list of orders (gets added to at the leaf end of things)
     e.g. [[('Age Group', 0), ('freq', 0)], ] if we have just collected the first complete branch-to-leaf sequence
    :param tree: any remaining subtree under existing list of ancestors (might be single-item list
     i.e. reached leaf end of that branch e.g. ['Age Group', ['Freq', ]])
    :param node_order: what was the order of the node in the source tree
    :param ancestors_with_orders: branches leading up to now, each with the order
     e.g. [[('Age Group', 0), ] if we are still recursing into first branch-to-leaf sequence

    Note - mutating a single list (orders)

    Task: look at tree. Any sub-trees or just the node?
    If just the node, we're at the leaf end and our sole job is to append (node, 0) to a copy of ancestors_with_orders
    and append that copy to orders.
    If sub-trees, we also append (node, 0) to a copy of ancestors_with_orders, and for each sub-tree,
    we pass it in recursively as the tree, and pass in the updated copy of ancestors_with_orders.
    The orders item remains unchanged.

    If root node, don't update ancestors_with_orders.
    """
    is_leaf = len(tree) == 1  ## just a node
    node = tree[0]
    ancestors_with_orders = ancestors_with_orders.copy()
    if node != 'root':
        ancestors_with_orders.append((node, node_order))
    if is_leaf:
        orders.append(ancestors_with_orders)
    else:
        for node_order, sub_tree in enumerate(tree[1:]):
            update_orders(orders, sub_tree, ancestors_with_orders, node_order=node_order)

def get_orders(col_tree: list, *, debug=False) -> list:
    orders = []
    ancestors_with_orders = []
    update_orders(orders, col_tree, ancestors_with_orders)
    if debug:
        for order in orders:
            print(order)
    return orders

def run():
    col_tree = [
        'root',
        ['Age Group', ['Freq', ]],
        ['Browser', ['Age Group', ['Freq', ]]],
        ['Age Group Repeated', ['Country', ['Freq', ]], ['Gender', ['Freq', ]], ['Country Repeated', ['Freq', ]]],
    ]
    _orders = get_orders(col_tree, debug=True)

if __name__ == '__main__':
    run()
