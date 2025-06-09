"""Integration tests for importing Haystack pipelines into deepset AI Platform."""
import json
from http import HTTPStatus

import pytest
import respx
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

from deepset_cloud_sdk.workflows.pipeline_client import PipelineClient
from deepset_cloud_sdk.workflows.pipeline_client.models import (
    IndexConfig,
    IndexInputs,
    PipelineConfig,
    PipelineInputs,
    PipelineOutputs,
)


@pytest.mark.parametrize("pipeline_class", [Pipeline, AsyncPipeline])
class TestImportIndexIntoDeepset:
    @pytest.fixture
    def sample_index(self, pipeline_class: Pipeline | AsyncPipeline) -> Pipeline:
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

    @pytest.mark.integration
    @respx.mock
    def test_import_index_into_deepset(self, sample_index: Pipeline) -> None:
        """Test synchronously importing an index into deepset."""
        route = respx.post("https://test-api-url.com/workspaces/test-workspace/indexes").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-index-id"})
        )

        # Initialize client with explicit configuration
        client = PipelineClient(
            api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace"
        )

        index_config = IndexConfig(
            name="test-index",
            inputs=IndexInputs(
                files=["file_type_router.sources"],
            ),
            enable_validation=False,
        )

        client.import_into_deepset(sample_index, index_config)

        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test-api-key"

        request_body = json.loads(request.content)
        assert request_body["name"] == "test-index"
        assert request_body["config_yaml"].startswith("components:\n  document_embedder:\n")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @respx.mock
    async def test_import_index_into_deepset_async(self, sample_index: Pipeline) -> None:
        """Test asynchronously importing an index into deepset."""
        route = respx.post("https://test-api-url.com/workspaces/test-workspace/indexes").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-index-id"})
        )

        # Initialize client with explicit configuration
        client = PipelineClient(
            api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace"
        )

        index_config = IndexConfig(
            name="test-index-async",
            inputs=IndexInputs(
                files=["file_type_router.sources"],
            ),
            enable_validation=False,
        )

        await client.import_into_deepset_async(sample_index, index_config)

        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test-api-key"

        request_body = json.loads(request.content)
        assert request_body["name"] == "test-index-async"
        assert request_body["config_yaml"].startswith("components:\n  document_embedder:\n")

    @pytest.mark.integration
    @respx.mock
    def test_import_index_into_deepset_with_validation(self, sample_index: Pipeline) -> None:
        """Test synchronously importing an index into deepset with validation enabled."""
        validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
            return_value=Response(status_code=HTTPStatus.NO_CONTENT)
        )
        import_route = respx.post("https://test-api-url.com/workspaces/test-workspace/indexes").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-index-id"})
        )

        client = PipelineClient(
            api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace"
        )

        index_config = IndexConfig(
            name="test-index-with-validation",
            inputs=IndexInputs(
                files=["file_type_router.sources"],
            ),
            enable_validation=True,
        )

        client.import_into_deepset(sample_index, index_config)

        # Verify both endpoints were called
        assert validation_route.called
        assert import_route.called

        # Verify validation was called first
        assert len(validation_route.calls) == 1
        assert len(import_route.calls) == 1

        # Check validation request
        validation_request = validation_route.calls[0].request
        assert validation_request.headers["Authorization"] == "Bearer test-api-key"
        validation_body = json.loads(validation_request.content)
        assert validation_body["name"] == "test-index-with-validation"
        assert "indexing_yaml" in validation_body
        assert validation_body["indexing_yaml"].startswith("components:\n  document_embedder:\n")

        # Check import request
        import_request = import_route.calls[0].request
        assert import_request.headers["Authorization"] == "Bearer test-api-key"
        import_body = json.loads(import_request.content)
        assert import_body["name"] == "test-index-with-validation"
        assert import_body["config_yaml"].startswith("components:\n  document_embedder:\n")


@pytest.mark.parametrize("pipeline_class", [Pipeline, AsyncPipeline])
class TestImportPipelineIntoDeepset:
    @pytest.fixture
    def sample_pipeline(self, pipeline_class: Pipeline | AsyncPipeline, monkeypatch: pytest.MonkeyPatch) -> Pipeline:
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

    @pytest.mark.integration
    @respx.mock
    def test_import_pipeline_into_deepset(self, sample_pipeline: Pipeline) -> None:
        """Test synchronously importing a pipeline into deepset AI Platform."""
        route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipelines").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-pipeline-id"})
        )

        client = PipelineClient(
            api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace"
        )

        pipeline_config = PipelineConfig(
            name="test-pipeline",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            enable_validation=False,
        )
        client.import_into_deepset(sample_pipeline, pipeline_config)

        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test-api-key"

        request_body = json.loads(request.content)
        assert request_body["name"] == "test-pipeline"
        assert request_body["query_yaml"].startswith("components:\n  answer_builder:\n    init_parameters:\n")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @respx.mock
    async def test_import_pipeline_into_deepset_async(self, sample_pipeline: Pipeline) -> None:
        """Test asynchronously importing a pipeline into deepset."""
        route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipelines").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"name": "test-pipeline-id"})
        )

        client = PipelineClient(
            api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace"
        )

        pipeline_config = PipelineConfig(
            name="test-pipeline",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            enable_validation=False,
        )
        await client.import_into_deepset_async(sample_pipeline, pipeline_config)

        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer test-api-key"

        request_body = json.loads(request.content)
        assert request_body["name"] == "test-pipeline"
        assert request_body["query_yaml"].startswith("components:\n  answer_builder:\n    init_parameters:\n")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @respx.mock
    async def test_import_pipeline_into_deepset_async_with_validation(self, sample_pipeline: Pipeline) -> None:
        """Test asynchronously importing a pipeline into deepset with validation enabled."""
        validation_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipeline_validations").mock(
            return_value=Response(status_code=HTTPStatus.NO_CONTENT)
        )

        import_route = respx.post("https://test-api-url.com/workspaces/test-workspace/pipelines").mock(
            return_value=Response(status_code=HTTPStatus.OK, json={"id": "test-pipeline-id"})
        )

        client = PipelineClient(
            api_key="test-api-key", api_url="https://test-api-url.com", workspace_name="test-workspace"
        )

        pipeline_config = PipelineConfig(
            name="test-pipeline-async-with-validation",
            inputs=PipelineInputs(query=["prompt_builder.prompt", "answer_builder.query"]),
            outputs=PipelineOutputs(answers="answer_builder.answers"),
            enable_validation=True,
        )
        await client.import_into_deepset_async(sample_pipeline, pipeline_config)

        # Verify both endpoints were called
        assert validation_route.called
        assert import_route.called

        # Verify validation was called first
        assert len(validation_route.calls) == 1
        assert len(import_route.calls) == 1

        # Check validation request
        validation_request = validation_route.calls[0].request
        assert validation_request.headers["Authorization"] == "Bearer test-api-key"
        validation_body = json.loads(validation_request.content)
        assert validation_body["name"] == "test-pipeline-async-with-validation"
        assert "query_yaml" in validation_body
        assert validation_body["query_yaml"].startswith("components:\n  answer_builder:\n    init_parameters:\n")

        # Check import request
        import_request = import_route.calls[0].request
        assert import_request.headers["Authorization"] == "Bearer test-api-key"
        import_body = json.loads(import_request.content)
        assert import_body["name"] == "test-pipeline-async-with-validation"
        assert import_body["query_yaml"].startswith("components:\n  answer_builder:\n    init_parameters:\n")
