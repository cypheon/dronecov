#!/usr/bin/env python3

from flask import Flask, abort, json, render_template, request
import flask
from flask_sqlalchemy import SQLAlchemy

import datetime
import os

MIME_TYPE_SVG = 'image/svg+xml;charset=utf-8'

colormap = {
    'green': '#97ca00',
    'orange': '#fe7d37',
    'red': '#e05d44',
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DRONECOV_DB_URI', 'sqlite:///./dronecov.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CoverageInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    reponame = db.Column(db.String(255), nullable=False)
    branch = db.Column(db.String(255), nullable=False)
    build_id = db.Column(db.String(8), nullable=False)
    coverage = db.Column(db.Float(), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.utcnow)

    def __repr__(self):
        return '<Coverage %r/%r/%r@%r = %r>' % (self.username, self.reponame, self.branch, self.build_id,self.coverage)

class AccessToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.utcnow)

# Test support:
# For the test DB, create all tables without asking
if app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///./tests/tmp.db':
    db.create_all()

class UnauthorizedException(Exception):
    pass

class TokenUnauthorizedException(Exception):
    pass

def coverage_precision(cov):
    if cov >= 99.95:
        return "100"
    if cov >= 9.995:
        # return "%d.%01d" % (cov, ((cov-int(cov))*10))
        return "%.1f" % cov
    return "%.2f" % cov

def format_coverage(cov):
    return coverage_precision(cov) + "&#8201;%"

def render_color(cov: float, threshold_warn: float, threshold_error: float) -> str:
    if cov <= threshold_error:
        return "red"
    if cov <= threshold_warn:
        return "orange"
    return "green"

@app.errorhandler(UnauthorizedException)
def handle_unauthorized(error):
    return ("Unauthorized", 401, {})

@app.errorhandler(TokenUnauthorizedException)
def handle_unauthorized(error):
    return ("Forbidden", 403, {})

@app.route('/<user>/<repo>/<branch>/coverage.svg')
def get_coverage_svg(user: str, repo: str, branch: str):
    try:
        threshold_error = float(request.args.get('error', 5))
        threshold_warn = float(request.args.get('warn', 80))
    except ValueError as e:
        return (str(e), 400, {})

    cov = db.session.query(CoverageInfo).filter_by(
        username=user,
        reponame=repo,
        branch=branch).order_by(CoverageInfo.created_at.desc()).first()

    if cov is not None:
        if app.debug and 'cov' in request.args:
            cov.coverage = float(request.args.get('cov'))
        coverage_string = format_coverage(cov.coverage)
        color = colormap[render_color(cov.coverage, threshold_warn, threshold_error)]
    else:
        coverage_string = 'N/A'
        color = colormap['red']

    return (render_template('badge-template.svg',
                            w1=60, w2=54, pad=4,
                            coverage=coverage_string,
                            color=color
                            ), 200, {
        'Content-Type': MIME_TYPE_SVG,
    })

AUTH_PREFIX = 'Bearer '

def validate_coverage_report(user: str, repo: str, branch: str, cov_json) -> CoverageInfo:
    cov_total = float(cov_json.get('coverage_total'))
    build_number = int(cov_json.get('build_number'))

    return CoverageInfo(coverage=cov_total,
                        build_id=build_number,
                        username=user,
                        reponame=repo,
                        branch=branch)

def token_can_access(token: str, user: str, repo: str):
    """Check that token can access "user/repo", otherwise throw an exception."""
    tk = db.session.query(AccessToken).filter_by(username=user, token=token).first()
    if tk is None:
        raise TokenUnauthorizedException()

def check_authorization(user: str, repo: str):
    auth = request.headers.get('Authorization', '')
    token = auth[len(AUTH_PREFIX):]
    if not (auth.startswith(AUTH_PREFIX) and len(token) == 32):
        raise UnauthorizedException()
    return token_can_access(token, user, repo)

@app.route('/<user>/<repo>/<branch>/coverage', methods=['POST'])
def update_coverage(user: str, repo: str, branch: str):
    check_authorization(user, repo)

    try:
        cov = validate_coverage_report(user, repo, branch, request.json)
    except (TypeError, ValueError) as e:
        return (str(e), 400, {})

    db.session.add(cov)
    db.session.commit()

    return ('OK', 201, None)

def generate_token() -> str:
    import random
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(alphabet) for _ in range(32))

if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'init':
        db.create_all()
        print("DB created.")
    elif sys.argv[1] in ['token', 'token-batch']:
        user_repo = sys.argv[2]
        if '/' not in user_repo:
            user_repo += '/*'
        user, repo = user_repo.split('/')
        if repo not in ['', '*']:
            print("warning: repo name is ignored, token is valid for all repos belonging to " + user)
        t = AccessToken(username = user,
                        name = sys.argv[3])
        t.token = generate_token()
        db.session.add(t)
        db.session.commit()

        if sys.argv[1] == 'token':
            print('Name: %s' % (t.name))
            print('Access Token: %s' % (t.token))
            print('Valid repos: %s/*' % (t.username))
        else:
            # Batch mode, print token and nothing else
            print(t.token)

