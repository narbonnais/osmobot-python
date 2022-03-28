import pathlib
import json

from amm.pool import simulate_swaps
from osmobot_discord.bot import Bot
from dotenv import load_dotenv

import os
import multiprocessing
import asyncio

from connectors.osmosis import make_model
from utils.cycles import save_available_cycles, rotate_cycle
from utils.sender import build_swap_command
# Typing
from amm import AMM
from typing import Tuple, List, Dict
from amm.engine import find_optimal_amount

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

    def __init__(self, discord_token) -> None:
        self.base_path = str(pathlib.Path(__file__).parent.resolve())

        with open(f"{self.base_path}/config/config.json", "r") as f:
            self.config = json.loads(f.read())

        with open(f"{self.base_path}/config/starters.json", "r") as f:
            self.starters = json.loads(f.read())

        self.amm = make_model(regenerate=True)
        self.discordToken = discord_token
        self.discordBot = Bot()
        self.cycles = save_available_cycles('osmosis', amm=self.amm, priorities=list(self.starters.keys()))

    def reload_cycles(self):
        self.cycles = save_available_cycles('osmosis', amm=self.amm, priorities=list(self.starters.keys()))

    async def step(self):
        """
        One step equals fetching, processing, and sending transaction if needed
        """
        print('TOP')
        self.amm = make_model(regenerate=False)

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

            carnet_profits.append((dollars_delta, delta, from_asset, best_input, pools, cycle))

        carnet_profits.sort(reverse=True)
        cmd = build_swap_command(*carnet_profits[0])
        print(cmd)

    async def run(self):
        while True:
            try:
                await asyncio.wait_for(self.step(), timeout=maxExecutionTimeoutSeconds)
            except asyncio.TimeoutError:
                await self.discordBot.sendMessageOnOsmoBotChannel("Timeout")

    async def start_discord_bot(self):
        await self.discordBot.start(self.discordToken)


if __name__ == '__main__':
    load_dotenv(dotenv_path="osmobot_discord/.env")
    token = os.getenv("TOKEN")
    app = App(token)

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(app.start_discord_bot())
        loop.create_task(app.run())
        loop.run_forever()
    except KeyboardInterrupt as e:
        print("Exited")
