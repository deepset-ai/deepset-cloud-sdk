"""Deepset AI platform SDK main class."""
import structlog

from deepset_cloud_sdk.workflows.pipeline_client.pipeline_service import (
    _enable_import_into_deepset,
)

logger = structlog.get_logger(__name__)


class DeepsetSDK:  # pylint: disable=too-few-public-methods
    """Main class for Deepset Cloud SDK functionality.

    This class provides a centralized way to initialize and manage SDK features.

    Example for importing an index or pipeline to deepset AI platform:
        ```python
        from deepset_cloud_sdk.workflows import DeepsetSDK
        from haystack import Pipeline

        # Initialize the SDK to enable using importing functionality
        sdk = DeepsetSDK()
        sdk.init()

        # Configure your pipeline
        pipeline = Pipeline()

        # Configure import
        # if importing an index, use IndexConfig
        config = IndexConfig(
            name="my-index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
        )

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
        )

        # sync execution
        pipeline.import_into_deepset(config)

        # async execution
        await pipeline.import_into_deepset_async(config)
        ```
    """

    def init(self) -> None:
        """Initialize the SDK features.

        This method sets up the SDK for use with Haystack pipelines.
        It enables the import functionality for haystack Pipeline and AsyncPipeline classes.

        Note:
            This method should be called before using any SDK features that require initialization.
        """
        try:
            _enable_import_into_deepset()
            logger.debug("SDK initialized successfully.")
        except ImportError as err:
            logger.error(f"Failed to initialize SDK: {str(err)}.")
            raise
