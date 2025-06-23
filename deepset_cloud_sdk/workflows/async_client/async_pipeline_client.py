"""Async pipeline client for importing pipelines and indexes to deepset AI Platform."""

import structlog

from deepset_cloud_sdk._api.config import (
    API_KEY,
    API_URL,
    DEFAULT_WORKSPACE_NAME,
    CommonConfig,
)
from deepset_cloud_sdk._api.deepset_cloud_api import DeepsetCloudAPI
from deepset_cloud_sdk._service.pipeline_service import (
    PipelineProtocol,
    PipelineService,
)
from deepset_cloud_sdk.models import IndexConfig, PipelineConfig

logger = structlog.get_logger(__name__)


# pylint: disable=too-few-public-methods
class AsyncPipelineClient:
    """Async client for importing Haystack pipelines and indexes to deepset AI platform.

    Note:
        When using this client, you need to manage your own event loop.

    Example for importing a Haystack pipeline or index to deepset AI platform:
        ```python
        from deepset_cloud_sdk import (
            AsyncPipelineClient,
            PipelineConfig,
            PipelineInputs,
            PipelineOutputs,
            IndexConfig,
            IndexInputs,
        )
        from haystack import Pipeline

        # Initialize the client with configuration from environment variables (after running `deepset-cloud login`)
        client = AsyncPipelineClient()

        # or initialize the client with explicit configuration
        client = AsyncPipelineClient(
            api_key="your-api-key",
            workspace_name="your-workspace",
            api_url="https://api.cloud.deepset.ai/api/v1"
        )

        # Configure your pipeline
        pipeline = Pipeline()

        # Configure import
        # if importing a pipeline, use PipelineConfig
        config = PipelineConfig(
            name="my-pipeline",
            inputs=PipelineInputs(
                query=["prompt_builder.query"],
                filters=["bm25_retriever.filters", "embedding_retriever.filters"],
            ),
            outputs=PipelineOutputs(
                answers="answers_builder.answers",
                documents="ranker.documents",
            ),
            strict_validation=False,  # Fail on validation errors (default: False, warnings only)
            overwrite=False,  # Overwrite existing pipelines with the same name. If True, creates if it doesn't exist (default: False)
        )

        # if importing an index, use IndexConfig
        config = IndexConfig(
            name="my-index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,  # Fail on validation errors (default: False, warnings only)
            overwrite=False,  # Overwrite existing indexes with the same name. If True, creates if it doesn't exist (default: False)
        )

        # async execution
        await client.import_into_deepset(pipeline, config)
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        workspace_name: str | None = None,
        api_url: str | None = None,
    ) -> None:
        """Initialize the Async Pipeline Client.

        The client can be configured in two ways:

        1. Using environment variables (recommended):
           - Run `deepset-cloud login` to set up the following environment variables:
             - `API_KEY`: Your deepset AI platform API key
             - `API_URL`: The URL of the deepset AI platform API
             - `DEFAULT_WORKSPACE_NAME`: The workspace name to use.

        2. Using explicit parameters:
           - Provide the values directly to this constructor
           - Any missing parameters will fall back to environment variables

        :param api_key: Your deepset AI platform API key. Falls back to `API_KEY` environment variable.
        :param workspace_name: The workspace to use. Falls back to `DEFAULT_WORKSPACE_NAME` environment variable.
        :param api_url: The URL of the deepset AI platform API. Falls back to `API_URL` environment variable.
        :raises ValueError: If no api key or workspace name is provided and `API_KEY` or `DEFAULT_WORKSPACE_NAME` is not set in the environment.
        """
        self._api_config = CommonConfig(
            api_key=api_key or API_KEY,
            api_url=api_url or API_URL,
        )
        self._workspace_name = workspace_name or DEFAULT_WORKSPACE_NAME
        if not self._workspace_name:
            raise ValueError(
                "Workspace not configured. Provide a workspace name or set the `DEFAULT_WORKSPACE_NAME` environment variable."
            )

    async def import_into_deepset(self, pipeline: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Import a Haystack `Pipeline` or `AsyncPipeline` into deepset AI Platform asynchronously.

        The pipeline must be imported as either an index or a pipeline:
        - An index: Processes files and stores them in a document store, making them available for
          pipelines to search.
        - A pipeline: For other use cases, for example, searching through documents stored by index pipelines.

        :param pipeline: The Haystack `Pipeline` or `AsyncPipeline` to import.
        :param config: Configuration for importing, use either `IndexConfig` or `PipelineConfig`.
            If importing an index, the config argument is expected to be of type `IndexConfig`,
            if importing a pipeline, the config argument is expected to be of type `PipelineConfig`.
        """
        async with DeepsetCloudAPI.factory(self._api_config) as api:
            service = PipelineService(api, self._workspace_name)
            await service.import_async(pipeline, config)
