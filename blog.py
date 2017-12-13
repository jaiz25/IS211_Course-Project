#!usr/bin/env/python
# -*- coding: utf-8 -*-
"""IS211 Course Project: Blogging Application"""


import sqlite3
from flask import Flask, render_template, request, redirect, url_for, \
    abort, flash, session, g
from contextlib import closing


# conn = sqlite3.connect('users.db')
#
# login = (('admin', 'password'),
#          ('test', 'code'),
#          ('firstname', 'lastname'))
#
# with conn:
#
#     cur = conn.cursor()
#     cur.execute('DROP TABLE IF EXISTS users')
#     cur.execute('CREATE TABLE users(username text PRIMARY KEY not null, password text not null')
#     cur.executemany('INSERT INTO users VALUES(?, ?)', login)


DATABASE = 'entries.db'
DEBUG = True
USERNAME = 'admin'
PASSWORD = 'password'
SECRET_KEY = 'development key'


app = Flask(__name__)
app.config.from_object(__name__)


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
def welcome():
    cur = g.db.execute('select title, text from entries order by id desc')
    entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
    return render_template('index.html', entries=entries)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('dashboard'))
    return render_template('login.html', error=error)


@app.route('/dashboard')
def dashboard():
    cur = g.db.execute('select id, title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('dashboard.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    error = None
    if not session.get('logged_in'):
        abort(401)
    if request.method == 'POST':
        if request.form['title'] == "":
            error = "Please enter a title"
            return render_template('/dashboard.html', error=error)
        if request.form['text'] == "":
            error = "Please enter a text"
            return render_template('/dashboard.html', error=error)
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('dashboard'))


@app.route('/entry/<id>')
def entry_id(id):
    error = None
    cur = g.db.execute('select id, title, text from entries where id=?', (id,))
    edits = cur.fetchall()
    return render_template('edit.html', edits=edits)


@app.route('/edit_entry/<id>', methods=['POST'])
def edit_entry(id):
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('update entries set title = ?, text = ? where id = ?',
                 [request.form['title'], request.form['text'], id])
    g.db.commit()
    flash('Entry was successfully updated')
    return redirect(url_for('dashboard'))


@app.route('/delete', methods=['POST'])
def delete_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('delete from entries where id = ?', [request.form['entry_id']])
    g.db.commit()
    flash('Entry deleted')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
