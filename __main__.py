from amm.engine import find_optimal_amount
from amm.pool import simulate_swaps
from amm import AMM
from utils.cycles import save_available_cycles, load_available_cycles
from utils.sender import build_swap_command, get_account_sequence, send_cmd,  retrieve_last_transaction, \
    compute_amount_in
from connectors.osmosis import make_model
from osmobot_discord.bot import Bot
from cosmostation.CosmoStationApi import CosmoStationApi

import pathlib
import json
import os
import multiprocessing
import asyncio
from dotenv import load_dotenv
from typing import List, Dict
from loguru import logger
import sys

logger.remove()
logger.add(sys.stderr, format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> {level}  <level>{message}</level>",
           level="DEBUG")

maxExecutionTimeoutSeconds = 60.0
nbCPU = multiprocessing.cpu_count()


class App:
    amm: AMM
    base_path: str
    config: dict
    discordToken: str
    discordBot: Bot
    cycles: List[List[str]]
    starters: Dict[str, Dict[str, float]]
    cosmoStationApi: CosmoStationApi

    def __init__(self, discord_token) -> None:
        self.base_path = str(pathlib.Path(__file__).parent.resolve())

        with open(f"{self.base_path}/config/config.json", "r") as f:
            self.config = json.loads(f.read())

        with open(f"{self.base_path}/config/starters.json", "r") as f:
            self.starters = json.loads(f.read())

        self.amm = make_model(regenerate=True)
        self.discordToken = discord_token
        self.discordBot = Bot()
        if len([]) == 1:
            self.cycles = save_available_cycles(
                'osmosis', amm=self.amm, priorities=list(self.starters.keys()))
        else:
            self.cycles = load_available_cycles('osmosis')

    def step(self):
        """
        One step equals fetching, processing, and sending transaction if needed
        """
        logger.debug('Starting a new step')
        self.amm = make_model(regenerate=False)

        best_transaction = self.get_best_transaction()

        if not best_transaction:
            logger.debug(f'No good transaction')
            return

        logger.debug(f'A transaction was found : {best_transaction}')

        sequence = get_account_sequence(self.config['account'])
        amount_in = compute_amount_in(**best_transaction, starters=self.starters)
        cmd = build_swap_command(**best_transaction, amount_in=amount_in, sequence=sequence)

        logger.debug(f'cmd successfully built : {cmd}')

        txhash, stdout = send_cmd(cmd)

        if txhash:
            logger.success(f'cmd successfully sent : https://www.mintscan.io/osmosis/txs/{txhash}')
        else:
            logger.error(f'cmd failed')

        if "insufficient fees" in stdout:
            self.config["fees"] += 100

        lastCosmoStationTx = retrieve_last_transaction(txhash, self.cosmoStationApi)

        self.discordBot.sendMessageOnOsmoBotChannel(lastCosmoStationTx)

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

            dollars_delta = float(self.starters[from_asset]['current_price']) * delta

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

        best_transaction = max(carnet_profits, key=lambda x: x['dollars_delta'])

        for p, asset in zip(best_transaction['pools'], best_transaction['cycle']):
            p.set_source(asset)

        return best_transaction

    async def start_discord_bot(self):
        await self.discordBot.start(self.discordToken)


if __name__ == '__main__':
    load_dotenv(dotenv_path="osmobot_discord/.env")
    token = os.getenv("TOKEN")
    app = App(token)
    app.run()
