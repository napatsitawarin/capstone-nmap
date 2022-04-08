from http.client import BAD_REQUEST
from fastapi import APIRouter, Body, Response
from app.schemas import Nmap_input
from starlette.responses import JSONResponse
import logging, os
import xmltodict
import re

router = APIRouter()


@router.post("/scan", status_code=200)
def test(req_body: Nmap_input = Body(...)) -> Response:
    url = req_body.url

    if not url:
        return JSONResponse(status_code=400, content={"message": "Invalid Request"})

    url_no_http = re.sub(r"^http[s]?://", "", url)
    output_filename = f"{url_no_http}.xml"
    output_path = f"./reports/{output_filename}"
    if os.path.exists(output_path):
        os.remove(output_path)

    try:

        status = os.system(
            f"/usr/bin/nmap -sV -oX {output_path} {url_no_http} 1>/dev/null 2>/dev/null"
        )
        # status = os.system(f"nmap -sV -oX {output_path} {url} 1>/dev/null 2>/dev/null")
        if status > 0:
            raise Exception(f"Command run fail with status {status}")
        # nmap -T4 -A -v
        # nmap -sV -oX

        result = None
        with open(output_path, "r") as file:
            result = xmltodict.parse(file.read())

        if os.path.exists(output_path):
            os.remove(output_path)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        logging.error(e)
        return JSONResponse(status_code=500, content={"message": "internal error"})
