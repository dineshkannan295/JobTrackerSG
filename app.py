from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobs.db"
db = SQLAlchemy(app)

# Job model
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shipment_ref = db.Column(db.String(100))
    importer_name = db.Column(db.String(100))
    job_received = db.Column(db.String(100))
    allocated_to = db.Column(db.String(100))
    status = db.Column(db.String(50), default="Pending")

@app.before_first_request
def create_tables():
    db.create_all()

@app.route("/")
def index():
    jobs = Job.query.all()
    return render_template("index.html", jobs=jobs)

@app.route("/add", methods=["POST"])
def add_job():
    shipment_ref = request.form["shipment_ref"]
    importer_name = request.form["importer_name"]
    job_received = request.form["job_received"]
    allocated_to = request.form["allocated_to"]
    new_job = Job(
        shipment_ref=shipment_ref,
        importer_name=importer_name,
        job_received=job_received,
        allocated_to=allocated_to
    )
    db.session.add(new_job)
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/update/<int:id>", methods=["POST"])
def update_status(id):
    job = Job.query.get_or_404(id)
    job.status = request.form["status"]
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
