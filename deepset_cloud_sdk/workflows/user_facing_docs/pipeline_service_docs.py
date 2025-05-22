"""Documentation strings for the pipeline service module.

This module contains all user-facing documentation strings used in the pipeline service,
including error messages, field descriptions, and validation messages.
"""

class PipelineServiceDocs:
    """Documentation for the PipelineService class."""

    PIPELINE_QUERY_INPUTS_DESCRIPTION = (
        "List of component names that will receive the query input when being executed. "
        "Mandatory for query pipelines. "
        "Format: '<component-name>.<run-parameter-name>', e.g., 'retriever.query'"
    )
    PIPELINE_FILTERS_INPUTS_DESCRIPTION = (
        "List of component names that will receive filters input when being executed. "
        "Format: '<component-name>.<run-parameter-name>', e.g., 'retriever.filters'"
    )
    INDEX_FILES_INPUTS_DESCRIPTION = (
        "List of component names that will receive files as input when being executed. "
        "Mandatory for index pipelines. "
        "Format: '<component-name>.<run-parameter-name>', e.g., 'file_type_router.sources'"
    )

    PUBLISH_CONFIG_NAME_DESCRIPTION = "Name of the pipeline or index to be published"
    PUBLISH_CONFIG_PIPELINE_TYPE_DESCRIPTION = "Type of the pipeline (pipeline or index)"
    PUBLISH_CONFIG_INPUTS_DESCRIPTION = "Input configuration for the pipeline or index"

    VALIDATION_ERROR_FILES_INPUT_REQUIRED = (
        "Indexes must define components expecting files as input when being executed at run time. "
        "Add a list of all components receiving files as input to the 'inputs.files' parameter of "
        "'PublishConfig', e.g. ['<component name>.<run parameter name>', ...]."
    )

    VALIDATION_ERROR_QUERY_INPUT_REQUIRED = (
        "Query pipelines must define components expecting a query as input when being executed at run time. "
        "Add a list of all components receiving a query as input to the 'inputs.query' parameter of "
        "'PublishConfig', e.g. ['<component name>.<run parameter name>', ...]."
    )

    VALIDATION_ERROR_OUTPUTS_REQUIRED = (
        "Query pipelines must define at least one output (documents or answers). "
        "Add the name of the component you expect to receive outputs from to the 'outputs.documents' "
        "and/or 'outputs.answers' parameter of 'PublishConfig', "
        "e.g. '<component name>.<output parameter name>'."
    )
    WORKSPACE_REQUIRED_ERROR = (
        "We couldn't find the workspace to publish to in your environment. "
        "Please run 'deepset-cloud login' and follow the instructions."
    )
    INVALID_PIPELINE_TYPE_ERROR = (
        "Haystack Pipeline or AsyncPipeline object expected. "
        "Make sure you have installed haystack-ai and use Pipeline or AsyncPipeline "
        "to define your pipeline."
    )
