from flask import Flask, render_template, request, jsonify
from uuid import uuid4
from accessibility_events.categorize import get_topic
import accessibility_events.database as db


app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template('startPage.html', events=list(db.Event.select().dicts()))


@app.route("/api/events", methods=["GET"])
def events():
    return render_template("startPage.html", events=list(db.Event.select().dicts()))


@app.route("/filterseting", methods=["GET"])
def filtersetting():
    return render_template('filterseting.html')


# @app.route("/api/events/search")
# def search_events():
#     print(request.args)
#     return "", 200


@app.route("/api/events/search", methods=["GET"])
def getEvents():
    category = request.args.get("kategorie", "")
    therm = request.args.get("search", "")
    location = request.args.get("ort", "")
    # distance = request.args.get("distanz")

    # result = list(db.Event.select().where(
    #     (
    #         (db.Event.title ** f"{therm}%") |
    #         (db.Event.description ** f"%{therm}%")
    #     ) & (
    #         db.Event.tags ** f"%{category}%"
    #     ) & (
    #         db.Event.address ** f"%{location}%" |
    #         db.Event.city.name == location
    #     )
    # ).dicts())

    result = list(db.Event.select().where(
        (
            (db.Event.title ** f"{therm}%") |
            (db.Event.description ** f"%{therm}%")
        ) & (
            db.Event.tags ** f"%{category}%"
        )
    ).dicts())

    return render_template("events.html", events=result)


@app.route("/api/emails", methods=["GET"])
def emails():
    return jsonify(list(db.EMailContent.select().dicts()))


@app.route("/api/add_event", methods=["POST"])
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
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == '__main__':
    main()
