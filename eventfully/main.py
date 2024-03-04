import atexit
from flask_apscheduler import APScheduler
from flask import Flask, render_template, request, jsonify, make_response, redirect
from uuid import uuid4
from eventfully.categorize import get_topic
from eventfully.utils import create_user_id
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
    app.logger.info("JOB: get_emails")
    try:
        emails.main()
    except Exception as e:
        app.logger.error(e)


@scheduler.task("cron", id="scrape", hour=1)
def scrape():
    app.logger.info("JOB: scrape")
    try:
        scraping.main()
    except Exception as e:
        app.logger.error(e)


@scheduler.task("cron", id="categorize", hour=6)
def categorize():
    app.logger.info("JOB: categorize")
    try:
        categorize.main()
    except Exception as e:
        app.logger.error(e)


scheduler.start()


# Routes
@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')


# Check the Cookie or redirect to log in
@app.route("/accounts/addCookie")
def checkAccount():
    userID = request.cookies.get('userID')
    if userID:
        return db.get_User_Data(request.cookies.get("userID"))
    else:
        return redirect("/", 302)


# TODO: reimplement (Doesn't work)
# Log out and delete the UserID-Cookie
# @app.route("/accounts/logout")
# def logout():
#    resp = make_response(redirect("/", 302))
#    resp.set_cookie('userID', '', expires=0, secure=True, httponly=True)
#    return resp


# Log out and delete the UserID-Cookie    
@app.route("/accounts/delete")
def deleteAccount():
    db.delete_Account(request.cookies.get("userID"))
    # return redirect("/accounts/logout", 302)
    return redirect("/", 302)


# Adding the User Data to the Database and setting the UserID-Cookie
@app.route("/accounts/addAccount")
def registerUser():
    userID = create_user_id()
    db.add_Account(request.args.get("username"), request.args.get("password"), userID, request.args.get("email"))
    resp = make_response(redirect("/accounts/addCookie", 302))
    resp.set_cookie('userID', userID, secure=True, httponly=True)
    return resp


# Checking Password and Username and setting UserID-Cookie
@app.route("/accounts/checkAccount")
def loginUser():
    userID = db.authenticate_user(request.args.get("username"), request.args.get("password"))
    if userID:
        resp = make_response(redirect("/accounts/addCookie", 302))
        resp.set_cookie('userID', userID, secure=True, httponly=True)
        return resp
    else:
        return redirect("/login", 302)


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


@app.route("/api/search", methods=["GET"])
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
