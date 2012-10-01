from georefine.app import app, db 
from flask import (request, render_template, redirect, url_for, flash, 
                   session)
from flask_login import (LoginManager, current_user, login_required,
                            login_user, logout_user, UserMixin, AnonymousUser,
                            confirm_login, fresh_login_required)
from flaskext.openid import OpenID

open_id = OpenID(app)

class AdminUser(UserMixin):
    id = u'1'
    name = 'admin'
    active = True

    def is_active(self):
        return self.active

admin_user = AdminUser()

login_manager = LoginManager()
login_manager.setup_app(app)

login_manager.anonymous_user = AnonymousUser
login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."
login_manager.refresh_view = "reauth"

@login_manager.user_loader
def load_user(id):
    if int(id) == 1:
        return admin_user
    else:
        return None

@app.route("/login", methods=["GET", "POST"])
@open_id.loginhandler
def login():
    if request.method == "POST":
        openid = request.form.get('openid')
        if openid:
            return open_id.try_login(openid)
    return render_template("login.html", next=open_id.get_next_url(),
                           error=open_id.fetch_error())

@open_id.after_login
def _do_login(resp):
    """This is called when login with OpenID succeeded and it's not
    necessary to figure out if this is the users's first login or not.
    This function has to redirect otherwise the user will be presented
    with a terrible URL which we certainly don't want.
    """
    session['openid'] = resp.identity_url
    flash(u'Successfully signed in')
    login_user(admin_user, remember=True)
    return redirect(open_id.get_next_url())

@app.route("/logout")
@login_required
def logout():
    session.pop('openid', None)
    logout_user()
    flash("Logged out.")
    return redirect(open_id.get_next_url())
