import json
import os
import random
from glob import glob
from unittest import TestCase

from classes import Status, Task

# from dotenv import load_dotenv
from jsonschema import validate
from main import app
from werkzeug.datastructures import FileStorage

from .factories import TaskFactory

os.environ["ENV"] = "testing"
env = os.getenv("ENV")

if env == "testing" or env == "development":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data-dev")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# import Task schema definition
with open(os.path.join(os.path.dirname(__file__), "..", "..", "stagetool.json")) as f:
    data = json.load(f)
    task_schema = data["components"]["schemas"]["Task"]


class TestGetTask(TestCase):
    def setUp(self) -> None:
        self.task = TaskFactory.create_task(num_images=2)

    def tearDown(self) -> None:
        self.task.destroy()

    def test_get_task(self):
        with app.test_client() as client:
            # Test retrieving an existing task
            response = client.get(f"/task?id={self.task.id}")
            assert response.status_code == 200
            assert validate(response.json, task_schema) is None

            # Test case where task is not found
            response = client.get("/task?id=1234")
            assert response.status_code == 404


class TestPostTask(TestCase):
    def tearDown(self) -> None:
        task = Task(id=self.task_id)
        task.destroy()

    def test_post_task(self):
        with app.test_client() as client:
            # Test case where images are not provided
            response = client.post("/task")
            assert response.status_code == 400

            img_dir = os.path.join(os.path.dirname(__file__), "images")

            with open(os.path.join(img_dir, "01.png"), "rb") as img1, open(
                os.path.join(img_dir, "02.png"), "rb"
            ) as img2:
                response = client.post(
                    "/task",
                    data={
                        "images": [
                            FileStorage(img1, filename="01.png"),
                            FileStorage(img2, filename="02.png"),
                        ]
                    },
                )

            assert response.status_code == 201
            assert validate(response.json, task_schema) is None

            assert response.json["status"] == "pending"
            assert len(response.json["image_filenames"]) == 2
            assert len(response.json["visualization_filenames"]) == 0

            self.task_id = response.json["id"]


class TestGetImages(TestCase):
    def setUp(self) -> None:
        self.task = TaskFactory.create_task(num_images=3)

    def tearDown(self) -> None:
        self.task.destroy()

    def test_get_images(self):
        with app.test_client() as client:
            # task id is not provided
            response = client.get("/images?filename=02.png")
            assert response.status_code == 400

            # task id does not exist
            response = client.get("/images?task_id=123&filename=02.png")
            assert response.status_code == 404

            # download existing image
            img_fnames = [
                os.path.basename(i)
                for i in glob(os.path.join(DATA_DIR, self.task.id, "images", "*"))
            ]
            response = client.get(
                f"/images?task_id={self.task.id}&filename={random.choice(img_fnames)}"
            )
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "image/png"


class TestVisualizations(TestCase):
    def setUp(self) -> None:
        self.task = TaskFactory.create_task(num_images=2, status=Status.COMPLETED.name)

    def tearDown(self) -> None:
        self.task.destroy()

    def test_get_visualizations(self):
        with app.test_client() as client:
            # task id is not provided
            response = client.get("/visualizations?filename=04.png")
            assert response.status_code == 400

            # vis filename is not provided
            response = client.get("/visualizations?task_id=123")
            assert response.status_code == 400

            # task id does not exist
            response = client.get("/visualizations?task_id=123&filename=image_0.png")
            assert response.status_code == 404

            # download existing vis image
            response = client.get(
                f"/visualizations?task_id={self.task.id}&filename=image_1.png"
            )
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "image/png"


# class TestResults(TestCase):
#     def setUp(self) -> None:
#         self.task = TaskFactory.create_task(num_images=1, status=Status.COMPLETED.name)

#     def tearDown(self) -> None:
#         self.task.destroy()

#     def test_get_results(self):
#         with app.test_client() as client:
#             # task id not provided
#             response = client.get("/results/csv?task_id=1234")
#             assert response.status_code == 400
