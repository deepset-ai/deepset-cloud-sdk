"""This is the entrypoint for the package."""

import logging

import structlog

from deepset_cloud_sdk._service.pipeline_service import (
    DeepsetValidationError,
    ErrorDetail,
)
from deepset_cloud_sdk.models import (
    BaseConfig,
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
    PipelineOutputType,
)
from deepset_cloud_sdk.workflows.async_client.async_pipeline_client import (
    AsyncPipelineClient,
)
from deepset_cloud_sdk.workflows.sync_client.pipeline_client import PipelineClient

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

log = structlog.get_logger()

__all__ = [
    "AsyncPipelineClient",
    "BaseConfig",
    "ErrorDetail",
    "PipelineClient",
    "PipelineConfig",
    "PipelineInputs",
    "PipelineOutputs",
    "IndexConfig",
    "IndexInputs",
    "IndexOutputs",
    "DeepsetValidationError",
    "PipelineOutputType",
]
