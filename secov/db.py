#!/usr/bin/python
# coding=utf-8
import os
import sqlite3
import config


def db_install():
    if not (os.path.isfile(config.sqli_db)):
        db = sqlite3.connect(config.sqli_db)
        cursor = db.cursor()

        cursor.execute('''
        CREATE TABLE project(pid INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)
        ''')
        cursor.execute('''
        CREATE TABLE route(rid INTEGER PRIMARY KEY AUTOINCREMENT, annotation TEXT, route TEXT, http_method TEXT, is_base_route TINYINT, file_path TEXT, pid INTEGER)
        ''')
        cursor.execute('''
        CREATE TABLE test(tid INTEGER PRIMARY KEY AUTOINCREMENT, annotation TEXT, route TEXT, http_method TEXT, pid INTEGER)
        ''')

        db.commit()
        db.close()
    else:
        pass


def connect():
    global db
    global cursor

    db = sqlite3.connect(config.sqli_db)
    cursor = db.cursor()


def close():
    db.close()


# Inserts new project to the DB and returns its project id
def insert_project(project):
    pid = False

    try:
        # Get an existing project's pid if already exists.
        cursor.execute('''SELECT pid FROM project WHERE name=?''', (project,))
        res = cursor.fetchone()
        if res:
            return res[0]

        # Insert or ignore if already exists
        cursor.execute('''INSERT OR IGNORE INTO project(name) VALUES(?)''', (project,))
        pid = cursor.lastrowid
        db.commit()

    except Exception as e:
        print(e)

    return pid


# Clear all the given project's routes and tests
def clear_project_data(pid):
    try:
        # Update if it exists
        cursor.execute('''DELETE FROM route WHERE pid=?''', (pid,))
        cursor.execute('''DELETE FROM test WHERE pid=?''', (pid,))
        db.commit()
    except Exception as e:
        print(e)


def insert_routes(routes, pid):
    try:
        for route in routes:
            # Insert or ignore if already exists
            cursor.execute('''INSERT OR IGNORE INTO route(annotation, route, http_method, is_base_route, file_path, pid)
             VALUES(?,?,?,?,?,?)''',
                           (route["annotation"], route["route"], route["http_method"], int(route["is_base_route"]), route["file_path"], pid))
        db.commit()
    except Exception as e:
        print(e)


def insert_tests(tests, pid):
    try:
        for test in tests:
            # Insert or ignore if already exists
            cursor.execute('''INSERT OR IGNORE INTO test(annotation, route, http_method, pid)
             VALUES(?,?,?,?)''',
                           (test["annotation"], test["route"], test["http_method"], pid))
        db.commit()
    except Exception as e:
        print(e)
