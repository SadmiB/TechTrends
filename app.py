import sqlite3, sys
from sqlite3.dbapi2 import Connection, connect

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from flask.wrappers import Response
from werkzeug.exceptions import abort
import logging
import __init__



file_handler = logging.FileHandler("app.log") # file handler

stdout_handler = logging.StreamHandler(sys.stdout) # stdout handler
stderr_handler = logging.StreamHandler(sys.stderr)  # stderr handler
handlers = [file_handler, stderr_handler, stdout_handler]

logging.basicConfig(handlers=handlers,format="%(asctime)8s %(levelname)-8s %(message)s")
logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)



# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    logger.debug("Connection to the database..")
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    __init__.db_connections += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    logger.debug(f"Get post {post_id}..")
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    logger.debug(f"Getting all posts..")
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      logger.warning(f"Post id {post_id} not found..")
      return render_template('404.html'), 404
    else:
      logger.debug(post)
      logger.debug(f"Returning post {post_id}: {post['title']}..")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger.debug("/about endpoint reached..")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    logger.debug("/create post endpoint reached..")
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            return redirect(url_for('index'))

    return render_template('create.html')

def get_posts_count():
    logger.debug("Getting posts count..")
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    count = len(posts)
    connection.close()
    logger.debug(f"Posts count is {count}..")
    return count


# staus
@app.route("/healthz")
def status():

    logger.debug(f" /healthz endpoint reached..")

    try:
        connection = get_db_connection()
        posts = connection.execute('SELECT * FROM posts').fetchall()
        connection.close()
        response = app.response_class(
          response = json.dumps({"result:": "OK - healthy"}),
          status=200,
          mimetype='application/json'
        )
    except:
        response = app.response_class(
          response = json.dumps({"result:": "ERROR - unhealthy"}),
          status=200,
          mimetype='application/json'
        )
 

    return response

# metrics
@app.route("/metrics")
def metrcis():

    logger.debug(f"/metrics endpoint reached..")

    response = app.response_class(
        response = json.dumps({"db_connection_count": __init__.db_connections, "post_count":get_posts_count()}),
        status=200,
        mimetype="application/json"
    )

    return response


# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
