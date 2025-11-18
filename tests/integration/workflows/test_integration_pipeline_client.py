"""Integration tests for importing Haystack pipelines into deepset AI Platform."""

import json
import uuid
from datetime import timedelta
from http import HTTPStatus
from typing import NamedTuple, Type, Union

import httpx
import pytest
import respx
import tenacity
from haystack import AsyncPipeline, Pipeline
from haystack.components.builders.answer_builder import AnswerBuilder
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.converters.txt import TextFileToDocument
from haystack.components.embedders.sentence_transformers_document_embedder import (
    SentenceTransformersDocumentEmbedder,
)
from haystack.components.generators.openai import OpenAIGenerator
from haystack.components.routers.file_type_router import FileTypeRouter
from haystack.utils import Secret
from httpx import Response

from deepset_cloud_sdk._api.config import CommonConfig
from deepset_cloud_sdk._service.pipeline_service import DeepsetValidationError
from deepset_cloud_sdk.models import (
    IndexConfig,
    IndexInputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)
from deepset_cloud_sdk.workflows.async_client.async_pipeline_client import (
    AsyncPipelineClient,
)
from deepset_cloud_sdk.workflows.sync_client.pipeline_client import PipelineClient


class MockRoutes(NamedTuple):
    """Container for mocked API routes."""

    validation: respx.Route
    import_: respx.Route


@pytest.fixture
def test_client() -> PipelineClient:
    """Create a test client with standard test configuration."""
    return PipelineClient(api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace")


@pytest.fixture
def test_async_client() -> AsyncPipelineClient:
    """Create a test client with standard test configuration."""
    return AsyncPipelineClient(
        api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace"
    )


@pytest.fixture
def index_import_routes() -> MockRoutes:
    """Create mock routes for index import (validation + index endpoints)."""
    validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
        return_value=Response(status_code=HTTPStatus.NO_CONTENT)
    )
    import_route = respx.post("https://test-api-url.com/workspaces/test-workspace/indexes").mock(
        return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-index-id"})
    )
    return MockRoutes(validation=validation_route, import_=import_route)


@pytest.fixture
def pipeline_import_routes() -> MockRoutes:
    """Create mock routes for pipeline import (validation + pipeline endpoints)."""
    validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
        return_value=Response(status_code=HTTPStatus.NO_CONTENT)
    )
    import_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipelines").mock(
        return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-pipeline-id"})
    )
    return MockRoutes(validation=validation_route, import_=import_route)


def assert_both_endpoints_called_with_auth(
    routes: MockRoutes, expected_name: str, yaml_key: str, expected_yaml_start: str
) -> None:
    """Assert that both validation and import endpoints were called with correct auth and content."""
    # Verify both endpoints were called
    assert routes.validation.called
    assert routes.import_.called

    # Check validation request
    validation_request = routes.validation.calls[0].request
    assert validation_request.headers["Authorization"] == "Bearer test-api-key"
    validation_body = json.loads(validation_request.content)
    assert validation_body["name"] == expected_name

    # Check import request
    import_request = routes.import_.calls[0].request
    assert import_request.headers["Authorization"] == "Bearer test-api-key"
    import_body = json.loads(import_request.content)
    assert import_body["name"] == expected_name
    assert import_body[yaml_key].startswith(expected_yaml_start)


def assert_index_exists(integration_config: CommonConfig, workspace_name: str, index_name: str) -> dict:
    """Assert that an index exists in deepset AI Platform."""
    for attempt in tenacity.Retrying(
        stop=tenacity.stop_after_delay(120),
        wait=tenacity.wait_fixed(wait=timedelta(seconds=1)),
        reraise=True,
    ):
        with attempt:
            response = httpx.get(
                f"{integration_config.api_url}/workspaces/{workspace_name}/indexes/{index_name}",
                headers={"Authorization": f"Bearer {integration_config.api_key}"},
            )
            assert response.status_code == HTTPStatus.OK, f"Failed to get index {index_name}"
            index_data: dict = response.json()
            assert index_data["name"] == index_name

    return index_data


