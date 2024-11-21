import atexit
from http import HTTPStatus
from uuid import uuid4

from flask import Flask, make_response
from flask_apscheduler import APScheduler

from eventfully.database import crud
from eventfully.logger import log
from eventfully.search import post_processing, crawl
from eventfully.routes import account, api, index, legal_notice

log.info("Starting Server ...")
crud.create_tables()

app = Flask(__name__)
app.config["SECRET_KEY"] = uuid4().hex
app.config["WTF_CSRF_ENABLED"] = False


# Background tasks mainly for searching for events
scheduler = APScheduler()
scheduler.init_app(app)
atexit.register(lambda: scheduler.shutdown())

scheduler.add_job("post_process", post_processing.main, trigger="interval", seconds=60, max_instances=1)
scheduler.add_job("collect", crawl.main, trigger="cron", day="*", max_instances=1)

scheduler.start()


@app.errorhandler(500)
def internal_error_server_error(error):
    """
    When something goes wrong on the server side, this error is returned.
    """

    log.error("Internal Server Error: " + str(error))
    return make_response(), HTTPStatus.INTERNAL_SERVER_ERROR


app.register_blueprint(api.bp)
app.register_blueprint(index.bp)
app.register_blueprint(legal_notice.bp)
# app.register_blueprint(account.bp)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
