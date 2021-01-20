import yaml
import logging
import os
import cms.db
import cmscommon.constants
from datetime import timedelta
from cmscontrib.loaders.base_loader import ContestLoader, TaskLoader, UserLoader, TeamLoader

logger = logging.getLogger(__name__)

class HashcodeLoader(ContestLoader, TaskLoader, UserLoader, TeamLoader):

    short_name = "hashcode_yaml"
    description = "Google Hashcode yaml-based format"

    @staticmethod
    def detect(path):
        # Automatic detection disabled
        return False

    # TeamLoader interface

    def team_has_changed(self):
        return False

    def get_team(self):
        return None

    # UserLoader interface

    def user_has_changed(self):
        return False

    def get_user(self):
        return None

    # TaskLoader interface

    def task_has_changed(self):
        return True

    def get_task(self, get_statement):
        task_name = os.path.split(self.path)[1]
        if not os.path.exists(os.path.join(self.path, "task.yaml")):
            logger.critical("File missing: task.yaml")
            return None

        task_conf = yaml.load(open(os.path.join(self.path, "task.yaml"), "r"), Loader=yaml.Loader)

        # Building task arguments
        args = dict()
        args["name"] = task_conf.get("name")
        args["title"] = task_conf.get("title")

        if get_statement:
            statement_path = os.path.join(self.path, "statement", "statement.pdf")
            digest = self.file_cacher.put_file_from_path(statement_path,
                    "Statement for task {}".format(task_name))
            args["statements"] = { "en": cms.db.Statement("en", digest) }
            args["primary_statements"] = ["en"]

        args["submission_format"] = []
        for filename in sorted(os.listdir(os.path.join(self.path, "input"))):
            basename = os.path.splitext(filename)[0]
            args["submission_format"].append("output_" + basename + ".txt")

        args["feedback_level"] = cms.FEEDBACK_LEVEL_FULL
        args["score_precision"] = task_conf.get("score_precision")
        args["score_mode"] = cmscommon.constants.SCORE_MODE_MAX
        args["attachments"] = dict()
        if os.path.exists(os.path.join(self.path, "att")):
            for filename in os.listdir(os.path.join(self.path, "att")):
                digest = self.file_cacher.put_file_from_path(os.path.join(self.path, "att", filename),
                        "Attachment {} for task {}".format(filename, task_name))
                args["attachments"][filename] = cms.db.Attachment(filename, digest)

        task_data = cms.db.Task(**args)

        # Building dataset arguments
        args = dict()
        args["task"] = task_data
        args["description"] = "1.0"
        args["task_type"] = "OutputOnly"
        args["task_type_parameters"] = ["comparator"]
        args["score_type"] = "Sum"
        args["score_type_parameters"] = 1.0
        
        checker_path = os.path.join(self.path, "check", "checker")
        args["managers"] = [ cms.db.Manager("checker", 
            self.file_cacher.put_file_from_path(checker_path, "Checker for task {}".format(task_name))) ]

        args["testcases"] = []
        for filename in sorted(os.listdir(os.path.join(self.path, "input"))):
            basename = os.path.splitext(filename)[0]
            digest = self.file_cacher.put_file_from_path(os.path.join(self.path, "input", filename), 
                    "Input {} for task {}".format(basename, task_name))
            args["testcases"].append( cms.db.Testcase(basename, True, digest, digest) )
            task_data.attachments.set( cms.db.Attachment(filename, digest) )
        args["testcases"] = dict((tc.codename, tc) for tc in args["testcases"])

        print("Testcases:\n\n")
        print(args["testcases"])

        args["managers"] = dict((mg.filename, mg) for mg in args["managers"])

        dataset_data = cms.db.Dataset(**args)
        task_data.active_dataset = dataset_data
        return task_data

    # ContestLoader interface

    def contest_has_changed(self):
        return True

    def get_contest(self):
        print(os.path.join(self.path, "contest.yaml"))

        conf = yaml.load(open(os.path.join(self.path, "contest.yaml"), "r"), Loader=yaml.Loader)
        args = dict()

        args["name"] = conf.get("name")
        args["description"] = conf.get("description")
        args["languages"] = []
        args["allow_questions"] = False
        args["allow_user_tests"] = False
        args["block_hidden_participations"] = conf.get("block_hidden_participations", True)
        args["allow_password_authentication"] = conf.get("allow_password_authentication", True)
        args["allow_registration"] = conf.get("allow_registration", True)
        args["ip_restriction"] = False
        args["ip_autologin"] = True 
        args["token_mode"] = cms.TOKEN_MODE_DISABLED
        args["score_precision"] = conf.get("score_precision")

        task_names = conf.get("tasks")
        return cms.db.Contest(**args), task_names, []

    def get_task_loader(self, taskname):
        return HashcodeLoader(os.path.join(self.path, taskname), self.file_cacher)
            
