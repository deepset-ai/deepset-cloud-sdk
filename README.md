<p align="center">
  <a href="https://cloud.deepset.ai/"><img src="/assets/logo.png"  alt="deepset Cloud SDK"></a>
</p>

[![Coverage badge](https://github.com/deepset-ai/deepset-cloud-sdk/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/tree/python-coverage-comment-action-data)
[![Tests](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/continuous-integration.yml)
[![Deploy PyPi](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/deploy-prod.yml/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/deploy-prod.yml)
[![Compliance Checks](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/compliance.yml/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/compliance.yml)

The deepset Cloud SDK is an open source software development kit that provides convenient access and integration with deepset Cloud, a powerful cloud offering for various natural language processing (NLP) tasks.
This README provides an overview of the SDK and its features, and information on contributing to the project and exploring related resources.

# Supported Features
The following examples demonstrate how to use the deepset Cloud SDK to interact with deepset Cloud using Python.
You can use the deepset Cloud SDK in the command line as well. For more information, see the [CLI documentation](/examples/cli/README.md).
- [SDK Examples - Upload datasets](/examples/sdk/upload.py)
- [CLI Examples - Upload datasets](/examples/cli/README.md)

## Installation
The deepset Cloud SDK is available on PyPI and you can install it using pip:
```bash
pip install deepset-cloud-sdk
```

After installing the deepset Cloud SDK, you can use it to interact with deepset Cloud. It comes with a command line interface (CLI), that you can use by calling:
```bash
deepset-cloud --help
```

<p align="center">
  <a href="https://cloud.deepset.ai/"><img src="/assets/cli.gif"  alt="deepset Cloud CLI"></a>
</p>

### Development Installation
To install the deepset Cloud SDK for development, clone the repository and install the package in editable mode:
```bash
pip install hatch==1.7.0
hatch build
```

Instead of calling the cli from the build package, you can call it directly from the source code:
```bash
python3 -m deepset_cloud_sdk.cli --help
```

## Contributing
We welcome contributions from the open source community to enhance the deepset Cloud SDK. If you would like to contribute, have a look at [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and instructions on how to get started.
We appreciate your contributions, whether they're bug fixes, new features, or documentation improvements.


---

## Interested in deepset Cloud?
If you are interested in exploring deepset Cloud, visit cloud.deepset.ai.
deepset Cloud provides a range of NLP capabilities and services to help you build and deploy powerful
natural language processing applications.

## Interested in Haystack?
deepset Cloud is powered by Haystack, an open source framework for building end-to-end NLP pipelines.
 - [Project website](https://haystack.deepset.ai/)
 - [GitHub repository](https://github.com/deepset-ai/haystack)
