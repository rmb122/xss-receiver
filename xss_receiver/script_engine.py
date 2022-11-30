import base64
import os.path
import shutil

from xss_receiver import system_config
from werkzeug.security import safe_join
from functools import reduce

import dukpy
import sanic

_prelude_js = '''
function _engine_parse_file(file) {
    file["raw_content"] = Duktape.dec("base64", file.raw_content);
    return file
}

function _engine_is_buffer(v) {
    return typeof v === 'buffer' || v instanceof Buffer || v instanceof Duktape.Buffer;
}

var request = {
    client_ip: call_python("_engine.request.get_client_ip"),
    client_port: call_python("_engine.request.get_client_port"),
    method: call_python("_engine.request.get_method"),
    path: call_python("_engine.request.get_path"),

    header: call_python("_engine.request.get_header"),
    header_list: call_python("_engine.request.get_header_list"),
    
    /* arg */
    arg: call_python("_engine.request.get_arg"),
    arg_list: call_python("_engine.request.get_arg_list"),
    
    /* body */
    get_body: function () {
        return call_python("_engine.request.get_body");
    },
    
    get_raw_body: function () {
        return Duktape.dec("base64", call_python("_engine.request.get_raw_body"));
    },
    
    /* json */
    get_json: function () {
        return call_python("_engine.request.get_json");
    },
     
    /* form */
    get_form: function () {
        return call_python("_engine.request.get_form");
    },
    
    get_form_list: function () {
        return call_python("_engine.request.get_form_list");
    },
    
    /* file */
    get_file: function () {
        var result = call_python("_engine.request.get_file");
        Object.keys(result).forEach(function (key) {
            _engine_parse_file(result[key]);
        });
        return result;
    },
    
    get_file_list: function () {
        var result = call_python("_engine.request.get_file_list");
        Object.keys(result).forEach(function (key) {
            result[key].forEach(function (f) {_engine_parse_file(f)});
        });
        return result;
    },
    
    get_file_by_name: function (name) {
        return _engine_parse_file(call_python("_engine.request.get_file_by_name", name));
    },
    
    get_file_list_by_name: function (name) {
        return call_python("_engine.request.get_file_list_by_name", name).map(_engine_parse_file);
    }
};

var response = {
    set_status_code: function (status_code) {
        call_python("_engine.response.set_status_code", status_code);
    },
    
    set_header: function (name, value) {
        call_python("_engine.response.set_header", name, value);
    },
    
    send: function (value) {
        if (_engine_is_buffer(value)) {
            call_python("_engine.response.send_raw", Duktape.enc("base64", value));
        } else {
            call_python("_engine.response.send", value);
        }
    }
};

var storage = {
    list_directory: function (path) {
        return call_python("_engine.storage.list_directory", path);
    },

    create_directory: function (path) {
        call_python("_engine.storage.create_directory", path);
    },
    
    remove_directory: function (path, recursion) {
        call_python("_engine.storage.remove_directory", path, recursion);
    },
    
    read_file: function (path, mode) {
        if (mode && mode.toString().indexOf("b") !== -1) {
            return Duktape.dec("base64", call_python("_engine.storage.read_file", path, mode));
        } else {
            return call_python("_engine.storage.read_file", path, mode);
        }
    },
    
    write_file: function (path, content, append) {
        if (_engine_is_buffer(content)) {
            call_python("_engine.storage.write_raw_file", path, Duktape.enc("base64", content), append);
        } else {
            call_python("_engine.storage.write_file", path, content, append);
        }
    },
    
    remove_file: function (path) {
        call_python("_engine.storage.remove_file", path);
    }
};
'''


def _file_to_dict(f: sanic.request.File) -> dict[str, str]:
    return {
        'filename': f.name,
        'type': f.type,
        'content': f.body.decode('utf-8', errors='ignore'),
        'raw_content': base64.b64encode(f.body).decode()
    }


