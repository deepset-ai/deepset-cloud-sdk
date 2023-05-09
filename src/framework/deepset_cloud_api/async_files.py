import asyncio
from dataclasses import dataclass
from itertools import chain
import os
from typing import List, Optional, Tuple
import aiohttp
import httpx
from httpx import HTTPError

from httpx import Response
from framework.deepset_cloud_api.config import CommonConfig

from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed, retry_if_exception_type, wait_random_exponential
import urllib.parse

import structlog
from framework.deepset_cloud_api.files import Files

import re 

from progress.bar import PixelBar  # type: ignore

class ProgressBar(PixelBar):
    suffix = "%(index)d/%(max)d elapsed: %(elapsed_minutes)s"

    @property
    def elapsed_minutes(self):
        return f"{int(self.elapsed/60)}m{self.elapsed%60}s"


logger = structlog.get_logger()
DEFAULT_WORKSPACE = "default"
logger.bind(source=__name__)

@dataclass
class UploadFile:
    name: str
    metadata_path: str
    content_path: bytes
    metadata_url: str
    content_url:str
    session_id: str

    def transformed_name(self):
        # characters to avoid: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
        transformed = re.sub('[#%\"\|<>\{\}`\^\[\]~ \x00\x08\x0B\x0C\x0E-\x1F]', '_', self.name)
        return urllib.parse.quote_plus(transformed)

@dataclass
class UploadFileResult:
    file: str
    upload_name:str
    meta: bool = False
    error: Optional[str] = None
    skipped: Optional[bool] =False

@dataclass 
class SessionDetails:
    session_id:str
    pending:int
    failed:int
    finished:int

class CouldNotCreateSessionsException(Exception):
    pass


