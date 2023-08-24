# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/deepset-ai/deepset-cloud-sdk/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                        |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| deepset\_cloud\_sdk/\_\_init\_\_.py                         |        4 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/\_api/config.py                         |       30 |        1 |        8 |        1 |     95% |        37 |
| deepset\_cloud\_sdk/\_api/deepset\_cloud\_api.py            |       46 |        1 |       16 |        6 |     89% |45->44, 61->63, 62->61, 63->62, 68->exit, 77->71, 212 |
| deepset\_cloud\_sdk/\_api/files.py                          |       49 |        2 |       18 |        5 |     90% |34->33, 96-99, 102->106, 106->110, 110->113 |
| deepset\_cloud\_sdk/\_api/upload\_sessions.py               |       90 |        0 |       28 |        2 |     98% |188->182, 227->221 |
| deepset\_cloud\_sdk/\_s3/\_\_init\_\_.py                    |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/\_s3/upload.py                          |      116 |        5 |       40 |        7 |     91% |85->79, 105->exit, 116-124, 160->exit, 161->160, 251->exit, 269->exit |
| deepset\_cloud\_sdk/\_service/files\_service.py             |      144 |        0 |       86 |       14 |     94% |46->48, 47->46, 48->47, 55->exit, 95->102, 107->106, 147->161, 161->exit, 172->171, 192->191, 236->235, 286->292, 327->339, 339->exit |
| deepset\_cloud\_sdk/\_utils/\_\_init\_\_.py                 |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/cli.py                                  |       72 |        1 |       32 |        8 |     91% |28->27, 48->51, 55->54, 71->70, 121->120, 167->143, 176->175, 226->225, 242 |
| deepset\_cloud\_sdk/models.py                               |       13 |        0 |        4 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/\_\_init\_\_.py               |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/async\_client/\_\_init\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/async\_client/files.py        |       37 |        0 |       16 |        8 |     85% |52->exit, 53->52, 86->exit, 87->86, 113->exit, 140->exit, 179->exit, 217->exit |
| deepset\_cloud\_sdk/workflows/sync\_client/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/sync\_client/files.py         |       37 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/sync\_client/utils.py         |       16 |        1 |        2 |        0 |     94% |        26 |
|                                                   **TOTAL** |  **654** |   **11** |  **250** |   **51** | **93%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/deepset-ai/deepset-cloud-sdk/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/deepset-ai/deepset-cloud-sdk/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/deepset-ai/deepset-cloud-sdk/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/deepset-ai/deepset-cloud-sdk/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fdeepset-ai%2Fdeepset-cloud-sdk%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/deepset-ai/deepset-cloud-sdk/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.