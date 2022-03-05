from fastapi import APIRouter, Body, Response
from app.schemas import Nmap_input
from starlette.responses import JSONResponse
import logging, os

router = APIRouter()

@router.post("/scan", status_code=200)
def test(req_body: Nmap_input = Body(...)) -> Response:
    try:
        if req_body:
            url = req_body.url
            os.system(f"nmap -sV -oX ./reports/nmap_output.xml {url} 1>/dev/null 2>/dev/null")
            # nmap -T4 -A -v
            # nmap -sV -oX
            return JSONResponse(
                status_code = 200,
                content = {
                    "message": "Success",
                },
            )
        else:
            return JSONResponse(
                status_code = 400,
                content = {
                    "message": "Invalid Request"
                }
            )
    except Exception as e:
        logging.error(e)
        return JSONResponse(
            status_code = 400,
            content = {
                "message": "error"
            }
        )
