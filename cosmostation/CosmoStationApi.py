import json
import requests
import asyncio
from typing import List
from .CosmoStationApiTransactionDetailsAnswer import CosmoStationTransactionDetailsAnswer, \
    cosmostation_transaction_from_dict
from .CosmoStationApiTransactionListAnswer import CosmoStationTransactionListAnswerElement, \
    cosmo_station_transaction_list_answer_from_dict
from .CosmoStationApiBalanceAnswer import CosmoStationBalanceAnswer, cosmo_station_balance_answer_from_dict

txMaxDownloadPerRequest = 50


class CosmoStationApi:
    def __init__(self) -> None:
        pass

    def getTransactionDetails(self, hash: str) -> CosmoStationTransactionDetailsAnswer:
        url = f'https://api-osmosis.cosmostation.io/v1/tx/hash/{hash}'
        # print(f"getTransactionDetails: {url}")
        res = requests.get(url)
        # print(f"Result: {res.text}")
        return cosmostation_transaction_from_dict(json.loads(res.text))

    async def getTransactionDetailsAsync(self, hash) -> CosmoStationTransactionDetailsAnswer:
        return await asyncio.to_thread(self.getTransactionDetails, hash)

    def getTransactionsList(self, walletAddress, startIndex=0, limit=50) -> List[
        CosmoStationTransactionListAnswerElement]:
        url = f'https://api-osmosis.cosmostation.io/v1/account/txs/{walletAddress}?limit={limit}&from={startIndex}'
        print(f"getTransactionsList : {url}")
        res = requests.get(url)
        return cosmo_station_transaction_list_answer_from_dict(json.loads(res.text))

    async def getAllTransactionsList(self, walletAddress, startId=0, totalRequested=50, onTransactionsFound=None) \
            -> List[CosmoStationTransactionListAnswerElement]:
        global txMaxDownloadPerRequest
        allTransactions = []
        remaining = totalRequested

        while remaining > 0:
            partLimit = txMaxDownloadPerRequest if remaining > txMaxDownloadPerRequest else remaining
            allTransactionsPart = self.getTransactionsList(walletAddress, startId, partLimit)
            allTransactionsPartCount = len(allTransactionsPart)

            print(f"-- {allTransactionsPartCount} fetched")
            if allTransactionsPartCount == 0:
                break

            lasTx = allTransactionsPart[-1]
            startId = lasTx.header.id

            remaining -= allTransactionsPartCount

            currentIds = [tx.header.id for tx in allTransactions]

            for tx in allTransactionsPart:
                if tx.header.id not in currentIds:
                    allTransactions.append(tx)

            if onTransactionsFound is not None:
                await onTransactionsFound(allTransactionsPart)

            print(
                f"-- Total fetched: {len(allTransactions)}, remaining: {remaining}, total requested: {totalRequested}")

        return allTransactions

    async def getTransactionsListAsync(self, walletAddress, startId=0, limit=50) \
            -> List[CosmoStationTransactionListAnswerElement]:
        return await asyncio.to_thread(self.getTransactionsList, walletAddress, startId, limit)

    def getAccountBalance(self, walletAddress) -> CosmoStationBalanceAnswer:
        url = f'https://lcd-osmosis.cosmostation.io/cosmos/bank/v1beta1/balances/{walletAddress}'
        res = requests.get(url)
        return cosmo_station_balance_answer_from_dict(json.loads(res.text))

    async def getAccountBalanceAsync(self, walletAddress) -> CosmoStationBalanceAnswer:
        return await asyncio.to_thread(self.getAccountBalance, walletAddress)

    # async def getLastTransactionsDetailAsync(self, walletAddress):
    #     list = await self.getTransactionsListAsync(walletAddress, 0, 1)
    #     if len(list) > 0 :
    #         txHash= list[O].data.txhash
    #         return await self.getTransactionDetailsAsync(txHash)

    #     return None
