from flask import Flask, render_template, request, jsonify

import eventfully.database as db

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')


@app.route("/add_window", methods=["GET"])
def add_window():
    return render_template('add_window.html')


@app.route("/filter_setting", methods=["GET"])
def filter_setting():
    return render_template('filter_setting.html')


# @app.route("/api/events/search")
# def search_events():
#     print(request.args)
#     return "", 200


@app.route("/api/events/search", methods=["GET"])
def get_events():
    category = request.args.get("kategorie", "")
    therm = request.args.get("search", "")
    location = request.args.get("ort", "")
    # distance = request.args.get("distanz")

    result = db.search_events(therm, category)

    return render_template("api/events.html", events=result)


@app.route("/api/emails", methods=["GET"])
def emails():
    return jsonify(list(db.EMailContent.select().dicts()))


# TODO: reimplement
# @app.route("/api/add_event", methods=["POST"])
# def add_event():
#     # location = request.args.get("location", "")
#     tag = get_topic(request.args.get("description", "") + request.args.get("title", ""))
#
#     event = db.Event(
#         title=request.args.get("title", ""),
#         description=request.args.get("description", ""),
#         link=request.args.get("link", ""),
#         price=request.args.get("price", ""),
#         tags=tag,
#         start_date=request.args.get("start_date", ""),
#         end_date=request.args.get("end_date", ""),
#         age=request.args.get("age", ""),
#         accessibility=request.args.get("accessibility", ""),
#         address=request.args.get("address", ""),
#         city=request.args.get("city", ""),
#     )
#     db.add_event(event)
#
#     return "", 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
