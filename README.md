<p align="center">
  <a href="https://cloud.deepset.ai/"><img src="/assets/logo.png"  alt="deepset SDK"></a>
</p>

[![Coverage badge](https://github.com/deepset-ai/deepset-cloud-sdk/raw/python-coverage-comment-action-data/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/tree/python-coverage-comment-action-data)
[![Tests](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/continuous-integration.yml/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/continuous-integration.yml)
[![Deploy PyPi](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/deploy-prod.yml/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/deploy-prod.yml)
[![Compliance Checks](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/compliance.yml/badge.svg)](https://github.com/deepset-ai/deepset-cloud-sdk/actions/workflows/compliance.yml)

The deepset SDK is an open source software development kit that provides convenient access to and integration with deepset AI Platform, a powerful cloud offering for various AI tasks.
This README provides an overview of the SDK and its features, and information on contributing to the project and exploring related resources.

- [Official SDK Docs](https://docs.cloud.deepset.ai/docs/working-with-the-sdk)
- Tutorials: 
    - [Uploading with CLI](https://docs.cloud.deepset.ai/docs/tutorial-uploading-files-with-cli) 
    - [Uploading with Python Methods](https://docs.cloud.deepset.ai/docs/tutorial-uploading-files-with-python-methods)

# Supported Features

In its current shape, the SDK offers a suite of tools for seamless data upload to deepset AI Platform and for importing Haystack pipelines and indexes.
The following examples demonstrate how to use the deepset SDK to interact with deepset AI Platform using Python.
You can use the deepset SDK in the command line as well. For more information, see the [CLI documentation](docs/examples/cli/README.md).

-   [SDK Examples - Upload datasets](/docs/examples/sdk/upload.py)
-   [CLI Examples - Upload datasets](/docs/examples/cli/README.md)

## Installation
The deepset SDK is available on [PyPI](https://pypi.org/project/deepset-cloud-sdk/) and you can install it using pip:
```bash
pip install deepset-cloud-sdk
```

After installing the deepset SDK, you can use it to interact with deepset AI Platform. It comes with a command line interface (CLI), that you can use by calling:
```bash
deepset-cloud --help
```

<p align="center">
  <a href="https://cloud.deepset.ai/"><img src="/assets/cli.gif"  alt="deepset CLI"></a>
</p>

### Development Installation
To install the deepset SDK for development, clone the repository and install the package in editable mode:
```bash
pip install hatch==1.7.0
hatch build
```

Instead of calling the CLI from the build package, you can call it directly from the source code:
```bash
python3 -m deepset_cloud_sdk.cli --help
```

## Contributing
We welcome contributions from the open source community to enhance the deepset SDK. If you would like to contribute, have a look at [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and instructions on how to get started.
We appreciate your contributions, whether they're bug fixes, new features, or documentation improvements.


---

## Interested in Haystack?
deepset AI Platform is powered by Haystack, an open source framework for building end-to-end NLP pipelines.

 -    [Project website](https://haystack.deepset.ai/)
 -    [GitHub repository](https://github.com/deepset-ai/haystack)

---

# Licenses

The SDK is licensed under Apache 2.0, you can see the license [here](https://github.com/deepset-ai/deepset-cloud-sdk/blob/main/LICENSE)

We use several libraries in this SDK that are licensed under the [MPL 2.0 license](https://www.mozilla.org/en-US/MPL/2.0/)

- [tqdm](https://github.com/tqdm/tqdm) for progress bars
- [pathspec](https://github.com/cpburnz/python-pathspec) for pattern matching file paths
- [certifi](https://github.com/certifi/python-certifi) for validating trustworthiness of SSL certificates
