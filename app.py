from desktop_wrapper import BaseApp
from flask import jsonify, render_template
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = BaseApp('My App', __name__, static_folder='./desktop_tester/assets', template_folder='./desktop_tester/templates')


@app.bind()
def custom_function(value):
    # Do some stuf
    return "finish"

if __name__ == '__main__':
    app.start(port='5000', gui=True, debug=True)
