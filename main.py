from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import re

uri = os.getenv("DATABASE_URL", "sqlite:///todo.db")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class TodoApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    priority = db.Column(db.String(25))
    date = db.Column(db.String(100))
    resolved = db.Column(db.Boolean())


db.create_all()


class TodoForm(FlaskForm):
    title = StringField('Task', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    priority = SelectField('Priority', choices=['Low', 'Medium', 'High'])
    submit = SubmitField('Add')


@app.route("/", methods=["GET", "POST"])
def home():
    open_todos = TodoApp.query.filter(TodoApp.resolved != 1).all()
    count_open = TodoApp.query.filter(TodoApp.resolved != 1).count()
    count_resolved = TodoApp.query.filter_by(resolved=1).count()
    form = TodoForm()
    if request.method == "POST":
        new_todo = TodoApp(title=form.title.data, description=form.description.data,
                           priority=form.priority.data, date=datetime.now().strftime("%c"), resolved=0)
        db.session.add(new_todo)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("index.html", todos=open_todos, form=form, count=count_open, resolved=count_resolved)


@app.route("/task/<int:task>")
def show_task(task):
    requested_task = TodoApp.query.get(task)
    return render_template("show.html", task=requested_task)


@app.route("/resolved")
def show_resolved():
    resolved_todos = TodoApp.query.filter(TodoApp.resolved == 1).all()
    return render_template("resolved.html", todos=resolved_todos)


@app.route("/delete/<int:task>")
def delete_task(task):
    get_task = TodoApp.query.get(task)
    db.session.delete(get_task)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/done/<int:task>")
def resolve_task(task):
    get_task = TodoApp.query.get(task)
    get_task.resolved = 1
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/edit/<int:task>", methods=["GET", "POST"])
def edit_task(task):
    task_to_edit = TodoApp.query.get(task)
    edit_form = TodoForm(title=task_to_edit.title,
                         description=task_to_edit.description, priority=task_to_edit.priority)
    if edit_form.validate_on_submit():
        task_to_edit.title = edit_form.title.data
        task_to_edit.description = edit_form.description.data
        task_to_edit.priority = edit_form.priority.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=edit_form)


if __name__ == "__main__":
    app.run(debug=True)
