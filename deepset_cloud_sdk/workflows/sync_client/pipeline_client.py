"""Sync pipeline client for importing pipelines and indexes to deepset AI Platform."""
import asyncio

import structlog

from deepset_cloud_sdk._service.pipeline_service import PipelineProtocol
from deepset_cloud_sdk.models import IndexConfig, PipelineConfig
from deepset_cloud_sdk.workflows.async_client.async_pipeline_client import (
    AsyncPipelineClient,
)

logger = structlog.get_logger(__name__)


class PipelineClient(AsyncPipelineClient):
    """Sync client for importing Haystack pipelines and indexes to deepset AI platform.

    Example for importing a Haystack pipeline or index to deepset AI platform:
        ```python
        from deepset_cloud_sdk import (
            PipelineClient,
            PipelineConfig,
            PipelineInputs,
            PipelineOutputs,
            IndexConfig,
            IndexInputs,
        )
        from haystack import Pipeline

        # Initialize the client with configuration from environment variables (after running `deepset-cloud login`)
        client = PipelineClient()

        # or initialize the client with explicit configuration
        client = PipelineClient(
            api_key="your-api-key",
            workspace_name="your-workspace",
            api_url="https://api.deepset.ai"
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

        # sync execution
        client.import_into_deepset(pipeline, config)
        ```
    """

    def import_into_deepset(self, pipeline: PipelineProtocol, config: IndexConfig | PipelineConfig) -> None:
        """Import a Haystack `Pipeline` or `AsyncPipeline` into deepset AI Platform synchronously.

        The pipeline must be imported as either an index or a pipeline:
        - An index: Processes files and stores them in a document store, making them available for
          pipelines to search.
        - A pipeline: For other use cases, for example, searching through documents stored by index pipelines.

        :param pipeline: The Haystack `Pipeline` or `AsyncPipeline` to import.
        :param config: Configuration for importing into deepset, use either `IndexConfig` or `PipelineConfig`.
            If importing an index, the config argument is expected to be of type `IndexConfig`,
            if importing a pipeline, the config argument is expected to be of type `PipelineConfig`.
        """
        try:
            loop = asyncio.get_event_loop()
            # do not close if event loop already exists, e.g. in Jupyter notebooks
            should_close = False
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            should_close = True

        try:
            return loop.run_until_complete(self.import_into_deepset_async(pipeline, config))
        finally:
            if should_close:
                loop.close()
