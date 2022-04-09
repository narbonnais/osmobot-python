

def compute_amount_in(best_transaction, starters):

    symbol_in = best_transaction.pools[0].asset_1.symbol

    m = starters[symbol_in]['maximum_input']

    # amount_in = np.round((m * best_input) / (m + best_input), 3)
    amount_in = min(m, best_transaction.best_input)

    return int(amount_in)
