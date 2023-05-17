"""This is the entrypoint for the package."""


import logging

import structlog

from deepset_cloud_sdk.workflows import async_client, sync_client

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

log = structlog.get_logger()
