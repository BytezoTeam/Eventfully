from flask import Flask, render_template, request
from uuid import uuid4
from accessibility_events.categorize import get_topic
import accessibility_events.database as db


app = Flask(__name__)


@app.route('/', methods=["GET"])
def index():
    return render_template('index.html')


@app.route("/api/add_event", methods=["GET"])
def add_event():
    # TODO: validation
    # location = request.args.get("location", "")
    tag = get_topic(request.args.get("description", "") + request.args.get("title", ""))

    db.Event.create(
        id=uuid4(),
        title=request.args.get("title", "---"),
        description=request.args.get("description", "---"),
        link=request.args.get("link", "---"),
        price=request.args.get("price", "---"),
        tags=tag,
        start_date=request.args.get("start_date", "---"),
        end_date=request.args.get("end_date", "---"),
        age=request.args.get("age", "---"),
        accessibility=request.args.get("accessibility", "---"),
        location=None
    )

    return "", 200


def main():
    app.run()


if __name__ == '__main__':
    main()
