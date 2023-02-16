# #TODO

#todo is a web application that allows users to manage sets of tasks called boards,
and collaborate with other users on boards. It has a full-text search feature to help
users easily find their tasks. #todo is built with [Flask](https://flask.palletsprojects.com)
and [SQLite](https://www.sqlite.org/index.html), using SQL directly.
The interface uses jinja2 templating and minimal Javascript, except for vendored packages
from [mermaid.js](https://mermaid.js.org/) and [pico.css](https://picocss.com/).
It is packaged as a container, using uWSGI as the HTTP gateway.
#todo tries to be easily testable, low maintenance, and easy to operate.

## Features

* create boards and collaborate with others by inviting them to join the board
* create and assign tasks to collaborators on the board
* set status of boards and tasks to one of three statuses: `todo`, `in-progress`, and `completed`
* users can add comments to tasks
* test suite using pytest
* database migration manager

There are a number of features that are still in-progress

* embed [mermaid.js](https://mermaid.js.org/) diagrams in tasks
* custom statuses for tasks
* task/event history feature
* admins can download a database backup from the UI
