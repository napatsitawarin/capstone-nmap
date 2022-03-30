from fastapi import APIRouter, Body, Response
from app.schemas import Nmap_input
from starlette.responses import JSONResponse
import logging, os
import xmltodict

router = APIRouter()


@router.post("/scan", status_code=200)
def test(req_body: Nmap_input = Body(...)) -> Response:
    output_filename = "nmap_output.xml"
    output_path = f"./reports/{output_filename}"
    
    try:
        '''
        Remove the old result file
        '''
        if os.path.exists(output_path):
            os.remove(output_path)

        if req_body:
            url = req_body.url
            status = os.system(
                f"nmap -sV -oX {output_path} {url} 1>/dev/null 2>/dev/null"
            )
            if status > 0:
                raise Exception(f"Command run fail with status {status}")
            # nmap -T4 -A -v
            # nmap -sV -oX

            with open(output_path, "r") as file:
                result = xmltodict.parse(file.read())
                return JSONResponse(status_code=200, content=result)

        else:
            return JSONResponse(status_code=400, content={"message": "Invalid Request"})
    except Exception as e:
        logging.error(e)
        return JSONResponse(status_code=400, content={"message": "error"})
