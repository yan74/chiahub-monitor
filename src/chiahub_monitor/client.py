import socket
from pathlib import Path
from typing import Optional, Tuple, List

import aiohttp
from chia.pools.pool_wallet_info import PoolWalletInfo, FARMING_TO_POOL
from chia.rpc.farmer_rpc_client import FarmerRpcClient
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.byte_types import hexstr_to_bytes
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16
from chia.wallet.transaction_record import TransactionRecord


class ChiaClient:

    farmer_rpc_client: Optional[FarmerRpcClient]
    wallet_rpc_client: Optional[WalletRpcClient]
    session: aiohttp.ClientSession

    def __init__(self,
                 wallet_adr, wallet_port,
                 farmer_adr, farmer_port,
                 config_path=DEFAULT_ROOT_PATH,
                 config=None):

        self.config_path = Path(config_path).resolve()
        if config is None:
            config = load_config(self.config_path, "config.yaml")
        self.config = config
        self.wallet_adr = wallet_adr
        self.wallet_port = wallet_port
        self.farmer_adr = farmer_adr
        self.farmer_port = farmer_port
        self.session = aiohttp.ClientSession()

    async def connect(self):

        self.wallet_rpc_client = await WalletRpcClient.create(
            self.wallet_adr, uint16(self.wallet_port), self.config_path, self.config
        )

        self.farmer_rpc_client = await FarmerRpcClient.create(
            self.farmer_adr, uint16(self.farmer_port), self.config_path, self.config
        )

    async def upload(self):
        hostname = socket.gethostname()
        harvesters = await self.farmer_rpc_client.get_harvesters()
        wallets = await self.wallet_rpc_client.get_wallets()
        pool_wallets = filter(lambda w: w['type'] == 9, wallets)

        for wallet in pool_wallets:
            status: Tuple[PoolWalletInfo, List[TransactionRecord]] = await self.wallet_rpc_client.pw_status(wallet['id'])

            if status[0].current.state == FARMING_TO_POOL and status[0].current.pool_url.endswith("chiahub.io"):
                launcher_id = status[0].launcher_id
                puzzle_hash = status[0].p2_singleton_puzzle_hash

                login_link = await self.farmer_rpc_client.get_pool_login_link(launcher_id)

                async with self.session.get(login_link, allow_redirects=False) as response:
                    response.raise_for_status()
                    access_token = response.cookies.get("access_token").value

                print(f"uploading for launcher_id: {launcher_id}")
                msg_harvesters = {}
                for h in harvesters["harvesters"]:
                    if h['connection']['node_id'] not in msg_harvesters:
                        msg_harvesters[h['connection']['node_id']] = {
                            "id": h['connection']['node_id'],
                            "host": h['connection']['host'],
                            "port": h['connection']['port'],
                            "failed_to_open_filenames": h['failed_to_open_filenames'],
                            "no_key_filenames": h['no_key_filenames'],
                            "plots": [],
                        }

                    plots = msg_harvesters[h['connection']['node_id']]['plots']

                    for plot in h['plots']:
                        if hexstr_to_bytes(plot['pool_contract_puzzle_hash']) == puzzle_hash:
                            del plot['pool_public_key']
                            plots.append(plot)

                msg = {
                    "host": self.farmer_adr,
                    "port": self.farmer_port,
                    "harvesters": list(msg_harvesters.values()),
                }
                headers = {"Authorization": f"Bearer {access_token}"}

                if status[0].current.pool_url.startswith("https://pool"):
                    url = f"https://api.chiahub.io/v1/client/{launcher_id.hex()}/{hostname}"
                else:
                    url = f"https://sandbox.chiahub.io/v1/client/{launcher_id.hex()}/{hostname}"

                async with self.session.post(url, json=msg, headers=headers):
                    pass

    async def close(self):
        await self.session.close()
        self.farmer_rpc_client.close()
        self.wallet_rpc_client.close()
        await self.farmer_rpc_client.await_closed()
        await self.wallet_rpc_client.await_closed()