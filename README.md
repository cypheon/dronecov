# Lighweight Coverage Tracking Server for Drone CI

The server has exactly 2 features:
 * Receive POSTed coverage summary results and store them per repo/branch
 * Provide badge SVGs with the current coverage. With color bassed on current
   coverage.


# Running the Server

    pipenv install

    # Optional, set database URI (default is ./dronecov.db)
    export DRONECOV_DB_URI=sqlite:///./var/dronecov_data.db

    pipenv run ./dronecov.py init
    pipenv run gunicorn -b 127.0.0.1:5000 dronecov:app

    # Generate access token
    pipenv run ./dronecov.py token username "Token Name / Description"


SVGs are available at: `http://localhost:5000/<username>/<reponame>/<branch>/coverage.svg`

Set custom thresholds for error (red) and warning (orange): `http://localhost:5000/<username>/<reponame>/<branch>/coverage.svg?error=60&warn=80`


# Using the Reporter Plugin in Drone CI

In `.drone.yml`:
```yaml
pipeline:

  # Your other steps ...

  coverage:
    image: cypheon/dronecov
    secrets: [ dronecov_access_token ]
    lcov_info: './path/to/coverage/total.info'
    server: https://your.coverage.server.example.com/dronecov-server/base-url/
```


# Develpment

Run development server:

    pipenv install --dev

    DRONECOV_DB_URI=sqlite:///./tests/tmp.db FLASK_DEBUG=1 FLASK_APP=dronecov.py pipenv run flask run

Run tests:

    ./runtests.sh