class ScriptEngine:
    interpreter: dukpy.JSInterpreter

    @staticmethod
    def _load_module(module_name):
        module_path = safe_join(system_config.UPLOAD_PATH, module_name)
        if module_path:
            for path in (module_path, module_path + '.js'):
                if os.path.exists(path):
                    with open(path, 'rb') as f:
                        return module_name, f.read().decode('utf-8')
        return None, None

    def __init__(self, request: sanic.Request, response: sanic.HTTPResponse):
        self.interpreter = dukpy.JSInterpreter()
        self.interpreter.export_function('dukpy.lookup_module', self._load_module)

        # self.interpreter.export_function('dukpy.log.info', lambda *args: print(' '.join(args)))

        # request
        self.interpreter.export_function('_engine.request.get_client_ip', lambda: request.ip)
        self.interpreter.export_function('_engine.request.get_client_port', lambda: request.port)
        self.interpreter.export_function('_engine.request.get_method', lambda: request.method)
        self.interpreter.export_function('_engine.request.get_path', lambda: request.path)

        self.interpreter.export_function('_engine.request.get_header', lambda: dict(request.headers.items()))
        self.interpreter.export_function(
            '_engine.request.get_header_list',
            lambda: reduce(lambda _sum, curr: _sum | {curr: request.headers.getall(curr)}, request.headers.keys(), {})
        )

        self.interpreter.export_function(
            '_engine.request.get_arg',
            lambda: dict(map(lambda kv: (kv[0], kv[1][-1]), request.args.items()))
        )
        self.interpreter.export_function('_engine.request.get_arg_list', lambda: dict(request.args.items()))

        self.interpreter.export_function(
            '_engine.request.get_body',
            lambda: request.body.decode(errors='ignore')
        )
        self.interpreter.export_function(
            '_engine.request.get_raw_body',
            lambda: base64.b64encode(request.body).decode()
        )

        self.interpreter.export_function('_engine.request.get_json', lambda: request.json)

        self.interpreter.export_function(
            '_engine.request.get_form',
            lambda: dict(map(lambda kv: (kv[0], kv[1][-1]), request.form.items()))
        )
        self.interpreter.export_function('_engine.request.get_form_list', lambda: dict(request.form.items()))

        self.interpreter.export_function(
            '_engine.request.get_file',
            lambda: dict(map(lambda kv: (kv[0], _file_to_dict(kv[1][0])), request.files.items()))
        )
        self.interpreter.export_function(
            '_engine.request.get_file_list',
            lambda: dict(map(lambda kv: (kv[0], list(map(_file_to_dict, kv[1]))), request.files.items()))
        )
        self.interpreter.export_function('_engine.request.get_file_by_name', lambda name: _file_to_dict(request.files.get(name)))
        self.interpreter.export_function('_engine.request.get_file_list_by_name', lambda name: list(map(_file_to_dict, request.files.getlist(name))))

        # response
        def set_status_code(status_code: int):
            if isinstance(status_code, int):
                response.status = status_code
            else:
                raise dukpy.JSRuntimeError("status code should be number")

        self.interpreter.export_function('_engine.response.set_status_code', set_status_code)

        def set_header(name: str, value: str):
            if isinstance(name, str):
                if isinstance(value, str):
                    response.headers[name] = value
                elif isinstance(value, list) and all(map(lambda i: isinstance(i, str), value)):
                    if name in response.headers:
                        del response.headers[name]

                    for i in value:
                        response.headers.add(name, i)
                else:
                    raise dukpy.JSRuntimeError("value should be string or array of string")
            else:
                raise dukpy.JSRuntimeError("name should be string")

        self.interpreter.export_function('_engine.response.set_header', set_header)

        def send(value: str):
            if isinstance(value, str):
                response.body += value.encode()
            else:
                raise dukpy.JSRuntimeError("value should be string")

        self.interpreter.export_function('_engine.response.send', send)

        def send_raw(value: str):
            if isinstance(value, str):
                response.body += base64.b64decode(value)
            else:
                raise dukpy.JSRuntimeError("value should be base64 string")

        self.interpreter.export_function('_engine.response.send_raw', send_raw)

        # storage
        def list_directory(path: str):
            if isinstance(path, str):
                path = path.lstrip('/\\')
                path = safe_join(system_config.UPLOAD_PATH, path)
                if path:
                    return os.listdir(path)
                else:
                    raise dukpy.JSRuntimeError("path is invalid")
            else:
                raise dukpy.JSRuntimeError("path should be string")

        self.interpreter.export_function('_engine.storage.list_directory', list_directory)

        def create_directory(path: str):
            if isinstance(path, str):
                path = path.lstrip('/\\')
                path = safe_join(system_config.UPLOAD_PATH, path)
                if path:
                    return os.mkdir(path)
                else:
                    raise dukpy.JSRuntimeError("path is invalid")
            else:
                raise dukpy.JSRuntimeError("path should be string")

        self.interpreter.export_function('_engine.storage.create_directory', create_directory)

        def remove_directory(path: str, recursion: bool):
            if isinstance(path, str):
                path = path.lstrip('/\\')
                path = safe_join(system_config.UPLOAD_PATH, path)
                if path:
                    if recursion:
                        shutil.rmtree(path)
                    else:
                        os.rmdir(path)
                else:
                    raise dukpy.JSRuntimeError("path is invalid")
            else:
                raise dukpy.JSRuntimeError("path should be string")

        self.interpreter.export_function('_engine.storage.remove_directory', remove_directory)

        def read_file(path: str, mode: str):
            if isinstance(path, str) and (isinstance(mode, str) or mode is None):
                path = path.lstrip('/\\')
                path = safe_join(system_config.UPLOAD_PATH, path)
                if path:
                    if mode is not None and "b" in mode:
                        with open(path, 'rb') as f:
                            return base64.b64encode(f.read()).decode()
                    else:
                        with open(path, 'r') as f:
                            return f.read()
                else:
                    raise dukpy.JSRuntimeError("path is invalid")
            else:
                raise dukpy.JSRuntimeError("path should be string, mode should be string or undefined")

        self.interpreter.export_function('_engine.storage.read_file', read_file)

        def write_file(path: str, content: str, append: bool):
            if isinstance(path, str) and isinstance(content, str):
                path = path.lstrip('/\\')
                path = safe_join(system_config.UPLOAD_PATH, path)
                if path:
                    if append:
                        with open(path, 'a') as f:
                            f.write(content)
                    else:
                        with open(path, 'w') as f:
                            f.write(content)
                else:
                    raise dukpy.JSRuntimeError("path is invalid")
            else:
                raise dukpy.JSRuntimeError("path and content should be string")

        def write_raw_file(path: str, content: str, append: bool):
            if isinstance(path, str) and isinstance(content, str):
                content = base64.b64decode(content)

                path = path.lstrip('/\\')
                path = safe_join(system_config.UPLOAD_PATH, path)
                if path:
                    if append:
                        with open(path, 'ab') as f:
                            f.write(content)
                    else:
                        with open(path, 'wb') as f:
                            f.write(content)
                else:
                    raise dukpy.JSRuntimeError("path is invalid")
            else:
                raise dukpy.JSRuntimeError("path and content should be string")

        self.interpreter.export_function('_engine.storage.write_file', write_file)
        self.interpreter.export_function('_engine.storage.write_raw_file', write_raw_file)

        def remove_file(path: str):
            if isinstance(path, str):
                path = path.lstrip('/\\')
                path = safe_join(system_config.UPLOAD_PATH, path)
                if path:
                    os.unlink(path)
                else:
                    raise dukpy.JSRuntimeError("path is invalid")
            else:
                raise dukpy.JSRuntimeError("path and content should be string")

        self.interpreter.export_function('_engine.storage.remove_file', remove_file)

        self.interpreter.evaljs(_prelude_js)

    def eval(self, script: str):
        self.interpreter.evaljs(script)
