import atexit

from flask import Flask, render_template, request, make_response, redirect
from flask_apscheduler import APScheduler

import eventfully.database as db
import eventfully.sources.main as sources
from eventfully.utils import create_user_id


class Config:
    SCHEDULER_API_ENABLED = True


app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())


# Scheduled tasks
@scheduler.task("cron", id="get_data", hour=0)
def get_data():
    app.logger.info("JOB: get_data")
    sources.main()


scheduler.start()


# Routes
@app.route("/", methods=["GET"])
def index():
    return render_template('index.html')


# Check the Cookie or redirect to log in
@app.route("/accounts/add_cookie")
def check_account():
    userID = request.cookies.get('userID')
    if userID:
        return db.get_user_data(request.cookies.get("userID"))
    else:
        return redirect("/", 302)



# Log out and delete the UserID-Cookie    
@app.route("/accounts/delete")
def delete_account():
    db.delete_account(request.cookies.get("userID"))
    return redirect("/", 302)


# Adding the User Data to the Database and setting the UserID-Cookie
@app.route("/accounts/add_account", methods=["POST"])
def register_user():
    userID = create_user_id()
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    db.add_account(username, password, userID, email)
    resp = make_response(redirect("/accounts/add_cookie", 302))
    resp.set_cookie('userID', userID, secure=True, httponly=True)
    return resp


# Checking Password and Username and setting UserID-Cookie
@app.route("/accounts/check_account")
def login_user():
    userID = db.authenticate_user(request.args.get("username"), request.args.get("password"))
    if userID:
        resp = make_response(redirect("/accounts/add_cookie", 302))
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


@app.route("/api/search", methods=["GET"])
def get_events():
    category = request.args.get("kategorie", "")
    therm = request.args.get("search", "")
    location = request.args.get("ort", "")
    # distance = request.args.get("distanz")

    result = db.search_events(therm, category)

    return render_template("api/events.html", events=result)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
