import os
import boto3
import logging
import watchtower

class Config:
    def __init__(self):
        self.TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.apuestas = {}
        self.responsabe_id = None

        users = os.getenv("USERS")
        self.usuarios_permitidos = [int(x) for x in users.split(',') if x.strip().isdigit()]

        self.admin = os.getenv("ADMIN")

        # Config logger for CloudWatch
        self.logger = logging.getLogger("quiniela_quinigol_bot")
        self.logger.setLevel(logging.INFO)
        boto3_client = boto3.client("logs", region_name="eu-west-1")
        self.logger.addHandler(watchtower.CloudWatchLogHandler(log_group_name="QuiniBot", boto3_client=boto3_client))

        self.info_tabla = {
            'quiniela': [],
            'quinigol': []
        }


config = Config()