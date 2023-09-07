# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/deepset-ai/deepset-cloud-sdk/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                        |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| deepset\_cloud\_sdk/\_\_init\_\_.py                         |        4 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/\_api/config.py                         |       30 |        1 |        8 |        1 |     95% |        37 |
| deepset\_cloud\_sdk/\_api/deepset\_cloud\_api.py            |       46 |        1 |       16 |        6 |     89% |45->44, 61->63, 62->61, 63->62, 68->exit, 77->71, 212 |
| deepset\_cloud\_sdk/\_api/files.py                          |       88 |        4 |       40 |        9 |     90% |39->38, 101-104, 107->111, 111->115, 115->118, 127->126, 156->158, 175, 179 |
| deepset\_cloud\_sdk/\_api/upload\_sessions.py               |       90 |        0 |       28 |        2 |     98% |188->182, 227->221 |
| deepset\_cloud\_sdk/\_s3/\_\_init\_\_.py                    |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/\_s3/upload.py                          |      118 |        5 |       42 |        7 |     91% |85->79, 105->exit, 116-124, 164->exit, 165->164, 256->exit, 274->exit |
| deepset\_cloud\_sdk/\_service/files\_service.py             |      180 |        1 |      104 |       15 |     94% |50->52, 51->50, 52->51, 59->exit, 104->111, 116->115, 156->170, 170->179, 182->181, 202->201, 246->245, 298->304, 385, 434->446, 446->454 |
| deepset\_cloud\_sdk/\_utils/\_\_init\_\_.py                 |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/cli.py                                  |       76 |        1 |       34 |        9 |     91% |29->28, 70->69, 90->93, 97->96, 113->112, 163->162, 209->185, 218->217, 268->267, 284 |
| deepset\_cloud\_sdk/models.py                               |       13 |        0 |        4 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/\_\_init\_\_.py               |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/async\_client/\_\_init\_\_.py |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/async\_client/files.py        |       38 |        0 |       16 |        8 |     85% |53->exit, 54->53, 87->exit, 88->87, 114->exit, 149->exit, 187->exit, 227->exit |
| deepset\_cloud\_sdk/workflows/sync\_client/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/sync\_client/files.py         |       38 |        0 |        0 |        0 |    100% |           |
| deepset\_cloud\_sdk/workflows/sync\_client/utils.py         |       16 |        1 |        2 |        0 |     94% |        26 |
|                                                   **TOTAL** |  **737** |   **14** |  **294** |   **57** | **93%** |           |


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