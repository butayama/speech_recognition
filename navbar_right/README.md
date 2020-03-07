A quick workaround for a flask-bootstrap navbar with items at the right side,
as requested at [#126](https://github.com/mbr/flask-bootstrap/issues/126).

**Bonus:** ability to change navbar's style
(`navbar navbar-inverse` in the example).

* copy the flask-bootstrap
  [sample app](https://github.com/mbr/flask-bootstrap/tree/master/sample_app)
  to a folder.
* overwrite `nav.py`, `__init__.py`, and `frontend.py` with the files here.
* create a virtual env, `pip install -r requirements.txt`, etc.

you should get this:

![screenshot](https://lut.im/OZaP9b3XJO/hYkBdef9smq2qXO3.png)

**Heads up:** `ExtendedNavbar` has `items=(...)` in the constructor
(unlike `Navbar` that receives `*items`).

I can make this a proper pull request (so that we don't need to tweak the
renderer at `__init__.py`).
