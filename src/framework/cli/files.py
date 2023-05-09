import typer
from framework.deepset_cloud_api.config import CommonConfig
from framework.deepset_cloud_api.files import Files
from framework.cli.async_file_upload_only import setup
from httpx import Response
import structlog
logger = structlog.get_logger()

app = typer.Typer()

@app.command()
def count(count:bool=typer.Argument(False), workspace:str=typer.Option(...), api_key:str=typer.Option(...), url=typer.Option("https://api.cloud.deepset.ai/api/v1") ):
    config = CommonConfig(api_url=url, api_key=api_key)
    files = Files(config)
    response:Response = files.list(workspace_name=workspace)

    try:
        response.raise_for_status()
    except:
        logger.warn("Got an unsuccessful response from the API", status=response.status, content=response.content)
        raise
    
    count = response.json().get("total")
    print(count)

@app.command()
def upload(datapath:str=typer.Option(...), workspace:str=typer.Option(...), api_key:str=typer.Option(...), url=typer.Option("https://api.cloud.deepset.ai/api/v1"), concurrency:int=typer.Option(120, min=1), ignore_ingestion:bool=typer.Option(False, "--ignore-ingestion")):
    setup(datapath, workspace, api_key, url, concurrency, ignore_ingestion)

