from utils.cycles import save_available_cycles, load_available_cycles
from utils.amount import compute_amount_in

from amm.engine import find_transactions
from amm import AMM

from osmosis.query import make_model
from osmosis.execute import build_swap_command, get_account_sequence, send_cmd

import pathlib
import yaml
from typing import List, Dict
from loguru import logger
import sys
import multiprocessing as mp
from functools import partial
import itertools
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
            logger.debug("Waiting for previous tx")
            time.sleep(self.config['sleep_time'])
            return

        self.amm = make_model(regenerate=False)
        logger.debug('Data fetched')

        # with mp.Pool(processes=5) as p:
        #     txs = p.map(partial(find_transactions, amm=self.amm, config=self.config, starters=self.starters),
        #                 self.cycles)
        #
        # txs = list(itertools.chain(*txs))

        txs = []
        for cycle in self.cycles:
            txs += find_transactions(amm=self.amm, config=self.config, starters=self.starters, cycle=cycle)

        if len(txs) == 0:
            logger.debug('No transaction found')
            return

        best_transaction = max(txs)
        logger.debug(f'A transaction was found : {best_transaction}')

        amount_in = compute_amount_in(best_transaction, starters=self.starters)

        cmd = build_swap_command(best_transaction, amount_in=amount_in, sequence=sequence, fees=self.config['fees'])

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

    def run(self):
        while True:
            self.step()


if __name__ == '__main__':
    app = App()
    app.run()
