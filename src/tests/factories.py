from werkzeug.datastructures import FileStorage
from classes import Task, Status, PickleParser
import os
from dotenv import load_dotenv
import numpy as np
from PIL import Image
from io import BytesIO
import shutil

# import pickle

load_dotenv()

env = os.getenv("ENV")

if env == "testing" or env == "development":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data-dev")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


class TaskFactory:
    @staticmethod
    def create_task(
        num_images: int = None,
        status: str = Status.PENDING.name,
        image_fnames: list = None,
    ):
        if num_images is not None:
            images = []
            for i in range(num_images):
                image = np.random.randint(0, 255, size=(50, 50), dtype=np.uint8)
                image = Image.fromarray(image)
                img_bytes = BytesIO()
                image.save(img_bytes, format="PNG")
                img_bytes.seek(0)
                images.append(FileStorage(img_bytes, filename=f"image_{i}.png"))
            task = Task(images=images)

        elif image_fnames is not None:
            images = []
            for fname in image_fnames:
                with open(os.path.join(DATA_DIR, fname), "rb") as f:
                    img_bytes = BytesIO(f.read())
                images.append(FileStorage(img_bytes, filename=fname))
            task = Task(images=images)
        else:
            raise ValueError("Either num_images or image_fnames must be provided.")

        if status == Status.PENDING.name:
            return task

        if status == Status.COMPLETED.name:
            task_img_paths = os.listdir(os.path.join(DATA_DIR, task.id, "images"))
            for i in task_img_paths:
                shutil.copy(
                    os.path.join(DATA_DIR, task.id, "images", os.path.basename(i)),
                    os.path.join(
                        DATA_DIR, task.id, "visualizations", os.path.basename(i)
                    ),
                )

            pkl_path = os.path.join(
                os.path.dirname(__file__), "pkl", "pkl_from_0.1.0.pkl"
            )
            shutil.copy(
                pkl_path, os.path.join(DATA_DIR, task.id, "results", "results.pkl")
            )

            return task
