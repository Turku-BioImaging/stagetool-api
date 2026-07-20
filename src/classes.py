"""
Here we define the Task class, which serves as a handle for prediction tasks containing several images and takes care of initializing StageTool Core. The PickleParser class is used to parse the results of the prediction task and return a dictionary with the parsed data.

Author: Junel Solis, Turku BioImaging, Turku, Finland, 2023.
"""


from glob import glob
from PIL import Image
import io
import os
from os import listdir
from os.path import isfile, join
from enum import Enum, auto
from uuid import uuid4
import subprocess
from dotenv import load_dotenv
from werkzeug.datastructures import FileStorage
import shutil
import pickle
import json
import re
import time

load_dotenv()
env = os.getenv("ENV", "development")
DOCKER_IMAGE_NAME = os.getenv("DOCKER_IMAGE_NAME")
DOCKER_IMAGE_VERSION = os.getenv("DOCKER_IMAGE_VERSION")
REPLACE_REGEX = r"[^a-zA-Z0-9_\-]" #True if: NOT (a-z, A-Z, 0-9, _, -)

if env == "development":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data-dev")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class Status(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()


class TaskNotFoundError(Exception):
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

        if id is not None:
            self._load_from_existing(id)
        else:
            self.id = str(uuid4().hex)
            self._configure_task_dir()
            self._save_images_to_task_dir(images)

    def _load_from_existing(self, id: str):
        if os.path.isdir(os.path.join(DATA_DIR, id)):
            self.id = id
            self.task_dir = os.path.join(DATA_DIR, self.id)
            return True
        raise TaskNotFoundError(f"Task with id {id} not found")

    def _configure_task_dir(self):
        assert self.id is not None
        if not os.path.isdir(DATA_DIR):
            os.mkdir(DATA_DIR)

        self.task_dir = os.path.join(DATA_DIR, self.id)
        os.makedirs(os.path.join(self.task_dir, "images"))
        os.makedirs(os.path.join(self.task_dir, "visualizations"))
        os.makedirs(os.path.join(self.task_dir, "results"))
        os.makedirs(os.path.join(self.task_dir, "resultconversions"))
        os.makedirs(os.path.join(self.task_dir, "imageconversions"))

    def _save_images_to_task_dir(self, images: FileStorage):
        for i in images:
            file_ending = f".{i.filename.split('.')[-1]}"
            fname = re.sub(REPLACE_REGEX, '_', i.filename.split('.')[0])+file_ending
            if re.match("pred_", fname):
                fname = re.sub("pred_", "pred-", fname)
            image_data = Image.open(io.BytesIO(i.read()))
            image_data.save(os.path.join(self.task_dir, "images", fname))

    def _save_results_to_json(self):
        """
        Move all pkl files (if any) from the visualizations directory to the results directory and save the data from modified_predicted_tub_cell_data.pkl to results.json.

        Returns:
            dict: A dictionary containing the data from predicted_tub_cell_data.pkl.
        """
        # Check if a dir has any *.pkl files
        # Move all pkl files into the results dir
        pkl_paths = glob(os.path.join(self.task_dir, "visualizations", "*.pkl"))
        [
            shutil.move(p, os.path.join(self.task_dir, "results", os.path.basename(p)))
            for p in pkl_paths
        ]

        
        pkl_fpath = glob(os.path.join(
            self.task_dir, "results", "*_modified_predicted_tub_cell_data.pkl"
            )
        )

        results_fpath = os.path.join(self.task_dir, "results", "results.json")
        
        for pkl_file in pkl_fpath:
            if not os.path.isfile(pkl_file):
                return {}
            
        data_dict = (PickleParser(pkl_fpath).parse())

        if not os.path.isfile(results_fpath):
            with open(
                os.path.join(self.task_dir, "results", "results.json"), "w"
            ) as json_file:
                json.dump(data_dict, json_file)

        return data_dict

    def execute(self):
        """
        Executes StageTool Docker command in the background.

        The method runs a StageTool Docker command in the background using the `os.system` function.

        Args:
            None

        Returns:
            None
        """
    
        container_name = f"{DOCKER_IMAGE_NAME}{DOCKER_IMAGE_VERSION}"
        input_image_path = f"{self.task_dir}/images"
        onlyfiles = [f for f in listdir(input_image_path) if isfile(join(input_image_path, f))]
        for image_name in onlyfiles:
            image_name_no_ending = image_name.split(".")[0]
            image_name_no_ending_sanitized = re.sub(REPLACE_REGEX, '_', image_name_no_ending)
            image = input_image_path+"/"+image_name

            docker_input_path = "/app/input/"
            docker_output_path = "/app/output/"


            create_dir_command = f"docker exec {container_name} mkdir {docker_input_path}{image_name_no_ending_sanitized}/"
            process_copy_command = os.system(create_dir_command)

            create_dir_command = f"docker exec {container_name} mkdir {docker_output_path}{image_name_no_ending_sanitized}/"
            process_copy_command = os.system(create_dir_command)

            create_dir_command = f"docker exec {container_name} ls {docker_input_path}"
            process_copy_command = os.system(create_dir_command)

            copy_command = f"docker cp {image} {container_name}:{docker_input_path}{image_name_no_ending_sanitized}/"
            process_copy_command = os.system(copy_command)

            exec_command = f"docker exec {container_name} python /app/STAGETOOL.py --image_name {image_name_no_ending_sanitized}"
            process_exec_command = os.system(exec_command)

            os.system(f"mkdir -p {self.task_dir}/visualizations")
            out_copy_command = f"docker cp {container_name}:{docker_output_path}{image_name_no_ending_sanitized}/. {self.task_dir}/visualizations/"
            process_out_copy_command = os.system(out_copy_command)

            exec_command = f"docker exec {container_name} rm -rf {docker_input_path}{image_name_no_ending_sanitized} && rm -rf {docker_output_path}"
            process_exec_command = subprocess.Popen(exec_command, shell=True)

            exec_command = f"docker exec {container_name} rm -rf {docker_output_path}{image_name_no_ending_sanitized}"
            process_exec_command = subprocess.Popen(exec_command, shell=True)

            time.sleep(3)

            os.system(f"mkdir -p {self.task_dir}/resultconversions")
            os.system(f"mkdir -p {self.task_dir}/imageconversions")            
            try:
                im = Image.open(f"{self.task_dir}/images/{image_name}")
                print (f"Generating preview jpeg for the tiff image {image_name_no_ending}")
                im.thumbnail(im.size)
                im.save(f"{self.task_dir}/imageconversions/{image_name_no_ending}.jpg", "JPEG", quality=100)

                print (f"Generating result jpeg for the tiff image {image_name_no_ending}")
                pred_im = Image.open(f"{self.task_dir}/visualizations/{image_name}")
                pred_im.thumbnail(pred_im.size)
                pred_im.save(f"{self.task_dir}/resultconversions/result_{image_name_no_ending}.jpg", "JPEG", quality=100)
            except Exception as e:
                print(e)



    def status(self) -> str:
        if not os.path.isdir(self.task_dir):
            return Status.PENDING.name.lower()        

        # Change this logic.
        # It's safer to check that each filename in images
        # has a corresponding filename in visualizations.
        has_results = glob(os.path.join(self.task_dir, "results", "*.pkl"))

        if has_results:
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
        vis_fnames = glob(os.path.join(self.task_dir, "visualizations", "*"))
        rescon_fnames = glob(os.path.join(self.task_dir, "resultconversions", "*"))
        imgcon_fnames = glob(os.path.join(self.task_dir, "imageconversions", "*"))

        # TEMPORARY:
        #  - Remove pred_ prefix from visualization filenames
        #  - Consider implementing this at the Docker level
        for p in vis_fnames:
            fname = os.path.basename(p)
            if fname.startswith("numbered_pred_"):
                new_fname = fname.replace("numbered_pred_", "")
                os.rename(
                    os.path.join(self.task_dir, "visualizations", fname),
                    os.path.join(self.task_dir, "visualizations", new_fname),
                )

        results_data = self._save_results_to_json()
        vis_fnames = sorted(glob(os.path.join(self.task_dir, "visualizations", "*")))

        return {
            "id": self.id,
            "status": self.status(),
            "image_filenames": [os.path.basename(i) for i in img_fnames],
            "visualization_filenames": [os.path.basename(i) for i in vis_fnames],
            "resultconversion_filenames":[os.path.basename(i) for i in rescon_fnames],
            "imageconversion_filenames":[os.path.basename(i) for i in imgcon_fnames],
            "results": results_data,
        }

    def destroy(self) -> None:
        """
        Deletes the task directory.

        Args:
            None
        Returns:
            None
        """
        if os.path.isdir(self.task_dir):
            shutil.rmtree(self.task_dir)


