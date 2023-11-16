"""
Utility script to explore the contents of the pickle file
and convert it to a JSON file for easier parsing.

At the current version, tub contour list elements need to be flattened
because there is an extra unnecessary dimension in the list.
"""
import os
import pickle
import json

pickle_path = os.path.join(os.path.dirname(__file__), "pkl", "pkl_from_0.1.0.pkl")

data_dict = {}

with open(pickle_path, "rb") as f:
    results = pickle.load(f)

for img_name in results:
    # parse cell data
    cell_data = results[img_name]["cell_data"]

    boxes = [list(map(int, b)) for b in cell_data["boxes"]]
    scores = cell_data["scores"]
    labels = cell_data["labels"]

    cell_data_dict = {
        "cell_data": {
            "boxes": boxes,
            "scores": scores,
            "labels": labels,
        }
    }

    # parse tub data
    tub_data = results[img_name]["tub_data"]
    labels = tub_data["labels"]
    scores = tub_data["scores"]
    boxes = [list(map(int, b)) for b in tub_data["boxes"]]
    contours = [j.flatten().tolist() for i in tub_data["contours"] for j in i]

    tub_data_dict = {
        "tub_data": {
            "labels": labels,
            "scores": scores,
            "boxes": boxes,
            "contours": contours,
        }
    }

    # assemble img name data dict
    data_dict[img_name] = {**cell_data_dict, **tub_data_dict}


with open("pickle_dump.json", "w") as json_file:
    json.dump(data_dict, json_file)
