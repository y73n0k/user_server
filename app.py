import os
import requests
from flask import Flask, session, abort, render_template, redirect, request
from werkzeug.utils import secure_filename

from forms.comments import CommentForm
from forms.users import LoginForm, RegisterForm
from forms.videos import VideoForm

app = Flask(__name__)
app.secret_key = "v3ry_s3cr37_k3y_wh1ch_y0u_w1ll_n3v3r_gu355"

DATABASE_URL = "http://127.0.0.1:4610"


def get_user_data():
    access_token = session.get("access_token", None)
    if access_token is None:
        return False, {}
    resp = requests.get(
        DATABASE_URL + "/get_me", headers={"Authorization": "Bearer " + access_token}
    ).json()
    if "user" in resp:
        return True, resp["user"]
    return False, {}


@app.route("/refresh")
def refresh():
    refresh_token = session.get("refresh_token", "")
    resp = requests.post(
        DATABASE_URL + "/refresh", headers={"Authorization": "Bearer " + refresh_token}
    ).json()
    access_token = resp.get("access_token", None)
    if access_token is not None:
        session["access_token"] = access_token
        is_auth, user_data = get_user_data()
        return render_template(
            "success.html", title="Refresh token", is_auth=is_auth, **user_data
        )
    return render_template("failed.html", title="Refresh token")


@app.route("/user/<string:slug>")
def user(slug):
    is_auth, user_data = get_user_data()
    if not is_auth:
        refresh()
        is_auth, user_data = get_user_data()
    data = requests.get(DATABASE_URL + "/users/" + slug).json()
    if "message" in data:
        return render_template(
            "user.html",
            error="User not founded",
            title="Not founded",
            is_auth=is_auth,
            **user_data
        )
    data = data["user"]
    return render_template(
        "user.html", title=data["slug"], user=data, is_auth=is_auth, **user_data
    )


@app.route("/me", methods=["GET", "POST"])
def current_user():
    is_auth, user_data = get_user_data()
    if not is_auth:
        refresh()
        is_auth, user_data = get_user_data()
        if not is_auth:
            abort(403, description="Please login in")
    form = VideoForm()
    if form.validate_on_submit():
        access_token = session.get("access_token")
        filename = (
            "temp/"
            + user_data["slug"]
            + "."
            + secure_filename(form.video.data.filename).split(".")[-1]
        )
        with open(filename, "wb") as f:
            f.write(form.video.data.stream.read())
        f = open(filename, "rb")
        files = {"file": f}
        answer = requests.post(
            DATABASE_URL + "/videos/",
            files=files,
            headers={"Authorization": "Bearer " + access_token},
            data={
                "title": form.title.data,
                "authors": form.authors.data,
                "description": form.description.data,
            },
        ).json()
        f.close()
        os.remove(filename)
    return render_template(
        "current_user.html", title="Me", form=form, is_auth=is_auth, **user_data
    )


@app.route("/")
def index():
    is_auth, user_data = get_user_data()
    if not is_auth:
        refresh()
        is_auth, user_data = get_user_data()
    all_videos = requests.get(DATABASE_URL + "/videos").json()["videos"]
    return render_template(
        "videos.html",
        all_videos=all_videos,
        title="Videos",
        is_auth=is_auth,
        **user_data
    )


@app.route("/delete_comment/<int:id>")
def delete_comment(id):
    is_auth, user_data = get_user_data()
    if not is_auth:
        refresh()
        is_auth, user_data = get_user_data()
        if not is_auth:
            return False
    access_token = session.get("access_token")
    answer = requests.delete(
        DATABASE_URL + "/comments/" + str(id),
        headers={"Authorization": "Bearer " + access_token},
    ).json()
    return redirect(request.referrer)


@app.route("/delete_video/<string:short_name>")
def delete_video(short_name):
    is_auth, user_data = get_user_data()
    if not is_auth:
        refresh()
        is_auth, user_data = get_user_data()
        if not is_auth:
            return False
    access_token = session.get("access_token")
    answer = requests.delete(
        DATABASE_URL + "/videos/" + short_name,
        headers={"Authorization": "Bearer " + access_token},
    ).json()
    return redirect(request.referrer)


@app.route("/watch/<string:slug>", methods=["GET", "POST"])
def watch(slug):
    is_auth, user_data = get_user_data()
    form = CommentForm()
    video = requests.get(DATABASE_URL + "/videos/" + slug).json()
    video = video.get("video", None)
    if not is_auth:
        refresh()
        is_auth, user_data = get_user_data()
    if form.validate_on_submit():
        access_token = session.get("access_token")
        if not is_auth:
            return render_template(
                "video.html", is_auth=is_auth, error="Зайдите в аккаунт!"
            )
        requests.post(
            DATABASE_URL + "/comments/" + video["short_name"],
            data={
                "text": form.text.data,
                "video_id": video["id"],
                "author_id": user_data["id"],
            },
            headers={"Authorization": "Bearer " + access_token},
        )
        return redirect("/watch/" + slug)
    if video is None:
        return render_template(
            "video.html", is_auth=is_auth, error="Видео не найдено!", **user_data
        )
    video["url"] = DATABASE_URL + video["url"]
    return render_template(
        "video.html", form=form, is_auth=is_auth, video=video, **user_data
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    is_auth, user_data = get_user_data()
    form = LoginForm()
    if form.validate_on_submit():
        slug = form.slug.data
        password = form.password.data
        data = requests.get(
            DATABASE_URL + "/get_token", params={"slug": slug, "password": password}
        ).json()
        if "error" in data:
            return render_template(
                "login.html",
                form=form,
                is_auth=is_auth,
                message="Wrong username or password",
                title="Log in",
                **user_data
            )
        session["access_token"] = data["access_token"]
        session["refresh_token"] = data["refresh_token"]
        return redirect("/me")
    return render_template(
        "login.html", form=form, is_auth=is_auth, title="Log in", **user_data
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    is_auth, user_data = get_user_data()
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        slug = form.slug.data
        password = form.password.data
        password_again = form.password.data
        if password == password_again:
            data = requests.post(
                DATABASE_URL + "/users",
                data={"name": name, "slug": slug, "password": password},
            ).json()
            if "error" in data:
                return render_template(
                    "login.html",
                    form=form,
                    is_auth=is_auth,
                    message="Wrong username or password",
                    title="Log in",
                    **user_data
                )
            session["access_token"] = data["access_token"]
            session["refresh_token"] = data["refresh_token"]
            return redirect("/me")
        else:
            return render_template(
                "register.html",
                form=form,
                is_auth=is_auth,
                title="Register",
                message="Пароль не совпадают",
                **user_data
            )
    return render_template(
        "register.html", form=form, is_auth=is_auth, title="Register", **user_data
    )


@app.route("/logout")
def logout():
    session.pop("access_token")
    session.pop("refresh_token")
    return redirect("login")


if __name__ == "__main__":
    app.run()
