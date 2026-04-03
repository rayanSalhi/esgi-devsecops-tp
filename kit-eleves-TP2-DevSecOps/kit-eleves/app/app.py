from flask import Flask, jsonify, request, render_template
import redis
import os
import uuid

app = Flask(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")

try:
    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD if REDIS_PASSWORD else None,
        decode_responses=True,
    )
    r.ping()
except Exception:
    r = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.route("/readyz")
def readyz():
    if r is None:
        return jsonify({"status": "unavailable", "reason": "redis not connected"}), 503
    try:
        r.ping()
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "unavailable", "reason": str(e)}), 503


@app.route("/tasks", methods=["GET"])
def list_tasks():
    if r is None:
        return jsonify({"error": "storage unavailable"}), 503
    keys = r.keys("task:*")
    tasks = []
    for key in keys:
        data = r.hgetall(key)
        data["id"] = key.split(":", 1)[1]
        tasks.append(data)
    tasks.sort(key=lambda t: t.get("created_at", ""))
    return jsonify(tasks)


@app.route("/tasks", methods=["POST"])
def create_task():
    if r is None:
        return jsonify({"error": "storage unavailable"}), 503
    body = request.get_json(silent=True)
    if not body or "title" not in body:
        return jsonify({"error": "field 'title' is required"}), 400
    task_id = str(uuid.uuid4())
    import datetime
    task = {
        "title": body["title"],
        "done": "false",
        "created_at": datetime.datetime.utcnow().isoformat(),
    }
    r.hset(f"task:{task_id}", mapping=task)
    task["id"] = task_id
    return jsonify(task), 201


@app.route("/tasks/<task_id>", methods=["PATCH"])
def update_task(task_id):
    if r is None:
        return jsonify({"error": "storage unavailable"}), 503
    key = f"task:{task_id}"
    if not r.exists(key):
        return jsonify({"error": "not found"}), 404
    body = request.get_json(silent=True) or {}
    if "done" in body:
        r.hset(key, "done", str(body["done"]).lower())
    data = r.hgetall(key)
    data["id"] = task_id
    return jsonify(data)


@app.route("/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    if r is None:
        return jsonify({"error": "storage unavailable"}), 503
    key = f"task:{task_id}"
    if not r.exists(key):
        return jsonify({"error": "not found"}), 404
    r.delete(key)
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
