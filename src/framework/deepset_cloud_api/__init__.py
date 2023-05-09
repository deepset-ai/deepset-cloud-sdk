from framework.deepset_cloud_api.config import CommonConfig
from framework.deepset_cloud_api.evaluation_set import EvaluationSets
from framework.deepset_cloud_api.files import Files
from framework.deepset_cloud_api.pipelines import Pipelines
from framework.deepset_cloud_api.workspaces import Workspaces
from framework.deepset_cloud_api.organizations import Organizations


class DeepsetCloudAPI:
    def __init__(self, config: CommonConfig):
        self.pipelines = Pipelines(config)
        self.files = Files(config)
        self.evaluation_sets = EvaluationSets(config)
        self.organization = Organizations(config)
        self.workspaces = Workspaces(config)
