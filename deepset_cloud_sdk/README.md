# Software development kit for the deepset.ai cloud API

This package is split into multiple layers:
- API layer
- Client layer
- Service layer
- Workflow layer


### API layer
This layer is the lowest level of abstraction and contains the API definition including all HTTP methods and takes care of the authentication.
You can find this layer in the `deepset_cloud_sdk/api/deepset_cloud_api.py` file. We should implement reties on this lowest layer.

### Client layer
This layer adds a thin wrapper around the API layer and provides a more convenient interface to the API. It for example includes explicit methods
for endpoints by specifying the HTTP methods and endpoints for e.g. uploading files.

### Service layer
This layer takes care of combining client methods to provide more complex functionality. Within this layer we can add functionalities like
first creating sessions, uploading files, and later closing them.

### Workflow layer
Public methods to be used by users. These workflows are split into async and sync implementation.


## Software architecture principles

### Factories
We are using factories implemented like this:
```python
@classmethod
async def factory(cls, config: CommonConfig) -> YourClass:
    """Create a new instance of the API client.

    :param config: CommonConfig object.
    """
    yield cls(config)
```

### Tests
We are using the classical pyramid of tests: unit tests (for each layer), integration tests. The goal is to gradually test each layer and
then test the whole stack once within the integration tests.
