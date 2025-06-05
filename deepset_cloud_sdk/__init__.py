"""This is the entrypoint for the package."""


import logging

import structlog

from deepset_cloud_sdk.workflows.pipeline_client import PipelineClient
from deepset_cloud_sdk.workflows.pipeline_client.models import (
    IndexConfig,
    IndexInputs,
    IndexOutputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

log = structlog.get_logger()

__all__ = [
    "PipelineClient",
    "PipelineConfig",
    "PipelineInputs",
    "PipelineOutputs",
    "IndexConfig",
    "IndexInputs",
    "IndexOutputs",
]
