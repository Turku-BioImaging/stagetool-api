import os
from main import app
from classes import TaskNotFound, Task
from unittest.mock import patch
from unittest import TestCase
from uuid import uuid4
from jsonschema import validate
from werkzeug.datastructures import FileStorage
import json
from dotenv import load_dotenv
from shutil import rmtree, copy

# load_dotenv()
os.environ["ENV"] = "testing"
env = os.getenv("ENV", "development")

if env == "testing":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data-dev")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# import Task schema definition
with open(os.path.join(os.path.dirname(__file__), "..", "..", "stagetool.json")) as f:
    data = json.load(f)
    task_schema = data["components"]["schemas"]["Task"]


class TestGetTask(TestCase):
    def setUp(self) -> None:
        self.task_data = {
            "id": str(uuid4().hex),
            "status": "pending",
            "image_filenames": ["01.png", "02.png"],
            "visualization_filenames": ["01.png", "02.png"],
            "results": ["results.pkl"],
        }

        return super().setUp()

    def test_get_task(self):
        with app.test_client() as client:
            # Test retrieving an existing task
            with patch("main.Task") as mock_task:
                mock_task.return_value.data.return_value = self.task_data
                response = client.get(f"/task?id={self.task_data['id']}")
                assert response.status_code == 200
                assert response.json == self.task_data
                assert validate(response.json, task_schema) is None

            # Test case where task is not found
            with patch("main.Task") as mock_task:
                mock_task.side_effect = TaskNotFound
                response = client.get(f"/task?id={str(uuid4().hex)}")
                assert response.status_code == 404
                assert response.json == {"error": "Task not found"}


class TestPostTask(TestCase):
    def tearDown(self) -> None:
        # delete all dirs in DATA_DIR
        for dir in os.listdir(DATA_DIR):
            dir_path = os.path.join(DATA_DIR, dir)
            if os.path.isdir(dir_path):
                rmtree(dir_path)

        return super().tearDown()

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


class TestGetImages(TestCase):
    def setUp(self) -> None:
        img_dir = os.path.join(os.path.dirname(__file__), "images")

        with open(os.path.join(img_dir, "02.png"), "rb") as img:
            images = [FileStorage(img, filename="02.png")]

            self.task = Task(images=images)

    def test_get_images(self):
        with app.test_client() as client:
            # task id is not provided
            response = client.get("/images?filename=02.png")
            assert response.status_code == 400

            # task id does not exist
            response = client.get("/images?task_id=123&filename=02.png")
            assert response.status_code == 404

            # download existing image
            response = client.get(f"/images?task_id={self.task.id}&filename=02.png")
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "image/png"


class TestGetVisualizations(TestCase):
    def setUp(self) -> None:
        img_dir = os.path.join(os.path.dirname(__file__), "images")
        with open(os.path.join(img_dir, "02.png"), "rb") as img:
            images = [FileStorage(img, filename="02.png")]

            self.task = Task(images=images)

        task_dir = os.path.join(DATA_DIR, self.task.id)
        copy(os.path.join(img_dir, "02.png"), os.path.join(task_dir, "visualizations"))

    def test_get_visualizations(self):
        with app.test_client() as client:
            # task id is not provided
            response = client.get("/visualizations?filename=02.png")
            assert response.status_code == 400

            # vis filename is not provided
            response = client.get("/visualizations?task_id=123")
            assert response.status_code == 400

            # task id does not exist
            response = client.get('/visualizations?task_id=123&filename="02.png"')
            assert response.status_code == 404

            # download existing vis image
            response = client.get(
                f"/visualizations?task_id={self.task.id}&filename=02.png"
            )
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "image/png"
