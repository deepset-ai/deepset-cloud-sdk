"""This is the entrypoint for the package."""


import logging

import structlog

from deepset_cloud_sdk.workflows.pipeline_client import PipelineClient
from deepset_cloud_sdk.workflows.pipeline_client.models import (
    BaseConfig,
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
    PipelineOutputType,
)
from deepset_cloud_sdk.workflows.pipeline_client.pipeline_service import (
    DeepsetValidationError,
    ErrorDetail,
)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

log = structlog.get_logger()

__all__ = [
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
