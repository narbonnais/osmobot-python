from amm.engine import find_optimal_amount
from amm.pool import simulate_swaps
from amm import AMM
from utils.cycles import save_available_cycles, rotate_cycle
from utils.sender import build_swap_command, get_account_sequence
from connectors.osmosis import make_model
from osmobot_discord.bot import Bot
import pathlib
import json
import os
import multiprocessing
import asyncio
from dotenv import load_dotenv
from subprocess import Popen, PIPE
from typing import Tuple, List, Dict
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)


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
        self.cycles = save_available_cycles(
            'osmosis', amm=self.amm, priorities=list(self.starters.keys()))

    def reload_cycles(self):
        self.cycles = save_available_cycles(
            'osmosis', amm=self.amm, priorities=list(self.starters.keys()))

    async def step(self):
        """
        One step equals fetching, processing, and sending transaction if needed
        """
        logging.info("New step")
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

            dollars_delta = float(
                self.starters[from_asset]['current_price']) * delta
            if dollars_delta <= self.config['minimum_dollars_delta']:
                continue

            carnet_profits.append(
                (dollars_delta, delta, from_asset, best_input, pools, cycle))

        carnet_profits.sort(reverse=True)
        if len(carnet_profits) == 0:
            return
        account = self.config['account']
        sequence = get_account_sequence(account)
        dollars_delta, delta, from_asset, best_input, pools, cycle = carnet_profits[0]
        cmd = build_swap_command(
            best_input, pools, cycle, account, sequence)

        # Send command using `osmosisd`
        txLogMessage = f"Tx sent {sequence}: {round(best_input  / 1e6, 3)}\t{from_asset}\tvia pools\t[{pools}]\tfor +{round(delta  / 1e6, 3)}\t{from_asset}"
        try:
            logging.info(cmd)
            p = Popen(cmd.split(" "), stdin=PIPE, stdout=PIPE)
            stdout = p.stdout.read().decode()
            logging.info(f"Transaction result : {stdout}")
            hash = stdout.split("txhash: ")[1].split("\n")[0]
            # txLogMessage = txLogMessage + f"\thash\t{hash}"

            # print("Hash:", hash)
            # print(f"INFO: {step_start} - Wait for 6 seconds to let the chain stat to be updated")

            # Try to retrieve last transaction from cosmostation
            retryCount = 10
            lastCosmoStationTx = None
            while retryCount > 0:
                try:
                    logging.debug("Try to retrieve last tx")
                    lastCosmoStationTx = await self.cosmoStationApi.getTransactionDetailsAsync(hash)
                    break
                except Exception as e:
                    logging.debug(f"{e}")
                    await asyncio.sleep(1)
                    pass

                retryCount -= 1

            # Try to retrieve last transaction from cosmostation

            if "insufficient fees" in stdout:
                self.config["fees"] += 100
                self.totalInsufficientFeeTransactionsCount = self.totalInsufficientFeeTransactionsCount + 1
                txLogMessage = txLogMessage + \
                    f"\tstatus\tfailed (insufficient fees)"
            else:
                sequence += 1
                # Increase transaction success count

                if lastCosmoStationTx == None:
                    self.totalSuccessTransactionsCount = self.totalSuccessTransactionsCount + 1
                    txLogMessage = txLogMessage + f"\tstatus\tsuccess"
                else:
                    if lastCosmoStationTx.isSuccess:
                        self.totalSuccessTransactionsCount = self.totalSuccessTransactionsCount + 1
                        txLogMessage = txLogMessage + f"\tstatus\tsuccess"
                    else:
                        txLogMessage = txLogMessage + f"\tstatus\tfailed"

            txLogMessage = txLogMessage + \
                f"\nhttps://www.mintscan.io/osmosis/txs/{hash}"
            
        except Exception as e:
            logging.error(f"{e}")
            # print(message)
            txLogMessage = txLogMessage + f"\tstatus\tfailed {e}"

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
