# #TODO

A lightweight task tracking application with some powerful features.

Designed to be durable and functional.

## Features

- Full-text search for tasks
- Create and collaborate on boards with other users
- Create and assign tasks to board collaborators
- Track the status of boards and tasks (todo/in-progress/completed)
- Comment on tasks
- Settings / Admin panel

**(todo)**

- Three-tier permissions system for shared boards
- View task history
- Embed diagrams in tasks
- Tag system for tasks
- Custom statuses for tasks
- Admins can download a database backup from UI

## Design

* Built on [Sqlite](https://www.sqlite.org/index.html) for persistence + FTS
* Built-in database migrations manager
* [anosql](https://anosql.readthedocs.io/en/latest/) to manage SQL queries
* Uses [Flask](https://flask.palletsprojects.com), Flask-Sessions, Flask-WTF for csrf protection
* Uses [scrypt](https://docs.python.org/3/library/hashlib.html#hashlib.scrypt) for password protection
* Aim to minimise the use of custom Javascripts
* Vendors the [Mermaid](https://mermaid.js.org/) JS library for charts and diagrams
* Packaged as a container using [uWSGI](https://flask.palletsprojects.com/en/2.2.x/deploying/uwsgi/) as gateway
* Unit tests using [pytest](https://docs.pytest.org/en/7.2.x/)

**(todo)**
* Github Actions for CI/CD
* Deploy to Kubernetes via Helm