class PickleParser:
    def __init__(self, pickle_path: str):
        self.pickle_path = pickle_path

    def parse(self) -> dict:
        """
        Parses a pickle file and returns a dictionary with the parsed data.

        Args:
            None
        Returns:
            dict: A dictionary containing the parsed data.
        """
        data_dict = {}

        for file_path in self.pickle_path:
            with open(file_path, "rb") as f:
                results = pickle.load(f)

            for img_name in results:
                img_data_dict = {f"{img_name}": {"tubules": []}}

                # get tubule data
                tubules = results[img_name]["tubules"]

                for tub in tubules:
                    tub_dict = {}
                    tub_dict["id"] = tub["id"]
                    tub_dict["label"] = tub["label"]
                    tub_dict["score"] = tub["score"]
                    tub_dict["box"] = tub["box"]
                    tub_dict["contours"] = [
                        j.flatten().tolist() for i in tub["contours"] for j in i
                    ]

                    tub_dict["cells"] = {
                        "labels": tub["cells"]["labels"],
                        "scores": tub["cells"]["scores"],
                        "boxes": [list(map(int, b)) for b in tub["cells"]["boxes"]],
                    }

                    img_data_dict[f"{img_name}"]["tubules"].append(tub_dict)

                data_dict.update(img_data_dict)

        return data_dict