def assert_pipeline_exists(integration_config: CommonConfig, workspace_name: str, pipeline_name: str) -> None:
    """Assert that a pipeline exists in deepset AI Platform."""
    for attempt in tenacity.Retrying(
        stop=tenacity.stop_after_delay(120),
        wait=tenacity.wait_fixed(wait=timedelta(seconds=1)),
        reraise=True,
    ):
        with attempt:
            response = httpx.get(
                f"{integration_config.api_url}/workspaces/{workspace_name}/pipelines/{pipeline_name}",
                headers={"Authorization": f"Bearer {integration_config.api_key}"},
            )
            assert response.status_code == HTTPStatus.OK, f"Failed to get pipeline {pipeline_name}."
            pipeline_data = response.json()
            assert pipeline_data["name"] == pipeline_name


def remove_index(integration_config: CommonConfig, workspace_name: str, index_name: str) -> None:
    """Remove an index from deepset AI Platform."""
    for attempt in tenacity.Retrying(
        stop=tenacity.stop_after_delay(60),
        wait=tenacity.wait_fixed(wait=timedelta(seconds=1)),
        reraise=True,
    ):
        with attempt:
            delete_response = httpx.delete(
                f"{integration_config.api_url}/workspaces/{workspace_name}/indexes/{index_name}",
                headers={"Authorization": f"Bearer {integration_config.api_key}"},
            )
            assert delete_response.status_code in (HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND)


def remove_pipeline(integration_config: CommonConfig, workspace_name: str, pipeline_name: str) -> None:
    """Remove a pipeline from deepset AI Platform."""
    for attempt in tenacity.Retrying(
        stop=tenacity.stop_after_delay(60),
        wait=tenacity.wait_fixed(wait=timedelta(seconds=1)),
        reraise=True,
    ):
        with attempt:
            delete_response = httpx.delete(
                f"{integration_config.api_url}/workspaces/{workspace_name}/pipelines/{pipeline_name}",
                headers={"Authorization": f"Bearer {integration_config.api_key}"},
            )
            assert delete_response.status_code in (HTTPStatus.OK, HTTPStatus.NOT_FOUND)


