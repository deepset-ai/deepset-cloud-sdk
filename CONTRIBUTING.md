# Contributing

## Setup

### Build from source

Install hatch
```
pip install hatch=="v1.7.0"
```

### Install pre-commit hooks
```
hatch run code-quality:hooks
```

## CI
Code quality checks, unit tests, and integration tests (against dev) are performed on the creation of a PR, and subsequent pushes for that PR.
Code quality checks, unit tests, and integration tests (against dev) are performed on a push to main.
Integration tests are triggered whenever the e2e tests are triggered (environment will be dependent on e2e tests)
Code quality checks, unit tests, and integration tests (against prod) are performed on the publishing of a release tag.

## Deploy to test PyPi

When you create a PR in the deepset-cloud-sdk repository, add the 'test-deploy' label to trigger deployment to the test PyPi repository.

## Publishing to PyPi

To publish a new version of the SDK you will need to create and publish a new release tag.


## Software design

Have a look at this [README](/deepset_cloud_sdk/README.md) to get an overview of the software design.
