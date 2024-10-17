import logging
import os

from src.RoboflowModel import RoboflowModelParams, RoboflowModel
from src.MongoDBRepository import MongoDBRepository


class DataExtractService:
    def __init__(self, roboflow_params: RoboflowModelParams, mongo_repo: MongoDBRepository):
        self.roboflow_model = RoboflowModel(roboflow_params)
        self.mongo_repo = mongo_repo

