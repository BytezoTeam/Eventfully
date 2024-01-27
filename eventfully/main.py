import atexit

from flask import Flask, render_template, request, jsonify
from flask_apscheduler import APScheduler

import eventfully.database as db
import eventfully.emails as emails
import eventfully.categorize as categorize
import eventfully.scraping as scraping


class Config:
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())


# Scheduled tasks
@scheduler.task("cron", id="get_emails", hour=0)
def get_emails():
    emails.main()


@scheduler.task("cron", id="scrape", hour=1)
def scrape():
    scraping.main()


@scheduler.task("cron", id="categorize", hour=6)
def categorize():
    categorize.main()


scheduler.start()


# Routes
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
