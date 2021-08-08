from app import auth
from flask import Blueprint
from flask import redirect
from flask import g
from flask import flash
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from app.db import get_db
from app.auth import login_required

bp = Blueprint("admin", __name__, '''url_prefix="/group"''')

@bp.route("/admin", methods=("GET", "POST"))
@login_required
def admin_page():
    if not g.user["admin"]:
        return render_template('page-404.html'), 404



    return render_template("page-blank.html", username = g.user["username"], admin=g.user["admin"])

#email for everyone

#message on homepage

#groupstage evaulation
#groupstage feedback for result of posting in client
#final bet evaulation, hand->user-by user, setting success flag true or false (after tournament ending!)

#odd submitting (for matches after groupstage)

# seperate final bet table for readabilty

#other:
#session timeout
#message after redirect
#timed callback -> update match database
#timed email notifications!
#disqus

# flask-init db, read teams from csv!

# html template -> removing deadlinks + dashboard problem + username problem