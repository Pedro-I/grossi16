#!/usr/bin/env python3

__author__ = "Gabriel Queiroz"
__credits__ = ["Gabriel Queiroz", "Estevão Lobo", "Pedro Ilído"]
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Gabriel Queiroz"
__email__ = "gabrieljvnq@gmail.com"
__status__ = "pre-alpha"

import io
import click
import flask
import logging
import tempfile
import builtins
import datetime
import pkg_resources

UseCache = True
ServerStart = None
TeacherPasswd = None

# WEB PART
FilesCache = {}
webapp = flask.Flask("Grossi16")

def templater(name, **kwargs):
    if UseCache == True and "templates/"+name in FilesCache:
        tempfile_src = FilesCache["templates/"+name]
    else:
        tempfile_src = pkg_resources.resource_string("grossi16.web", "templates/"+name)
        if UseCache:
            FilesCache["templates/"+name] = tempfile_src
    return flask.render_template_string(
        str(tempfile_src, encoding="utf-8"),
        **kwargs)

def get_mime_from_extension(file):
    ext = file.split(".")[-1]
    if ext == "css":
        return "text/css"
    if ext == "html":
        return "text/html"
    if ext == "js":
        return "application/javascript"
    if ext == "woff2":
        return "application/x-font-woff"
    if ext == "png":
        return "image/png"
    return ""

@webapp.route("/")
def who_are_you():
    return templater("index.html")

@webapp.route("/student")
def student_page():
    o = []
    o.append({"id": 1, "text": "hi"})
    o.append({"id": 2, "text": "hi3"})
    o.append({"id": 3, "text": "hi2"})
    return templater("student.html", options=o, question="hi")

@webapp.route("/teacher")
def teacher_page():
    if is_teacher_logged_in():
        return flask.redirect("/teacher/dashboard")
    else:
        return flask.redirect("/teacher/login")

def is_teacher_logged_in():
    return TeacherPasswd == flask.request.cookies.get('passwd')

@webapp.route("/teacher/login", methods=["GET", "POST"])
def teacher_login_page():
    if is_teacher_logged_in():
        return flask.redirect("/teacher/dashboard")

    if flask.request.method == "POST":
        # Store password in cookie
        resp = flask.Response()
        resp.set_cookie('passwd', flask.request.form["passwd"])

        # Check if password is correct
        if flask.request.form["passwd"] == TeacherPasswd:
            #resp.set_data(flask.redirect("/teacher/dashboard"))
            resp.headers['Location'] = "/teacher/dashboard"
            resp.status_code = 302
            resp.status = "Found"
            return resp, 302

        # Ask user to retry loging in
        resp.set_data(templater("teacher_login.html", failed_once=True))
        return resp

    # Check if user has already tried to log in
    if flask.request.cookies.get("passwd") != "":
        return templater("teacher_login.html", failed_once=True)
    else:
        return templater("teacher_login.html")

@webapp.route("/teacher/logout", methods=["GET", "POST"])
def teacher_logout():
    # Store password in cookie
    resp = flask.Response()
    resp.set_cookie("passwd", "")
    resp.headers['Location'] = "/"
    resp.status_code = 302
    resp.status = "Found"
    return resp, 302

@webapp.route("/teacher/dashboard", methods=["GET", "POST"])
def teacher_dashboard_page():
    # Check if user has logged in
    if not is_teacher_logged_in():
        return flask.redirect("/teacher/login")

    # Show dashboard
    return templater("teacher_dashboard.html")

@webapp.errorhandler(404)
def err404(error):
    return templater("404.html"), 404

@webapp.errorhandler(500)
def err500(error):
    return templater("500.html"), 500

@webapp.route("/static/<path>")
def static_handler(path):
    if UseCache == True and path in FilesCache:
        data = FilesCache["static/"+path]
        mime = get_mime_from_extension("static/"+path)
    else:
        try:
            data = pkg_resources.resource_string("grossi16.web", "static/"+path)
            mime = get_mime_from_extension(path)
        except builtins.FileNotFoundError as e:
            flask.abort(404)
        
    return flask.send_file(io.BytesIO(data), mimetype=mime, conditional=False, add_etags=False)

# CLI PART

@click.command()
@click.option(
    '--port',
    '-p',
    default=8080,
    type=click.IntRange(0, 65535),
    help='Port in which the web server will listen to'
)
@click.option(
    '--bind-address',
    'addr',
    '-a',
    default="0.0.0.0",
    help='Address in which to bind the web server. Leave the default if you do not know what you are doing!'
)
@click.option(
    '--code',
    '-c',
    default="1234",
    type=click.IntRange(0, 65535),
    help="Teacher's console password"
)
@click.option(
    '--debug',
    '-d',
    'debug_mode',
    default=False,
    is_flag=True,
    help="If set to true, many optimization will be disabled in order to ease development. It will also automatically reload the code in event of any change. DO NOT USE IN PRODUCTION"
)
@click.option(
    '--use-threads/--no-threads',
    'threads_flag',
    default=True,
    help="Default value: True"
)
def main(addr, port, code, debug_mode, threads_flag):
    # Load files in memory
    global FilesCache, ServerStart, UseCache, TeacherPasswd

    TeacherPasswd = str(code)
    ServerStart = datetime.datetime.now()
    UseCache = not debug_mode

    if UseCache == True:
        print("Loading files...")
        for path in ["static/", "templates/"]:
            for name in pkg_resources.resource_listdir("grossi16.web", path):
                print("Loading "+path+name+"...")
                FilesCache[path+name] = pkg_resources.resource_string("grossi16.web", path+name)
        print("Files loaded!")

    # Start webserver
    print("Starting webserver")
    print("Options in use: "+str({
        "host": addr,
        "port": port,
        "threaded": threads_flag,
        "debug": debug_mode,
        "UseCache": UseCache,
        "TeacherPasswd": TeacherPasswd
    }))
    webapp.run(host=addr, port=port, threaded=threads_flag, debug=debug_mode)

if __name__ == "__main__":
    main()
