from flask import Flask, render_template, request, jsonify
import webview
import threading
import requests
import time
from .formats import (
    BASE_INDEX_JS,
    BASE_INDEX_JS_IMPORTS,
    HTML_SCRIPT_TAGS_TEMPLATE,
    functions_js_template,
    custom_function_template
)
import logging
import os
logger = logging.getLogger(__name__)



def stc(string):

    cap = False
    new_str = ''
    for ch in string:
        if ch == '_':
            cap = True
            continue
        if cap:
            new_str += ch.upper()
            cap = False
        else:
            new_str += ch
    return new_str


class BaseApp(Flask):
    def __init__(self, app_name:str, *args, **kwargs):
        if 'template_folder' not in kwargs.keys():
            kwargs['template_folder'] = './templates'
        if 'static_folder' not in kwargs.keys():
            kwargs['static_folder'] = './assets'
        
        self.assets_path = kwargs['static_folder']
        self.templates_path = kwargs['template_folder']
        super().__init__(*args, **kwargs)
        self.window = webview.create_window(app_name, self)

        self.functions = []
        self.clean_up_generated_assets()


        @self.route('/')
        def index():
            return render_template('index.html')
    
    def clean_up_generated_assets(self):
        try:
            for fil in os.listdir(f'{self.assets_path}/generated'):
                try:
                    os.remove(f'{self.assets_path}/generated/{fil}')
                except Exception as e:
                    logger.error(e)
        except Exception as e:
            logger.error(f'Clean Up Failed due to: {e}')

    
    def bind(self, *eargs, **ekwargs):
        import inspect
        def _bind(func):
            # Create A separated Function to run as API backend for backup
            def route_func(fun):
                fun.__name__ = f'api_{func.__name__}'
                return fun

            route_func.__name__ = f'api_{func.__name__}'

            @self.route(f'/api/v1/{stc(func.__name__)}', methods=['POST'])
            @route_func
            def routed_function():
                args = request.json.get('values')
                resp = func(*args)
                return jsonify(response=resp)
            
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            # Setup Funcion name and Docs
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            # Set Original Signature to keep track of the original function
            wrapper.original_signature = inspect.signature(func)
            logger.info(f'Binding function: {wrapper.__name__}')
            # Expose functions for Pywebdriver
            self.window.expose(wrapper)
            # Use functions to render Autogenrated JS Files
            self.functions.append(wrapper)
            self.add_script_file(wrapper)
            return wrapper
        
        return _bind
    
    def add_script_file(self, function):
        params = ", ".join([stc(param) for param in function.original_signature.parameters])

        file_content = custom_function_template.format(
            python_name=function.__name__,
            name=stc(function.__name__),
            params=params
        )

        if not os.path.exists(f'{self.assets_path}/js'):
            os.mkdir(f'{self.assets_path}/js')

        if not os.path.exists(f'{self.assets_path}/js/generated'):
            os.mkdir(f'{self.assets_path}/js/generated')

        with open(f'{self.assets_path}/js/generated/{stc(function.__name__)}.js', 'w+') as js_file:
            js_file.write(file_content)
        
    def bind_javascript(self):
        imports = "\n".join([f"import {{ {stc(func.__name__)}Interface }} from './generated/{stc(func.__name__)}.js';" for func in self.functions])
        def params(func):
            return ", ".join(func.original_signature.parameters)

        api_binds = "\n".join([f"const {stc(func.__name__)} = ({params(func)}) => {{ return {stc(func.__name__)}Interface({params(func)}) }};" for func in self.functions])
        exports = ",\n\t".join([f"{stc(func.__name__)}" for func in self.functions])

        assets = ',\n\t'.join([f'"{stc(func.__name__)}"' for func in self.functions])

        func_binds = ",\n\t".join([f'{stc(func.__name__)}: {stc(func.__name__)}' for func in self.functions])

        # content = binds_file_template.format(assets=assets)
        content = functions_js_template.format(imports=imports, api_binds=api_binds, exports=exports, func_binds=func_binds)

        # logger.info(content)

        with open(f'{self.assets_path}/js/functions.js', 'w+') as js_file:
            js_file.write(content)

        # Update index.js imports
        js_old_content = None

        with open(f'{self.assets_path}/js/index.js', 'r') as js_file:
            js_old_content = js_file.read()
        
        pattern = '// EOI'

        find = js_old_content.find(pattern)
        if find >= 0:
            second_half = js_old_content[find + len(pattern) + 1:]

            functions = ", ".join([f'{stc(fun.__name__)}' for fun in self.functions])
            imports = BASE_INDEX_JS_IMPORTS.format(functions=functions)

            all_new_file = imports + second_half
            with open(f'{self.assets_path}/js/index.js', 'w+') as js_file:
                js_file.write(all_new_file)
        
        # Update index.html scripts section to add the custom functions
        custom_tags = "\n".join([HTML_SCRIPT_TAGS_TEMPLATE.format(func=stc(func.__name__)) for func in self.functions])

        first_half = None
        second_half = None

        with open(f'{self.templates_path}/index.html', 'r') as index_file:
            index_old_content = index_file.read()
            patt = "<!-- SOS -->"
            e_patt = "<!-- EOS -->"
            find_start = index_old_content.find(patt)
            find_end = index_old_content.find(e_patt)

            if find_start >= 0:
                first_half = index_old_content[:find_start + len(patt) + 1]
            
            if find_end >= 0:
                second_half = index_old_content[find_end:]

        with open(f'{self.templates_path}/index.html', 'w+') as index_file:
            index_content = first_half + custom_tags + second_half
            index_file.write(index_content)


    def start(self, *args, debug=False, gui=True, reload=False, **kwargs):
        self.bind_javascript()

        if gui and reload:
            def reload_function():
                while True:
                    time.sleep(5)
                    logger.info('reload window')
                    self.window.load_url('/')

            reload_thread = threading.Thread(target=reload_function, daemon=True)
            reload_thread.start()    

        def run_flask(*args, **kwargs):
            self.run(*args, debug=(not gui), **kwargs)

        if not gui:
            run_flask(*args, **kwargs)

        else:
            flask_thread = threading.Thread(target=run_flask, args=set(args), kwargs=kwargs, daemon=True)
            flask_thread.start()

        if debug and gui:
            webview.start(debug=True, http_port=kwargs.get('port'))
        elif gui:
            webview.start(http_port=kwargs.get('port'))
       
