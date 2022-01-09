# Basic heartbeat controller
from threading import Thread
import asyncio
from .signals import gateway  # type: ignore


class KeepAlive(Thread):
    def __init__(self, identity, ws, helloPacket: dict):
        self._ws = ws
        self.packet = helloPacket
        self.identity = identity

    async def run(self):
        packet = self.packet

        await self._ws.send_json(self.identity)

        while True:
            if packet["op"] != gateway.HELLO:
                raise ValueError("Invalid hello packet provided")

            await asyncio.sleep((packet["d"]["heartbeat_interval"] / 1000))

            await self._ws.send_json(self.get_payload())

    def get_payload(self):
        return {"op": gateway.HEARTBEAT, "d": gateway.SEQUENCE}
