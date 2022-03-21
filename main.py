from flask import Flask, render_template, request, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, UserMixin, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, TextAreaField, SubmitField, SelectField, EmailField, PasswordField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

uri = os.getenv("DATABASE_URL", "sqlite:///todo.db")  # or other relevant config var
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)


class TodoApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="tasks")
    title = db.Column(db.String(100))
    description = db.Column(db.String(500))
    priority = db.Column(db.String(25))
    date = db.Column(db.String(100))
    resolved = db.Column(db.Integer)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    password = db.Column(db.String(100), unique=True, nullable=False)
    tasks = relationship("TodoApp", back_populates="author")


db.create_all()


class TodoForm(FlaskForm):
    title = StringField('Task')
    description = TextAreaField('Description')
    priority = SelectField('Priority', choices=[' ', 'Low', 'Medium', 'High'])
    submit = SubmitField('Add')


class SignUpForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class SignInForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/", methods=["GET", "POST"])
def home():
    if current_user.is_authenticated:
        open_todos = TodoApp.query.filter(TodoApp.resolved == 0).filter(TodoApp.author_id == current_user.id).all()
        count_open = TodoApp.query.filter(TodoApp.resolved == 0).filter(TodoApp.author_id == current_user.id).count()
        count_resolved = TodoApp.query.filter(TodoApp.resolved == 1).filter(TodoApp.author_id == current_user.id).count()
        task_form = TodoForm()
        if task_form.validate_on_submit():
            new_todo = TodoApp(title=task_form.title.data, description=task_form.description.data,
                               priority=task_form.priority.data, date=datetime.now().strftime("%c"), resolved=0,
                               author=current_user)
            db.session.add(new_todo)
            db.session.commit()
            return redirect(url_for('home'))
        return render_template("index.html", todos=open_todos, task_form=task_form, count=count_open,
                               resolved=count_resolved)
    else:
        sign_in_form = SignInForm()
        if sign_in_form.validate_on_submit():
            user = User.query.filter_by(email=sign_in_form.email.data).first()
            if user:
                if check_password_hash(user.password, sign_in_form.password.data):
                    login_user(user)
                    return redirect(url_for('home'))
        return render_template("index.html", sign_in_form=sign_in_form)


@app.route("/task/<int:task>")
@login_required
def show_task(task):
    requested_task = TodoApp.query.get(task)
    return render_template("show.html", task=requested_task)


@app.route("/resolved")
@login_required
def show_resolved():
    resolved_todos = TodoApp.query.filter(TodoApp.resolved == 1).filter(TodoApp.author_id == current_user.id).all()
    return render_template("resolved.html", todos=resolved_todos)


@app.route("/delete/<int:task>")
@login_required
def delete_task(task):
    get_task = TodoApp.query.get(task)
    db.session.delete(get_task)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/done/<int:task>")
@login_required
def resolve_task(task):
    get_task = TodoApp.query.get(task)
    get_task.resolved = 1
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/edit/<int:task>", methods=["GET", "POST"])
@login_required
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


@app.route("/signup", methods=["GET", "POST"])
def signup():
    sign_up_form = SignUpForm()
    if sign_up_form.validate_on_submit():
        new_user = User(email=sign_up_form.email.data, name=sign_up_form.name.data,
                        password=generate_password_hash(sign_up_form.password.data, method='pbkdf2:sha256',
                                                        salt_length=8))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('signup.html', sign_up_form=sign_up_form)


@app.route('/logout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
