# Lighweight Coverage Tracking Server for Drone CI

This is the target server, where the coverage reporter can post test results.


# Running

    pipenv install

    # Optional, set database URI (default is ./dronecov.db)
    export DRONECOV_DB_URI=sqlite:///./var/dronecov_data.db

    pipenv run ./dronecov.py init
    pipenv run gunicorn -b 127.0.0.1:5000 dronecov:app

    # Generate access token
    pipenv run ./dronecov.py token username "Token Name / Description"


# Develpment

Run development server:

    pipenv install --dev

    DRONECOV_DB_URI=sqlite:///./tests/tmp.db FLASK_DEBUG=1 FLASK_APP=dronecov.py pipenv run flask run

Run tests:

    ./runtests.sh