@pytest.mark.parametrize("pipeline_class", [Pipeline, AsyncPipeline])
class TestImportIndexIntoDeepset:
    @pytest.fixture
    def sample_index(self, pipeline_class: Type[Union[Pipeline, AsyncPipeline]]) -> Union[Pipeline, AsyncPipeline]:
        """Create a simple index for testing."""
        file_type_router = FileTypeRouter(mime_types=["text/plain"])
        text_converter = TextFileToDocument(encoding="utf-8")
        document_embedder = SentenceTransformersDocumentEmbedder(normalize_embeddings=True, model="intfloat/e5-base-v2")

        # Create and configure pipeline
        index = pipeline_class()

        # Add components
        index.add_component("file_type_router", file_type_router)
        index.add_component("text_converter", text_converter)
        index.add_component("document_embedder", document_embedder)

        # Connect components
        index.connect("file_type_router.text/plain", "text_converter.sources")
        index.connect("text_converter.documents", "document_embedder.documents")

        return index

    @respx.mock
    def test_import_index_into_deepset(
        self, sample_index: Pipeline, test_client: PipelineClient, index_import_routes: MockRoutes
    ) -> None:
        """Test synchronously importing an index into deepset."""
        index_config = IndexConfig(
            name="test-index",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
        )

        test_client.import_into_deepset(sample_index, index_config)

        assert_both_endpoints_called_with_auth(
            index_import_routes, "test-index", "config_yaml", "components:\n  document_embedder:\n"
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_index_into_deepset_async(
        self, sample_index: Pipeline, test_async_client: AsyncPipelineClient, index_import_routes: MockRoutes
    ) -> None:
        """Test asynchronously importing an index into deepset."""
        index_config = IndexConfig(
            name="test-index-async",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
        )

        await test_async_client.import_into_deepset(sample_index, index_config)

        assert_both_endpoints_called_with_auth(
            index_import_routes, "test-index-async", "config_yaml", "components:\n  document_embedder:\n"
        )

    @respx.mock
    def test_import_index_into_deepset_with_validation(
        self, sample_index: Pipeline, test_client: PipelineClient, index_import_routes: MockRoutes
    ) -> None:
        """Test synchronously importing an index into deepset with validation enabled."""
        index_config = IndexConfig(
            name="test-index-with-validation",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=True,
        )

        test_client.import_into_deepset(sample_index, index_config)

        # Verify both endpoints were called
        assert index_import_routes.validation.called
        assert index_import_routes.import_.called
        assert len(index_import_routes.validation.calls) == 1
        assert len(index_import_routes.import_.calls) == 1

        assert_both_endpoints_called_with_auth(
            index_import_routes, "test-index-with-validation", "config_yaml", "components:\n  document_embedder:\n"
        )

    @respx.mock
    def test_import_index_validation_failure_blocks_import(
        self, sample_index: Pipeline, test_client: PipelineClient
    ) -> None:
        """Test that validation failure with strict_validation=True prevents import call."""
        # Mock validation failure response
        validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
            return_value=Response(
                status_code=HTTPStatus.BAD_REQUEST,
                json={"details": [{"code": "INVALID_COMPONENT", "message": "Component 'invalid_component' not found"}]},
            )
        )

        # Mock import route (should never be called)
        import_route = respx.post("https://test-api-url.com/workspaces/test-workspace/indexes").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-index-id"})
        )

        index_config = IndexConfig(
            name="test-index-validation-failure",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=True,  # Should fail on validation errors
        )

        # Import should fail with validation error
        with pytest.raises(DeepsetValidationError):
            test_client.import_into_deepset(sample_index, index_config)

        # Verify only validation endpoint was called, NOT import
        assert validation_route.called
        assert not import_route.called  # This is the key assertion
        assert len(validation_route.calls) == 1
        assert len(import_route.calls) == 0

    @respx.mock
    def test_import_index_with_overwrite_fallback_to_create(
        self, sample_index: Pipeline, test_client: PipelineClient
    ) -> None:
        """Test overwriting an index that doesn't exist, falling back to creation."""
        # Mock validation success
        validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
            return_value=Response(status_code=HTTPStatus.NO_CONTENT)
        )

        # Mock 404 response for PATCH (resource not found)
        overwrite_route = respx.patch(
            "https://test-api-url.com/workspaces/test-workspace/indexes/test-index-fallback"
        ).mock(return_value=Response(status_code=HTTPStatus.NOT_FOUND))

        # Mock successful creation
        create_route = respx.post("https://test-api-url.com/workspaces/test-workspace/indexes").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-index-id"})
        )
        index_config = IndexConfig(
            name="test-index-fallback",
            inputs=IndexInputs(files=["file_type_router.sources"]),
            strict_validation=False,
            overwrite=True,
        )

        test_client.import_into_deepset(sample_index, index_config)

        # Verify all three endpoints were called in sequence
        assert validation_route.called
        assert overwrite_route.called
        assert create_route.called

        # Check validation request
        validation_request = validation_route.calls[0].request
        assert validation_request.headers["Authorization"] == "Bearer test-api-key"
        validation_body = json.loads(validation_request.content)
        assert "indexing_yaml" in validation_body

        # Check PATCH attempt
        overwrite_request = overwrite_route.calls[0].request
        assert overwrite_request.headers["Authorization"] == "Bearer test-api-key"
        overwrite_body = json.loads(overwrite_request.content)
        assert "config_yaml" in overwrite_body

        # Check fallback creation
        create_request = create_route.calls[0].request
        assert create_request.headers["Authorization"] == "Bearer test-api-key"
        create_body = json.loads(create_request.content)
        assert create_body["name"] == "test-index-fallback"
        assert "config_yaml" in create_body


