# osmosis plugin

## docker

### For start

$ docker-compose up -d

### For access to shell in the container

$ docker-compose exec osmosis_plugin bash

### For end

$ docker-compose down

### For remove

$ docker-compose down --rmi all --volumes --remove-orphans

## for developers

1. Install poetry to set up python environment

```
If you have not yet installed poetry, first install poetry as follows
$ curl -sSL https://install.python-poetry.org | python3 -
Set the poetry path as the log shows.
$ export PATH="$HOME/.local/bin:$PATH"
Set up the python environment as follows.
$ poetry config virtualenvs.in-project true && poetry install
```

2. Install pre-commit

```
# Before committing, we use pre-commmit hook to check the code style.
# Install pre-commit in the following way
$ pre-commit install

# If you are using docker and the venv environment is not enabled, please do the following to enable it.
$ source /app/.venv/bin/activate

```

### For test

```
$ poetry shell
$ pytest --cov=src --cov-branch --cov-report=term-missing -vv
```

### For execution

```
$ poetry shell
$ python src/main.py address > result.csv
e.x. $ python src/main.py osmo1f2rznaz9s6cwevtfwyq8daguajqaac0yahsgqm > result.csv
```
