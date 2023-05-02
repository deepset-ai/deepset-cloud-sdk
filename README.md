# platform-python-template

This repository can be used as a template for other platform-engineering python based repositories.

It already contains:

  - issue templates
  - PR template
  - workflows for:
    - compliance
    - velocity metrics
    - dependabot configuration
    - high-priority bugs
    - code quality and unit tests
    - secret scanning
  - basic code $ test structure
  - .gitignore
  - builds using hatch
  - pre commit config

# Setup

Install hatch
```
pip install hatch=="v1.7.0"
```

To use the precommit hooks please run:
```
hatch run code-quality:hooks
```

## Secrets to add in your new repository

**SLACK**

  - SLACK_WEBHOOK_URL - the webhook for posting a message to slack
  - SLACK_WEBHOOK_BUG_ALERT_URL - the webhook for posting a high priority bug alert to slack

**FOSSA**

  - FOSSA_LICENSE_SCAN_TOKEN

**GITHUB**

  - VELOCITY_METRICS_ORG_READ_TOKEN - github token with read permissions for the current github repo

**DATADOG**

  - VELOCITY_METRICS_DATADOG_API_KEY
