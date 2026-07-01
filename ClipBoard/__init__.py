from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
import pyperclip
import threading
import time

db = SQLAlchemy()

DATABASE = "sqlite:///ClipBoard.db"
toggle = False
last = ""


class ClipBoard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    starred = db.Column(db.Boolean, default=False)


def CheckCopy(app):
    global last

    with app.app_context():

        while True:

            try:

                text = pyperclip.paste()

                if text and text != last:

                    last = text

                    clip = ClipBoard.query.filter_by(
                        content=text
                    ).first()

                    if clip:
                        clip.timestamp = db.func.current_timestamp()
                        print(f"{text} - Already Exists")

                    else:

                        count = ClipBoard.query.count()

                        if count >= 100:

                            oldest = (
                                ClipBoard.query
                                .order_by(ClipBoard.timestamp)
                                .first()
                            )

                            if oldest:
                                db.session.delete(oldest)

                        new_clip = ClipBoard(
                            content=text
                        )

                        db.session.add(new_clip)

                        print(f"Copied : {text}")

                    db.session.commit()

                time.sleep(0.3)

            except Exception as e:
                print(e)
                time.sleep(1)


def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "aSBB"
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE

    db.init_app(app)

    with app.app_context():
        db.create_all()

    threading.Thread(
        target=CheckCopy,
        args=(app,),
        daemon=True
        
    ).start()

    @app.route("/")
    def home():
        top = ClipBoard.query.filter_by(starred=True).order_by(ClipBoard.timestamp.desc()).all()
        clips = (
            ClipBoard.query
            .order_by(ClipBoard.timestamp.desc())
            .all()
        )
        if top:
            combined = top + clips
            seen = set()
            tot = []
            for item in combined:
                if item.id not in seen:  # Use id or some unique identifier
                    seen.add(item.id)
                    tot.append(item)
        else:
            tot = clips

        return render_template(
            "index.html",
            clips=tot
        )
    @app.route("/delete/<int:id>",methods = ["POST"])
    def delete(id):
        clip = ClipBoard.query.filter_by(id=id).first()
        if clip:
            db.session.delete(clip)
            db.session.commit()
        return redirect("/")
    
    @app.route("/star/<int:id>",methods = ["POST"])
    def star(id):
        if request.method == "GET":
            return redirect("/")
        clip = ClipBoard.query.filter_by(id=id).first()
        if clip:
            if clip.starred:
                clip.starred = False
            else:
                clip.starred = True
            db.session.commit()
        return redirect("/")

    
    @app.route("/clear",methods = ["POST"])
    def clear():
        ClipBoard.query.delete()
        db.session.commit()
        return redirect("/")

    return app