from typing import List
from amm import Pool
from utils.fetcher import fetch_raw_data
from subprocess import Popen, PIPE


def get_account_sequence(account):
    return '1'


def build_swap_command(transaction, amount_in, sequence, fees) -> str:
    return ' '


def send_cmd(cmd):
    p = Popen(cmd.split(" "), stdin=PIPE, stdout=PIPE)
    stdout = p.stdout.read().decode()
    return stdout
