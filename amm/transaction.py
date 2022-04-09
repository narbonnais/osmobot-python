from functools import total_ordering


@total_ordering
class Transaction:
    def __init__(self, dollars_delta, delta, from_asset, best_input, pools, cycle, change):
        self.dollars_delta = dollars_delta
        self.delta = delta
        self.from_asset = from_asset
        self.best_input = best_input
        self.pools = pools
        self.cycle = cycle
        self.change = change

    def __eq__(self, other):
        return self.dollars_delta == other.dollars_delta

    def __lt__(self, other):
        return self.dollars_delta < other.dollars_delta

    def __repr__(self):
        return f"Transaction(dollars_delta={self.dollars_delta}, cycle={self.cycle}, amount_in={self.best_input})"