@pytest.mark.parametrize("pipeline_class", [Pipeline, AsyncPipeline])
class TestImportPipelineIntoDeepset:
    @pytest.fixture
    def sample_pipeline(
        self, pipeline_class: Type[Union[Pipeline, AsyncPipeline]], monkeypatch: pytest.MonkeyPatch
    ) -> Union[Pipeline, AsyncPipeline]:
        """Create a sample pipeline for testing."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")

        # Initialize components
        prompt_builder = PromptBuilder(
            template="""You are a technical expert.
                You summary should be no longer than five sentences.
                Passage: {{ question }}
                Your summary: """,
            required_variables=["*"],
        )

        llm = OpenAIGenerator(api_key=Secret.from_env_var("OPENAI_API_KEY", strict=False), model="gpt-4")

        answer_builder = AnswerBuilder()

        # Create and configure pipeline
        pipeline = pipeline_class()

        # Add components
        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("llm", llm)
        pipeline.add_component("answer_builder", answer_builder)

        # Connect components
        pipeline.connect("prompt_builder.prompt", "llm.prompt")
        pipeline.connect("llm.replies", "answer_builder.replies")

        return pipeline

    @respx.mock
    def test_import_pipeline_into_deepset(
        self, sample_pipeline: Pipeline, test_client: PipelineClient, pipeline_import_routes: MockRoutes
    ) -> None:
        """Test synchronously importing a pipeline into deepset AI Platform."""
        pipeline_config = PipelineConfig(
            name="test-pipeline",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            strict_validation=False,
        )
        test_client.import_into_deepset(sample_pipeline, pipeline_config)

        assert_both_endpoints_called_with_auth(
            pipeline_import_routes,
            "test-pipeline",
            "query_yaml",
            "components:\n  answer_builder:\n    init_parameters:\n",
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_pipeline_into_deepset_async(
        self, sample_pipeline: Pipeline, test_async_client: AsyncPipelineClient, pipeline_import_routes: MockRoutes
    ) -> None:
        """Test asynchronously importing a pipeline into deepset."""
        pipeline_config = PipelineConfig(
            name="test-pipeline",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            strict_validation=False,
        )
        await test_async_client.import_into_deepset(sample_pipeline, pipeline_config)

        assert_both_endpoints_called_with_auth(
            pipeline_import_routes,
            "test-pipeline",
            "query_yaml",
            "components:\n  answer_builder:\n    init_parameters:\n",
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_pipeline_into_deepset_async_with_validation(
        self, sample_pipeline: Pipeline, test_async_client: AsyncPipelineClient, pipeline_import_routes: MockRoutes
    ) -> None:
        """Test asynchronously importing a pipeline into deepset with validation enabled."""
        pipeline_config = PipelineConfig(
            name="test-pipeline-async-with-validation",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            strict_validation=True,
        )
        await test_async_client.import_into_deepset(sample_pipeline, pipeline_config)

        # Verify both endpoints were called
        assert pipeline_import_routes.validation.called
        assert pipeline_import_routes.import_.called
        assert len(pipeline_import_routes.validation.calls) == 1
        assert len(pipeline_import_routes.import_.calls) == 1

        assert_both_endpoints_called_with_auth(
            pipeline_import_routes,
            "test-pipeline-async-with-validation",
            "query_yaml",
            "components:\n  answer_builder:\n    init_parameters:\n",
        )

    @respx.mock
    def test_import_pipeline_validation_failure_blocks_import(
        self, sample_pipeline: Pipeline, test_client: PipelineClient
    ) -> None:
        """Test that validation failure with strict_validation=True prevents import call."""
        # Mock validation failure response
        validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
            return_value=Response(
                status_code=HTTPStatus.BAD_REQUEST,
                json={"details": [{"code": "INVALID_CONFIGURATION", "message": "Pipeline configuration is invalid"}]},
            )
        )

        # Mock import route (should never be called)
        import_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipelines").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-pipeline-id"})
        )

        pipeline_config = PipelineConfig(
            name="test-pipeline-validation-failure",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            strict_validation=True,  # Should fail on validation errors
        )

        # Import should fail with validation error
        with pytest.raises(DeepsetValidationError):
            test_client.import_into_deepset(sample_pipeline, pipeline_config)

        # Verify only validation endpoint was called, NOT import
        assert validation_route.called
        assert not import_route.called
        assert len(validation_route.calls) == 1
        assert len(import_route.calls) == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_pipeline_with_overwrite_fallback_to_create_async(
        self, sample_pipeline: Pipeline, test_async_client: AsyncPipelineClient
    ) -> None:
        """Test overwriting a pipeline that doesn't exist, falling back to creation."""
        # Mock validation success
        validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
            return_value=Response(status_code=HTTPStatus.NO_CONTENT)
        )

        # Mock 404 response for GET (resource not found)
        version_check_route = respx.get(
            "https://test-api-url.com/workspaces/test-workspace/pipelines/test-pipeline-fallback/versions"
        ).mock(return_value=Response(status_code=HTTPStatus.NOT_FOUND))

        # Mock successful creation
        create_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipelines").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-pipeline-id"})
        )

        pipeline_config = PipelineConfig(
            name="test-pipeline-fallback",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            strict_validation=False,
            overwrite=True,
        )

        await test_async_client.import_into_deepset(sample_pipeline, pipeline_config)

        # Verify all three endpoints were called in sequence
        assert validation_route.called
        assert version_check_route.called
        assert create_route.called

        # Check validation request
        validation_request = validation_route.calls[0].request
        assert validation_request.headers["Authorization"] == "Bearer test-api-key"
        validation_body = json.loads(validation_request.content)
        assert "query_yaml" in validation_body

        # Check GET attempt
        version_check_request = version_check_route.calls[0].request
        assert version_check_request.headers["Authorization"] == "Bearer test-api-key"

        # Check fallback creation
        create_request = create_route.calls[0].request
        assert create_request.headers["Authorization"] == "Bearer test-api-key"
        create_body = json.loads(create_request.content)
        assert create_body["name"] == "test-pipeline-fallback"
        assert "query_yaml" in create_body


