from classes import Task, TaskNotFound, TaskCreationError
from flask import Flask, abort, jsonify, request, send_file
from dotenv import load_dotenv
import os
import mimetypes
import io

load_dotenv()
app = Flask(__name__)


app.config["ENV"] = os.getenv("ENV", "development")


if app.config["ENV"] == "development" or app.config["ENV"] == "testing":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data-dev")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@app.route("/task", methods=["GET"])
def get_task():
    task_id = request.args.get("id")

    try:
        task = Task(id=task_id, images=None)
        return jsonify(task.data()), 200
    except TaskNotFound:
        return jsonify({"error": "Task not found"}), 404


@app.route("/task", methods=["POST"])
def post_task():
    if "images" not in request.files:
        abort(400)

    try:
        images = request.files.getlist("images")

        task = Task(images=images)
        if not os.environ["ENV"] == "testing":
            task.execute()

        return jsonify(task.data()), 201
    except TaskCreationError:
        abort(500)


@app.route("/images", methods=["GET"])
def get_image():
    task_id = request.args.get("task_id")
    filename = request.args.get("filename")

    if not task_id or not filename:
        abort(400, description="Required query parameters are missing.")

    image_path = os.path.join(DATA_DIR, task_id, "images", filename)

    if os.path.exists(image_path):
        with open(image_path, "rb") as img:
            img_data = img.read()
        return send_file(
            io.BytesIO(img_data), mimetype=mimetypes.guess_type(image_path)[0]
        )
    else:
        abort(404, description="Image not found.")


@app.route("/visualizations", methods=["GET"])
def get_visualization():
    task_id = request.args.get("task_id")
    filename = request.args.get("filename")

    if not task_id or not filename:
        abort(400, description="Required query parameters are missing.")

    try:
        task = Task(id=task_id)
        vis_path = os.path.join(DATA_DIR, task.id, "visualizations", filename)
        with open(vis_path, "rb") as vis:
            vis_data = vis.read()
        return send_file(
            io.BytesIO(vis_data), mimetype=mimetypes.guess_type(vis_path)[0]
        )
    else:
        abort(404, description="Visualization not found.")


if __name__ == "__main__":
    if __name__ == "__main__":
        if app.config["ENV"] == "development" or app.config["ENV"] == "testing":
            app.run(debug=True)
        else:
            app.run()