class AsyncFiles(Files):
    def __init__(self, config: CommonConfig, concurrency:int = 100):
        super().__init__(config=config)
        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        }
        self.config = config
        self.sessions_url = (
            lambda workspace_name: f"{config.api_url}/workspaces/{workspace_name}/upload_sessions"
        )

        self.client = httpx.AsyncClient(            
            limits=httpx.Limits(
            max_keepalive_connections=concurrency, max_connections=concurrency
        ))
        self.client_session = aiohttp.ClientSession()

        self.semaphore = asyncio.Semaphore(concurrency)

    @retry(  # type: ignore
        retry=retry_if_exception_type(HTTPError),
        wait=wait_exponential(multiplier=2, min = 1, max = 120),
        stop=stop_after_attempt(10),
        reraise=True
    )
    async def _create_session(self, workspace_name):

        try:
                response = await self.client.post(
                            self.sessions_url(workspace_name),
                            headers=self.headers,
                            timeout=180,
                        )
                response.raise_for_status()
                self.validate_responses([response])
                session_id = response.json()["session_id"]

                return session_id

        except HTTPError as e:
            logger.error("Could not create session")
            raise

    def validate_responses(self, responses:List[Response]) -> None:
        for response in responses:
            try:
                response.raise_for_status()
            except HTTPError:
                logger.error("Could not create sessions for all files, please try again")

                raise CouldNotCreateSessionsException()

    async def upload(
        self, workspace_name: str, files: List[UploadFile], session_limit=10_000
    ) -> Tuple[List[UploadFile], List[str]]:
        # this method modifies and returns the files argument
        chunks = []

        logger.info("Creating sessions", session_size=session_limit, number_of_sessions=len(chunks))
        sessionBar = ProgressBar("Creating sessions", max=len(chunks))
        sessionBar.start()
        upload_bar = ProgressBar(
            f"Presigned URL uploads::workspace={workspace_name}",
            max=len(files),
        ) 
        upload_bar.start()

        session_id = self._create_session(workspace_name)
        logger.info("Created Session", session_id=session_id)

        uploadResults = []
        tasks = []


        tasks.append(self._upload_with_metadata_async(workspace_name, bar=upload_bar))
        
        results = await asyncio.gather(*tasks)
        [uploadResults.extend(result) for result in results]
        
        print("") # required to make the loading bars and logs look nice
        sessionBar.finish()
        upload_bar.finish()
        await self.client_session.close()
        return (uploadResults)


    async def get_session(self, workspace, session_id:str) -> SessionDetails:
        try:
            # the below line gets called from a lambda function that is run from outside
            # this file. For some reason I have not uncovered using the async httpx client here does
            # not work, so decided to go with sync. async capability isn't important for this 
            # specific call anyway.
            response = httpx.get(f"{self.sessions_url(workspace)}/{session_id}", headers=self.headers)
            response.raise_for_status()
        except:
            return SessionDetails(None, None, None, None)
        
        response_json = response.json()

        return SessionDetails(
            session_id=response_json["session_id"],
            failed=response_json["ingestion_status"]["failed_files"],
            pending=response_json["ingestion_status"]["pending_files"],
            finished=response_json["ingestion_status"]["finished_files"]
        )

    async def wait_until_session_completes(self,workspace, session_id:str, total_uploaded):
        logger.info("Checking ingestion status for workspace", workspace=workspace)
        bar = ProgressBar(f"File Ingestion Status::workspace={workspace}", max=total_uploaded)
        bar.start()
        current_complete = 0

        while (current_complete < total_uploaded):
            await asyncio.sleep(5)
            result:SessionDetails = await self.get_session(workspace, session_id)

            finished_total = result.finished if result.finished != None else 0
            failed_total = result.failed if result.failed != None else 0
            new_total = finished_total+failed_total
            
            for _ in range(0, new_total-current_complete):
                current_complete += 1
                bar.next()
            bar.update()

        bar.finish()
        logger.info("Ingestion for workspace is complete", workspace=workspace)

    @retry(  # type: ignore
        retry=retry_if_exception_type(HTTPError),
        stop=stop_after_attempt(3),
        wait = wait_fixed(0.5)

    )
    async def _upload_part_async(self, transformed_name, filename, filepath, upload_url):
        # url_safe_name = urllib.parse.quote(transformed_name, safe="")
        if transformed_name not in upload_url:
            return UploadFileResult(
                file=filename, upload_name=transformed_name, error=f"file does not match the name {urllib.parse.quote(upload_url, safe='')}"
            )

        try:
            length = os.stat(filepath).st_size
            with open(filepath, "rb") as upload_file:
                file_contents = upload_file.read()
                async with self.client_session.put(
                    upload_url,
                    data=file_contents,
                    headers={"content-length": str(length)}
                ) as response:
                    response.raise_for_status()
        except Exception as e:
            raise e

        return UploadFileResult(file=filename, upload_name=transformed_name)


    async def _upload_file_and_metadata_async(self, file: UploadFile, bar:ProgressBar) -> List[UploadFileResult]:
        r1:UploadFileResult = None
        r2:UploadFileResult = None

        
        async with self.semaphore:
                
            try:
                r1 = await self._upload_part_async(transformed_name=file.transformed_name(), filename=f"{file.name}.meta.json", filepath=file.metadata_path, upload_url=file.metadata_url)
                r1.meta = True
            except Exception as e:
                error_message = str(e)[:100]
                if hasattr(e, "message"):
                    error_message = e
                r1 = UploadFileResult(f"{file.name}.meta.json", upload_name=file.transformed_name(), error=e, meta=True)
           
            try:            
                r2 = await self._upload_part_async(transformed_name=file.transformed_name(), filename=f"{file.name}", filepath=file.content_path, upload_url=file.content_url)
                r2.meta = False
            except Exception as e:
                error_message = f""
                if hasattr(e, "message"):
                    error_message = e.message

                r2 = UploadFileResult(file.name, upload_name=file.transformed_name(), error=error_message, meta=False)
        
        bar.next()
        return [r1, r2]

    async def _upload_with_metadata_async(self, workspace:str, files: List[UploadFile], bar=None) -> List[UploadFileResult]:
        logger.info("Starting File Uploads to presigned S3 URLs ")
        tasks = []

        if bar == None:
            bar = ProgressBar(
                f"Presigned URL uploads::workspace={workspace}",
                max=len(files),
            ) 
        

        results = await asyncio.gather(*[
            self._upload_file_and_metadata_async(file, bar) for file in files
        ])
        return list(chain.from_iterable(results))


