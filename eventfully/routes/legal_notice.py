from http import HTTPStatus

from flask import Blueprint, render_template

from eventfully.config import CONFIG
from eventfully.routes.utils import translation_provider

bp = Blueprint('legal_notice', __name__)


@bp.route("/legal_notice", methods=["GET"])
def legal_notice():
    if not CONFIG.EVENTFULLY_LEGAL_NOTICE:
        return "", HTTPStatus.NOT_FOUND

    return render_template("legal_notice.html", t=translation_provider(), CONFIG=CONFIG)
