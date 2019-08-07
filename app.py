from flask import Flask, flash, redirect, render_template, url_for, session, logging, request
from flask_mysqldb import MySQL
from functools import wraps
from wtforms import StringField, PasswordField, TextAreaField, validators, Form
from passlib.apps import custom_app_context as pwd_context

app = Flask(__name__)

# Config MYSQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Ayush043@'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSOR'] = 'DictCursor'

# Intilialize MYSQL
mysql = MySQL(app)


class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Password do not match')])
    confirm = PasswordField('Confirm Password')


class ArticlesForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=1)])


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


# check if user logged in or not
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/articles')
def articles():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("select * from articles")

    article = cur.fetchall()

    # Close Cursor
    cur.close()

    if result > 0:
        return render_template('articles.html', article=article)
    else:
        msg = 'No Article is found'
        return render_template('articles.html', msg=msg)


@app.route('/article/<string:id>/')
def article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Article
    result = cur.execute("select * from articles where id=%s", [id])

    article = cur.fetchone()

    # Close Cursor
    cur.close()

    return render_template('article.html', article=article)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = pwd_context.hash(str(form.password.data))

        # Create Cursor
        cur = mysql.connection.cursor()

        cur.execute("insert into users(name, email, username, password) values(%s, %s, %s, %s)",
                    (name, email, username, password))

        # Commit to database
        mysql.connection.commit()

        # Close Cursor
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create Cursor
        cur = mysql.connection.cursor()

        # Get Usernames
        result = cur.execute("select * from users where username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Password
            if pwd_context.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                flash('You are now logged in', 'success')

                # Close Cursor
                cur.close()
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login Details'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create Cursor
    cur = mysql.connection.cursor()

    # Get Articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    # Close Cursor
    cur.close()

    if result > 0:
        return render_template('dashboard.html', article=articles)
    else:
        msg = 'No Article is found'
        return render_template('dashboard.html', msg=msg)


@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out')
    return redirect(url_for('login'))


@app.route('/add_articles', methods=['GET', 'POST'])
@is_logged_in
def add_articles():
    form = ArticlesForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        cur.execute("insert into articles(title, body, author) values(%s, %s, %s)", (title, body, session['username']))

        # Commit to database
        mysql.connection.commit()

        # Close Cursor
        cur.close()

        flash('Article Added', 'success')

        return redirect(url_for('dashboard'))
    return render_template('add_articles.html', form=form)


@app.route('/edit_articles', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()

    result = cur.execute("select * from articles where id = %s", [id])

    article = cur.fetchone()

    form = ArticlesForm(request.form)

    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()

        cur.execute("update articles set title = %s, body = %s where id = %s", (title, body, id))

        # Commit to database
        mysql.connection.commit()

        # Close Cursor
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))
    return render_template('edit_articles.html', form=form)


@app.route('/delete_articles/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("delete from articles where id = %s", [id])

    # Commit to database
    mysql.connection.commit()

    # Close Cursor
    cur.close()

    flash('Article Updated', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.secret_key = 'secret123'
    app.run(debug=True)
