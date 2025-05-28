"""Deepset AI platform SDK main class."""
import structlog

from deepset_cloud_sdk._api.config import (
    API_KEY,
    API_URL,
    DEFAULT_WORKSPACE_NAME,
    CommonConfig,
)
from deepset_cloud_sdk.workflows.pipeline_client.pipeline_service import (
    _enable_import_into_deepset,
)

logger = structlog.get_logger(__name__)


class DeepsetSDK:  # pylint: disable=too-few-public-methods
    """Main class for Deepset AI Platform SDK functionality.

    This class provides a centralized way to initialize and manage SDK features.

    Example for importing an Haystack index or pipeline to deepset AI platform:
        ```python
        from deepset_cloud_sdk.workflows import DeepsetSDK
        from haystack import Pipeline

        # Initialize the SDK with configuration from environment variables (after running `deepset-cloud login`)
        sdk = DeepsetSDK()

        # or initialize the SDK with custom configuration
        sdk = DeepsetSDK(
            api_key="your-api-key",
            workspace_name="your-workspace",
            api_url="https://api.deepset.ai"
        )

        # Initialize the SDK features
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

    def __init__(
        self,
        api_key: str | None = None,
        workspace_name: str | None = None,
        api_url: str | None = None,
    ) -> None:
        """Initialize the Deepset SDK.

        The SDK can be configured in two ways:

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
        :raises ValueError: If no workspace name is provided and `DEFAULT_WORKSPACE_NAME` is not set.
        """
        self._config = CommonConfig(
            api_key=api_key or API_KEY,
            api_url=api_url or API_URL,
        )
        self._workspace_name = workspace_name or DEFAULT_WORKSPACE_NAME
        if not self._workspace_name:
            raise ValueError(
                "Workspace not configured. Provide a workspace name or set the `DEFAULT_WORKSPACE_NAME` environment variable."
            )

    def init(self) -> None:
        """Initialize the SDK features.

        This method sets up the SDK for use with Haystack pipelines.
        It enables the import functionality for Haystack Pipeline and AsyncPipeline classes.

        Note:
            This method should be called before using any SDK features that require initialization.
        """
        try:
            _enable_import_into_deepset(self._config, self._workspace_name)
            logger.debug("SDK initialized successfully.")
        except ImportError as err:
            logger.error(f"Failed to initialize SDK: {str(err)}.")
            raise
