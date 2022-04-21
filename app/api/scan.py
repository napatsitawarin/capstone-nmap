import io
from typing import List
from fastapi import APIRouter, Body, Response
from fastapi import WebSocket, WebSocketDisconnect
from app.schemas import Nmap_input
from starlette.responses import JSONResponse
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK


import re
import time
import subprocess
import asyncio
import logging
import xmltodict


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


PORT_REGEX = re.compile(r"<port.*?>(.+?)</port>", re.IGNORECASE)
HOST_REGEX = re.compile(r"<hostname\s.*?>", re.IGNORECASE)
ADDRESS_REGEX = re.compile(r"<address.*?>", re.IGNORECASE)

router = APIRouter()
manager = ConnectionManager()


async def _process(websocket: WebSocket, url: str):
    try:
        filename = f"reports/{url}.log"
        cmd = [
            "nmap",
            "--open",
            "-v",
            "-F",  # top 100 ports
            "--host-timeout=10m",
            "-sV",
            "-Pn",
            "-oX",
            "-",
            url,
        ]
        with io.open(filename, "wb") as writer:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
            )

            for line in iter(process.stdout.readline, b""):
                writer.write(line)
                line = line.decode("utf-8")
                print(line, end="")
                if line:
                    if HOST_REGEX.match(line):
                        result = xmltodict.parse(line, xml_attribs=True)
                        await websocket.send_json({"type": "hostname", "data": result})
                    elif ADDRESS_REGEX.match(line):
                        result = xmltodict.parse(line, xml_attribs=True)
                        await websocket.send_json({"type": "address", "data": result})
                    elif PORT_REGEX.match(line):
                        result = xmltodict.parse(line, xml_attribs=True)
                        await websocket.send_json({"type": "port", "data": result})
                    await asyncio.sleep(0.5)

        with open(filename, "rb") as reader:
            final_result = xmltodict.parse(
                reader.read().decode("utf-8"), force_list=("ports", "hostnames")
            )
            await websocket.send_json({"type": "final", "data": final_result})

    except ConnectionClosedOK as e:
        manager.disconnect(websocket)
        await websocket.close()
    except (WebSocketDisconnect, ConnectionClosedError) as e:
        manager.disconnect(websocket)
        await websocket.close(1011)
    finally:
        process.terminate()


@router.websocket("/ws/scan", "websocket-scan")
async def ws_scan(
    websocket: WebSocket,
):
    await manager.connect(websocket)

    request = await websocket.receive_json()
    url = re.sub(r"^http[s]?://", "", request["url"])

    await _process(websocket, url)


@router.post("/scan", status_code=200)
def test(req_body: Nmap_input = Body(...)) -> Response:
    url = req_body.url

    if not url:
        return JSONResponse(status_code=400, content={"message": "Invalid Request"})

    url_no_http = re.sub(r"^http[s]?://", "", url)

    try:
        result = subprocess.check_output(
            f"/usr/bin/nmap -sV -oX - {url_no_http}", shell=True
        )
        result = xmltodict.parse(result.decode("utf-8"))
        # nmap -T4 -A -v
        # nmap -sV -oX

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        logging.error(e)
        return JSONResponse(status_code=500, content={"message": "internal error"})