class TestRealIntegrationIndex:
    """Real integration tests that call the actual DeepsetCloudAPI."""

    @pytest.fixture
    def sample_index_for_integration(self) -> Pipeline:
        """Create a simple index for real integration testing."""
        file_type_router = FileTypeRouter(mime_types=["text/plain"])
        text_converter = TextFileToDocument(encoding="utf-8")
        document_embedder = SentenceTransformersDocumentEmbedder(normalize_embeddings=True, model="intfloat/e5-base-v2")

        index = Pipeline()

        index.add_component("file_type_router", file_type_router)
        index.add_component("text_converter", text_converter)
        index.add_component("document_embedder", document_embedder)

        index.connect("file_type_router.text/plain", "text_converter.sources")
        index.connect("text_converter.documents", "document_embedder.documents")

        return index

    def test_create_and_delete_index_integration(
        self, integration_config: CommonConfig, workspace_name: str, sample_index_for_integration: Pipeline
    ) -> None:
        """Test creating and deleting an index using real API calls."""
        index_name = f"test-integration-index-{uuid.uuid4().hex[:8]}"

        client = PipelineClient(
            api_key=integration_config.api_key, api_url=integration_config.api_url, workspace_name=workspace_name
        )

        try:
            index_config = IndexConfig(
                name=index_name,
                inputs=IndexInputs(files=["file_type_router.sources"]),
                strict_validation=False,  # Skip validation for integration test
            )

            client.import_into_deepset(sample_index_for_integration, index_config)

            assert_index_exists(integration_config, workspace_name, index_name)
        finally:
            remove_index(integration_config, workspace_name, index_name)

    def test_overwrite_existing_index_integration(
        self, integration_config: CommonConfig, workspace_name: str, sample_index_for_integration: Pipeline
    ) -> None:
        """Test that importing an existing index with overwrite=True overwrites it."""
        index_name = f"test-integration-index-{uuid.uuid4().hex[:8]}"

        client = PipelineClient(
            api_key=integration_config.api_key, api_url=integration_config.api_url, workspace_name=workspace_name
        )

        try:
            # create index
            index_config = IndexConfig(
                name=index_name,
                inputs=IndexInputs(files=["file_type_router.sources"]),
                strict_validation=False,  # Skip validation for integration test
            )

            client.import_into_deepset(sample_index_for_integration, index_config)

            assert_index_exists(integration_config, workspace_name, index_name)

            # Overwrite the index
            index_config = IndexConfig(
                name=index_name,
                inputs=IndexInputs(files=["some_component.sources"]),
                strict_validation=False,  # Skip validation for integration test
                overwrite=True,
            )
            new_index = Pipeline()
            answer_builder = AnswerBuilder()
            new_index.add_component("answer_builder", answer_builder)

            client.import_into_deepset(new_index, index_config)
            response_data = assert_index_exists(integration_config, workspace_name, index_name)
            assert "answer_builder" in response_data["config_yaml"], f"Failed to overwrite index {index_name}"
        finally:
            remove_index(integration_config, workspace_name, index_name)


