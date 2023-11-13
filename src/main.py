from classes import Task, TaskNotFound, TaskCreationError
from flask import Flask, abort, jsonify, request, send_file
from dotenv import load_dotenv
import os
import mimetypes

load_dotenv()
app = Flask(__name__)
app.config["ENV"] = os.getenv("ENV", "development")


if app.config["ENV"] == "development":
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data-dev")
else:
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@app.route("/task", methods=["GET"])
def get_task():
    task_id = request.args.get("id")

    try:
        task = Task(id=task_id)
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
        if app.config["ENV"] != "development":
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
        return send_file(image_path, mimetype=mimetypes.guess_type(image_path)[0])
    else:
        abort(404, description="Image not found.")


@app.route("/visualizations", methods=["GET"])
def get_visualization():
    task_id = request.args.get("task_id")
    filename = request.args.get("filename")

    if not task_id or not filename:
        abort(400, description="Required query parameters are missing.")

    vis_path = os.path.join(DATA_DIR, task_id, "visualizations", filename)

    if os.path.exists(vis_path):
        return send_file(vis_path, mimetype=mimetypes.guess_type(vis_path)[0])
    else:
        abort(404, description="Visualization not found.")


if __name__ == "__main__":
    if __name__ == "__main__":
        if app.config["ENV"] == "development":
            app.run(debug=True)
        else:
            app.run()
