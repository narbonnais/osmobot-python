from utils.cycles import save_available_cycles, load_available_cycles
from utils.amount import compute_amount_in

from amm.engine import find_optimal_amount
from amm.pool import simulate_swaps
from amm import AMM

from osmosis.query import make_model
from osmosis.execute import build_swap_command, get_account_sequence, send_cmd

import pathlib
import yaml

from typing import List, Dict
from loguru import logger
import sys

import requests
import time

logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD at HH:mm:ss.SSS}</green> {level}  <level>{message}</level>",
           level="DEBUG")


class App:
    amm: AMM
    base_path: str
    config: dict
    cycles: List[List[str]]
    starters: Dict[str, Dict[str, float]]
    previous_sequence: int

    def __init__(self) -> None:
        self.base_path = str(pathlib.Path(__file__).parent.resolve())

        with open(f"{self.base_path}/config/config.yaml", "r") as f:
            self.config = yaml.safe_load(f)

        with open(f"{self.base_path}/config/starters.yaml", "r") as f:
            self.starters = yaml.safe_load(f)

        self.amm = make_model(
            regenerate=self.config['regenerate_denom2symbol'])

        if self.config['regenerate_cycles']:
            self.cycles = save_available_cycles(
                'osmosis', amm=self.amm, priorities=list(self.starters.keys()))
        else:
            self.cycles = load_available_cycles('osmosis')

        self.previous_sequence = 0

    def step(self):
        """
        One step equals fetching, processing, and sending transaction if needed
        """
        logger.debug('Starting a new step')

        sequence = get_account_sequence(self.config['account'])
        if sequence == self.previous_sequence:
            logger.debug("Waitinig for previous tx")
            time.sleep(self.config['sleep_time'])
            return

        self.amm = make_model(regenerate=False)
        logger.debug('Data fetched')
        best_transaction = self.get_best_transaction()

        if not best_transaction:
            logger.debug(f'No good transaction')
            return

        logger.debug(f'A transaction was found : {best_transaction}')

        amount_in = compute_amount_in(
            **best_transaction, starters=self.starters)

        cmd = build_swap_command(
            **best_transaction, amount_in=amount_in, sequence=sequence)

        logger.debug(f'cmd successfully built : {cmd}')

        if self.config["do_transactions"]:

            txhash, stdout = send_cmd(cmd)

            if txhash:
                logger.success(
                    f'cmd successfully sent : https://www.mintscan.io/osmosis/txs/{txhash}')
                self.previous_sequence = sequence
            else:
                logger.error(f'cmd failed')

            if "insufficient fees" in stdout:
                self.config["fees"] += 100

            requests.post(
                url="http://127.0.0.1:5000/arbitrages/osmosis", data={"hash": txhash})

            time.sleep(self.config["sleep_time"])

    def run(self):
        while True:
            self.step()

    def get_best_transaction(self):
        carnet_profits = []

        for cycle in self.cycles:
            change, pools = self.amm.compute_cycle(cycle)

            if change < 0:
                continue

            from_asset = cycle[0]

            for p, asset in zip(pools, cycle):
                p.set_source(asset)

            best_input = find_optimal_amount(pools, from_asset)

            if best_input <= 0:
                continue

            output = simulate_swaps(pools, from_asset, best_input)[1]

            delta = output - best_input

            dollars_delta = float(
                self.starters[from_asset]['current_price']) * delta

            if dollars_delta <= self.config['minimum_dollars_delta']:
                continue

            transaction = {"dollars_delta": dollars_delta,
                           "delta": delta,
                           "from_asset": from_asset,
                           "best_input": best_input,
                           "pools": pools,
                           "cycle": cycle}

            carnet_profits.append(transaction)

        if len(carnet_profits) == 0:
            return None

        best_transaction = max(
            carnet_profits, key=lambda x: x['dollars_delta'])

        for p, asset in zip(best_transaction['pools'], best_transaction['cycle']):
            p.set_source(asset)

        return best_transaction


if __name__ == '__main__':
    app = App()
    app.run()
