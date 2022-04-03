import asyncio
import traceback

from chiahub_monitor.client import ChiaClient


async def run(client: ChiaClient):

    while True:
        try:
            await client.upload()
        except:
            tb = traceback.format_exc()
            print(f"Error while uploading: {tb}")
        print("sleeping")
        await asyncio.sleep(60 * 60)


if __name__ == '__main__':

    client = ChiaClient(
        wallet_adr="localhost", wallet_port=9256,
        farmer_adr="localhost", farmer_port=8559,
        )

    try:
        asyncio.get_event_loop().run_until_complete(run(client))
    except KeyboardInterrupt:
        pass

    print("closing")
    asyncio.get_event_loop().run_until_complete(client.close())