@pytest.mark.asyncio
class TestRealIntegrationPipeline:
    """Real integration tests for pipelines that call the actual DeepsetCloudAPI."""

    @pytest.fixture
    def sample_pipeline_for_integration(self, monkeypatch: pytest.MonkeyPatch) -> Pipeline:
        """Create a sample pipeline for real integration testing."""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")

        prompt_builder = PromptBuilder(
            template="""You are a technical expert.
                You summary should be no longer than five sentences.
                Passage: {{ question }}
                Your summary: """,
            required_variables=["*"],
        )

        llm = OpenAIGenerator(api_key=Secret.from_env_var("OPENAI_API_KEY", strict=False), model="gpt-4")
        answer_builder = AnswerBuilder()

        pipeline = Pipeline()

        pipeline.add_component("prompt_builder", prompt_builder)
        pipeline.add_component("llm", llm)
        pipeline.add_component("answer_builder", answer_builder)

        pipeline.connect("prompt_builder.prompt", "llm.prompt")
        pipeline.connect("llm.replies", "answer_builder.replies")

        return pipeline

    async def test_create_and_delete_pipeline_integration_async(
        self, integration_config: CommonConfig, workspace_name: str, sample_pipeline_for_integration: Pipeline
    ) -> None:
        """Test import a pipeline using real API calls asynchronously."""
        pipeline_name = f"test-integration-pipeline-{uuid.uuid4().hex[:8]}"

        client = AsyncPipelineClient(
            api_key=integration_config.api_key, api_url=integration_config.api_url, workspace_name=workspace_name
        )

        try:
            pipeline_config = PipelineConfig(
                name=pipeline_name,
                inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
                outputs=PipelineOutputs(answers="answer_builder.answers"),
                strict_validation=False,  # Skip validation for integration test
            )

            await client.import_into_deepset(sample_pipeline_for_integration, pipeline_config)

            assert_pipeline_exists(integration_config, workspace_name, pipeline_name)
        finally:
            remove_pipeline(integration_config, workspace_name, pipeline_name)

    async def test_overwrite_non_existing_pipeline_integration_async(
        self, integration_config: CommonConfig, workspace_name: str, sample_pipeline_for_integration: Pipeline
    ) -> None:
        """Test that importing a non-existent pipeline with overwrite=True falls back to creating it."""
        pipeline_name = f"test-integration-pipeline-{uuid.uuid4().hex[:8]}"

        client = AsyncPipelineClient(
            api_key=integration_config.api_key, api_url=integration_config.api_url, workspace_name=workspace_name
        )

        try:
            pipeline_config = PipelineConfig(
                name=pipeline_name,
                inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
                outputs=PipelineOutputs(answers="answer_builder.answers"),
                strict_validation=False,  # Skip validation for integration test
                overwrite=True,
            )

            await client.import_into_deepset(sample_pipeline_for_integration, pipeline_config)

            assert_pipeline_exists(integration_config, workspace_name, pipeline_name)
        finally:
            remove_pipeline(integration_config, workspace_name, pipeline_name)
