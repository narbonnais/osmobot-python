import asyncio
import discord.ext.tasks
import os
from dotenv import load_dotenv
import requests
from typing import Dict
import attr
import datetime
import json
import signal

load_dotenv(dotenv_path=".env")
token = os.getenv("TOKEN")
atom_denom = "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2"
osmo_denom = "uosmo"

updateTimeout = 5


async def get_price_async(asset):
    return await asyncio.to_thread(get_price, asset)


def get_price(asset):
    usd_price_url = f'https://api-osmosis.imperator.co/tokens/v2/price/{asset}'
    print(f"Fetching : {usd_price_url}")
    res = requests.get(usd_price_url)
    print(f"Fetching result : {res.text}")
    raw_data = json.loads(res.text)

    return raw_data['price']


@attr.s
class OsmosisAccountResponse():
    balances: Dict[str, int] = attr.ib(default=attr.Factory(dict))

    @classmethod
    def from_data(cls, data):
        return cls(
            balances={bal["denom"]: int(bal["amount"])
                      for bal in data["balances"]}
        )


class Bot(discord.Client):
    commandsRoutines: dict

    def __init__(self):
        super().__init__(command_prefix="!")
        self.initial_balances: Dict[str, int] = {
            "ibc/27394FB092D2ECCD56123C74F36E4C1F926001CEADA9CA97EA622B25F41E5EB2": 33990999,
            "uosmo": 20740000,
        }
        self.balances: Dict[str, int] = {}
        self.guild_id = 954947304106897488
        self.last_updated = datetime.datetime.now()
        self.commandsRoutines = {
            "!profit": self.onQueryProfit,
            "!addtoken": self.onQueryAddToken,
            "!updateOsmoBot": self.onQueryUpdateOsmoBot,
            "!commands?": self.onQueryCommands,
        }

    async def on_ready(self):
        print("Le bot est prêt.")
        self.background_get_atom_balance.start()

    async def sendMessageOnChannel(self, message: str, channelId):
        try:
            await self.wait_until_ready()
            channel = self.get_channel(id=channelId)
            await channel.send(message)
        except Exception as e:
            print(f"discord bot ERROR: {e}")

    async def sendMessageOnOsmoBotChannel(self, message: str):
        await self.sendMessageOnChannel(message, 956489942513618974)

    async def sendCommandReceived(self, channel):
        await channel.send("Please wait...")

    def isMessageContainsSupportedCommands(self, message: str):
        for supportedCommand in self.commandsRoutines:
            if message.startswith(supportedCommand):
                return True
        return False

    async def onQueryProfit(self, message):
        assets = ["ATOM", "OSMO"]
        tasks = []

        for asset in assets:
            tasks.append(get_price_async(asset))

        prices = await asyncio.gather(*tasks)

        price_atom = prices[0]
        price_osmo = prices[1]

        diff_atom = (self.balances[atom_denom] -
                     self.initial_balances[atom_denom]) / 1e6
        diff_osmo = (self.balances[osmo_denom] -
                     self.initial_balances[osmo_denom]) / 1e6

        value_atom = diff_atom * price_atom
        value_osmo = diff_osmo * price_osmo
        total_value = value_atom + value_osmo

        lines = [
            f"> Total earned: ${round(total_value, 2)}",
            f"> Last updated: {self.last_updated}",
            f"> ATOM: {round(diff_atom, 2)} (${round(value_atom, 2)})",
            f"> OSMO: {round(diff_osmo, 2)} (${round(value_osmo, 2)})"
        ]

        await message.channel.send("\n".join(lines))

    async def onQueryAddToken(self, message):
        """!addtoken osmo 1000"""

        # Extract instructions
        instructions = message.content.split(" ")
        if len(instructions) != 3:
            await message.channel.send("Syntax error: correct usage is `!addtoken osmo 1000000` for 1 osmo")
            return

        # Parse instructions
        token = instructions[1]
        amount = int(instructions[2])
        if token == "osmo":
            denom = osmo_denom
        elif token == "atom":
            denom = atom_denom
        else:
            await message.channel.send(f"Input error: token {token} not supported. Options: `atom`, `osmo`.")
            return

        # Update amount
        self.initial_balances[denom] += amount

    async def onQueryUpdateOsmoBot(self, message):
        global updateTimeout
        await message.channel.send(f"Updating in {updateTimeout}s...")
        await asyncio.sleep(updateTimeout)
        await message.channel.send(f"Updating...")

        os.kill(os.getpid(), signal.SIGKILL)

    async def onQueryCommands(self, message):
        commandsPresentation = [f"- {command}" for command in self.commandsRoutines]
        await message.channel.send("\n".join(commandsPresentation))

    async def on_message(self, message):
        if not self.isMessageContainsSupportedCommands(message.content):
            return

        await self.sendCommandReceived(message.channel)

        try:
            for command in self.commandsRoutines:
                if message.content.startswith(command):
                    routine = self.commandsRoutines[command]
                    await routine(message)
        except Exception as e:
            await message.channel.send(f"Failed ! => {e}")

    @discord.ext.tasks.loop(seconds=60.0)
    async def background_get_atom_balance(self):
        """Get osmo price every 5 seconds"""

        url = "https://lcd-osmosis.cosmostation.io/cosmos/bank/v1beta1/balances/osmo123kgn90rmdcrhas5fu2anfvnyrhvgurlk7j4es"

        try:
            # Get data and parse it
            raw_data = requests.get(url).json()
            account_response = OsmosisAccountResponse.from_data(raw_data)
            # print(account_response.balances)
            # Update self balance
            self.balances = account_response.balances
            self.last_updated = datetime.datetime.now()
        except Exception as e:
            print(e)

        # Extract ATOM balance
        try:
            atom_bal: int = account_response.balances[atom_denom]
        except:
            print("Atom not found in balances")
            atom_bal = 0

        # Change bot name
        try:
            new_name = f"Osmobot {round(atom_bal / 1e6, 2)} ATOM"
            await self.get_guild(self.guild_id).get_member(self.user.id).edit(nick=new_name)
        except Exception as e:
            print(e)
        # print("ATOM:", round(atom_bal / 1e6, 2))
