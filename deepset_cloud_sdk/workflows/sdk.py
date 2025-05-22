"""Deepset Cloud SDK main class."""
import structlog

from deepset_cloud_sdk.workflows.pipeline_client.pipeline_service import (
    _enable_publish_to_deepset,
)

logger = structlog.get_logger(__name__)


class DeepsetSDK:
    """Main class for Deepset Cloud SDK functionality.

    This class provides a centralized way to initialize and manage SDK features.

    Example:
        ```python
        from deepset_cloud_sdk.workflows import DeepsetSDK
        from haystack import Pipeline

        # Initialize the SDK
        sdk = DeepsetSDK()
        sdk.init()

        # Now you can use the publish functionality
        pipeline = Pipeline()
        # ... configure your pipeline ...
        await pipeline.publish(config)
        ```
    """

    def __init__(self) -> None:
        """Initialize the DeepsetSDK instance."""
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if the SDK has been initialized.

        :return: True if the SDK has been initialized, False otherwise
        """
        return self._initialized

    def init(self) -> None:
        """Initialize the SDK features.

        This method sets up the SDK for use with haystack pipelines.
        It enables the publish functionality for haystack Pipeline and AsyncPipeline classes.

        Note:
            This method should be called before using any SDK features that require initialization.
        """
        if self._initialized:
            logger.debug("SDK already initialized")
            return

        try:
            _enable_publish_to_deepset()
            self._initialized = True
            logger.debug("SDK initialized successfully")
        except ImportError as err:
            logger.error(f"Failed to initialize SDK: {str(err)}")
            self._initialized = False
