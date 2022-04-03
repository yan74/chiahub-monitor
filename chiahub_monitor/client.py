import os
import socket
import ssl
import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any

import aiohttp
import yaml

DEFAULT_ROOT_PATH = Path(os.path.expanduser(os.getenv("CHIA_ROOT", "~/.chia/mainnet"))).resolve()
FARMING_TO_POOL = 3


def config_path_for_filename(root_path: Path, filename: Union[str, Path]) -> Path:
    path_filename = Path(filename)
    if path_filename.is_absolute():
        return path_filename
    return root_path / "config" / filename


def hexstr_to_bytes(input_str: str) -> bytes:
    """
    Converts a hex string into bytes, removing the 0x if it's present.
    """
    if input_str.startswith("0x") or input_str.startswith("0X"):
        return bytes.fromhex(input_str[2:])
    return bytes.fromhex(input_str)


def load_config(
    root_path: Path,
    filename: Union[str, Path],
    sub_config: Optional[str] = None,
    exit_on_error=True,
) -> Dict:
    path = config_path_for_filename(root_path, filename)
    if not path.is_file():
        if not exit_on_error:
            raise ValueError("Config not found")
        print(f"can't find {path}")
        print("** please run `chia init` to migrate or create new config files **")
        # TODO: fix this hack
        sys.exit(-1)
    r = yaml.safe_load(open(path, "r"))
    if sub_config is not None:
        r = r.get(sub_config)
    return r


def ssl_context_for_client(
    ca_cert: Path,
    ca_key: Path,
    private_cert_path: Path,
    private_key_path: Path,
) -> Optional[ssl.SSLContext]:

    ssl_context = ssl._create_unverified_context(purpose=ssl.Purpose.SERVER_AUTH, cafile=str(ca_cert))
    ssl_context.check_hostname = False
    ssl_context.load_cert_chain(certfile=str(private_cert_path), keyfile=str(private_key_path))
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    return ssl_context


def private_ssl_ca_paths(path: Path, config: Dict):
    return (
        path / config["private_ssl_ca"]["crt"],
        path / config["private_ssl_ca"]["key"],
    )


class ChiaClient:

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
        self.wallet_url = f"https://{wallet_adr}:{str(wallet_port)}/"
        self.farmer_url = f"https://{farmer_adr}:{str(farmer_port)}/"
        ca_crt_path, ca_key_path = private_ssl_ca_paths(self.config_path, self.config)
        crt_path = self.config_path / self.config["daemon_ssl"]["private_crt"]
        key_path = self.config_path / self.config["daemon_ssl"]["private_key"]
        self.ssl_context = ssl_context_for_client(ca_crt_path, ca_key_path, crt_path, key_path)

    async def upload(self):
        hostname = socket.gethostname()
        harvesters = await self.get_harvesters()
        wallets = await self.get_wallets()
        pool_wallets = filter(lambda w: w['type'] == 9, wallets)

        for wallet in pool_wallets:
            status = await self.pw_status(wallet['id'])

            if status["current"]["state"] == FARMING_TO_POOL and status["current"]["pool_url"].endswith("chiahub.io"):
                launcher_id = hexstr_to_bytes(status["launcher_id"])
                puzzle_hash = hexstr_to_bytes(status["p2_singleton_puzzle_hash"])

                login_link = await self.get_pool_login_link(launcher_id)

                async with self.session.get(login_link, allow_redirects=False) as response:
                    response.raise_for_status()
                    access_token = response.cookies.get("access_token").value

                print(f"uploading for launcher_id: {launcher_id.hex()}")
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
                        if plot['pool_contract_puzzle_hash']:
                            if hexstr_to_bytes(plot['pool_contract_puzzle_hash']) == puzzle_hash:
                                del plot['pool_public_key']
                                plots.append(plot)

                msg = {
                    "host": self.farmer_adr,
                    "port": self.farmer_port,
                    "harvesters": list(msg_harvesters.values()),
                }
                headers = {"Authorization": f"Bearer {access_token}"}

                if status["current"]["pool_url"].startswith("https://pool"):
                    url = f"https://api.chiahub.io/v1/client/{launcher_id.hex()}/{hostname}"
                else:
                    url = f"https://sandbox.chiahub.io/v1/client/{launcher_id.hex()}/{hostname}"

                async with self.session.post(url, json=msg, headers=headers):
                    pass

    async def get_harvesters(self) -> Dict[str, Any]:
        return await self.fetch_farmer("get_harvesters", {})

    async def get_wallets(self) -> Dict:
        return (await self.fetch_wallet("get_wallets", {}))["wallets"]

    async def pw_status(self, wallet_id: str) -> Dict:
        return (await self.fetch_wallet("pw_status", {"wallet_id": wallet_id}))["state"]

    async def get_pool_login_link(self, launcher_id: bytes) -> Optional[str]:
        try:
            return (await self.fetch_farmer("get_pool_login_link", {"launcher_id": launcher_id.hex()}))["login_link"]
        except ValueError:
            return None

    async def fetch_farmer(self, path, request_json) -> Any:
        async with self.session.post(self.farmer_url + path, json=request_json, ssl_context=self.ssl_context) as response:
            response.raise_for_status()
            res_json = await response.json()
            if not res_json["success"]:
                raise ValueError(res_json)
            return res_json

    async def fetch_wallet(self, path, request_json) -> Any:
        async with self.session.post(self.wallet_url + path, json=request_json, ssl_context=self.ssl_context) as response:
            response.raise_for_status()
            res_json = await response.json()
            if not res_json["success"]:
                raise ValueError(res_json)
            return res_json

    async def close(self):
        await self.session.close()
