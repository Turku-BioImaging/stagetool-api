from glob import glob
from PIL import Image
import io
import os
from enum import Enum, auto
from uuid import uuid4
import subprocess
from dotenv import load_dotenv
from werkzeug.datastructures import FileStorage

load_dotenv()
env = os.getenv("ENV", "development")

if env == "development":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data-dev")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class Status(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()


class TaskNotFound(Exception):
    pass


class TaskCreationError(Exception):
    pass


class Task:
    def __init__(
        self,
        id: str = None,
        # images: bytearray = None,
        images: FileStorage = None,
    ):
        if id is None and images is None:
            raise ValueError("Either a task id or images must be provided")

        if id is not None and self._load_from_existing(id) is True:
            return self
        else:
            self.id = str(uuid4().hex)
            self._configure_task_dir()
            self._save_images_to_task_dir(images)

    def _load_from_existing(self, id: str):
        if os.path.isdir(os.path.join(DATA_DIR, id)):
            self.id = id
            return True
        raise TaskNotFound(f"Task with id {id} not found")

    def _configure_task_dir(self):
        assert self.id is not None
        if not os.path.isdir(DATA_DIR):
            os.mkdir(DATA_DIR)

        self.task_dir = os.path.join(DATA_DIR, self.id)
        os.makedirs(os.path.join(self.task_dir, "images"))
        os.makedirs(os.path.join(self.task_dir, "visualizations"))
        os.makedirs(os.path.join(self.task_dir, "results"))

    def _save_images_to_task_dir(self, images: FileStorage):
        for i in images:
            fname = i.filename
            image_data = Image.open(io.BytesIO(i.read()))
            image_data.save(os.path.join(self.task_dir, "images", fname))

    def execute(self):
        """
        Executes StageTool Docker command in the background.

        The method runs a StageTool Docker command in the background using the `subprocess.Popen` function.

        Args:
            None

        Returns:
            None
        """
        command = f"docker run -v {self.task_dir}:/data my-docker-image"

        # Start the command as a background process
        process = subprocess.Popen(command, shell=True)

        # Print a message to indicate that the process has started
        print("Process started with PID:", process.pid)

    def status(self) -> str:
        if not os.path.isdir(self.task_dir):
            return Status.PENDING.name.lower()

        images_count = len(glob(os.path.join(self.task_dir, "images", "*")))

        visualizations_count = len(
            glob(os.path.join(self.task_dir, "visualizations", "*"))
        )

        has_results = os.path.isfile(os.path.join(self.task_dir, "results", "*.pkl"))

        if (images_count == visualizations_count) and has_results:
            return Status.COMPLETED.name.lower()

        return Status.PENDING.name.lower()

    def data(self) -> dict:
        """
        Method is used by the Flask app to return information about the task, including its ID, status, image filenames,
        visualization filenames, and result URLs.

        Args:
            None
        Returns:
            dict: A dictionary containing information about the task.
        """
        img_fnames = sorted(glob(os.path.join(self.task_dir, "images", "*")))
        vis_fnames = sorted(glob(os.path.join(self.task_dir, "visualizations", "*")))
        result_urls = sorted(glob(os.path.join(self.task_dir, "results", "*")))

        return {
            "id": self.id,
            "status": self.status(),
            "image_filenames": [os.path.basename(i) for i in img_fnames],
            "visualization_filenames": [os.path.basename(i) for i in vis_fnames],
            "results": result_urls,
        }
