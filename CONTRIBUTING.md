# Contributing

## Setup

### To build from source

Install hatch
```
pip install hatch=="v1.7.0"
```

### Install pre commit hooks
```
hatch run code-quality:hooks
```

## Deploying to Test PyPi

When you create a PR in the deepset-cloud-sdk repository, adding the 'test-deploy' label will trigger a deployment to the test PyPi repository.
