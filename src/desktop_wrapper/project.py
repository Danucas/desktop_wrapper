# Project Initial Setup
import os
from .formats import (
    BASE_INDEX_HTML,
    BASE_INDEX_JS,
    BASE_REACT_JS,
    BASE_INDEX_JS_IMPORTS,
    BASE_INDEX_CSS,
    HTML_SCRIPT_TAGS_TEMPLATE,
    functions_js_template,
    custom_function_template
)
import requests
import sys


def create_new_app(app_name=None):
    if not app_name:
        app_name = sys.argv[1]
    
    if not app_name:
        raise Exception('No app_name provided')

    if not os.path.exists(app_name):
        os.mkdir(app_name)
    
    templates_path = f'{app_name}/templates'

    if not os.path.exists(templates_path):
        os.mkdir(templates_path)

    # Create HTML file

    index_content = BASE_INDEX_HTML.format(app_name=app_name)
    with open(f'{templates_path}/index.html', 'w+') as index_file:
        index_file.write(index_content)

    # Create Static folder
    
    assets_path = f'{app_name}/assets'

    if not os.path.exists(assets_path):
        os.mkdir(assets_path)

    # Create JS folders and index.js

    if not os.path.exists(f'{assets_path}/js'):
        os.mkdir(f'{assets_path}/js')
    
    with open(f'{assets_path}/js/index.js', 'w+') as index_js_file:
        index_content = BASE_INDEX_JS
        index_js_file.write(index_content)
    

    with open(f'{assets_path}/js/App.js', 'w+') as react_js_file:
        index_content = BASE_REACT_JS
        react_js_file.write(index_content)

    # Download Babel and React js dependencies to local storage
    babel_js = requests.get('https://unpkg.com/@babel/standalone/babel.min.js')

    if not os.path.exists(f'{assets_path}/js/packages'):
        os.mkdir(f'{assets_path}/js/packages')

    with open(f'{assets_path}/js/packages/babel.min.js', 'w+') as babel_js_file:
        babel_js_file.write(babel_js.text)
    
    react_js = requests.get("https://unpkg.com/react@18/umd/react.development.js")

    with open(f'{assets_path}/js/packages/react.js', 'w+') as react_package_js_file:
        react_package_js_file.write(react_js.text)

    react_dom_js = requests.get("https://unpkg.com/react-dom@18/umd/react-dom.development.js")

    with open(f'{assets_path}/js/packages/react_dom.js', 'w+') as react_dom_package_js_file:
        react_dom_package_js_file.write(react_dom_js.text)


    # Create Css Files

    if not os.path.exists(f'{assets_path}/css'):
        os.mkdir(f'{assets_path}/css')
    
    with open(f'{assets_path}/css/index.css', 'w+') as index_css_file:
        index_content = BASE_INDEX_CSS
        index_css_file.write(index_content)


if __name__ == '__main__':
    import sys
    args = sys.argv
    name = args[1]
    create_new_app(name)
