import logging
import os
import string
import subprocess
import sys
import time
from datetime import datetime
import random
from functools import wraps
from flask import Flask, request, jsonify, json
from marshmallow import Schema, fields, ValidationError, validate
from os.path import exists

TOKEN: str = "TOKEN123"  # TODO: Implement tokens on production
SCRIPT_DIR: str = os.path.join(os.path.expanduser('~'), "python")  # TODO: Update with Python scripts directory location
LOG_DIR: str = os.path.join(os.path.expanduser('~'), "logs")  # TODO: Update with logs directory location


# region ApiLogger
class ApiLogger:  # Used because prefix approach is needed, TimedRotatingFileHandler only supports suffix
    format_logger_default: str = '%(asctime)s %(message)s'
    today_str = '20000101'  # Will be updated after first execution

    @staticmethod
    def __get_date_today__() -> str:
        return datetime.now().strftime("%Y%m%d")

    def __get_file_name__(self) -> str:
        global LOG_DIR
        log_file: str = os.path.basename(sys.argv[0]).replace(".", "_").lower()
        return f'{LOG_DIR}/{self.today_str}_{log_file}.log'

    def __init__(self):
        logging.getLogger().setLevel(logging.INFO)
        self.refresh_config()

    def refresh_config(self):
        if self.today_str != self.__get_date_today__():
            # 1 Update variable
            self.today_str = self.__get_date_today__()
            # 2 Remote old handlers
            log = logging.getLogger()  # root logger
            for hdlr in log.handlers[:]:  # remove all old handlers
                log.removeHandler(hdlr)
            # 2 Log to file
            log.setLevel(logging.INFO)
            handler_f = logging.FileHandler(filename=self.__get_file_name__(), mode='a', encoding='utf-8')
            handler_f.setFormatter(logging.Formatter(self.format_logger_default))
            log.addHandler(handler_f)
            # 3 Log to console
            handler_s = logging.StreamHandler()
            handler_s.setFormatter(logging.Formatter(self.format_logger_default))
            log.addHandler(handler_s)
# endregion


apiLogger = ApiLogger()
api = Flask(__name__)


# region Token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token_provided = None
        if "Authorization" in request.headers:
            try:
                token_provided = request.headers["Authorization"].split(" ")[1]
            except Exception:
                pass
        if not token_provided:
            msg: str = "Authentication Token is missing"
            logging.warning(msg)
            return {
                       "message": msg,
                       "error": "Unauthorized"
                   }, 401
        if TOKEN != token_provided:
            msg: str = "Invalid Authentication token"
            logging.warning(msg)
            return {
                       "message": msg,
                       "error": "Unauthorized"
                   }, 401
        return f(*args, **kwargs)

    return decorated
# endregion


# region Support Functions
def executor_get_python_full_path(script_name: str):
    return f"{SCRIPT_DIR}/{script_name}"


def executor_get_python_cmd(script_name: str, parameters: str = None, wait_flag: bool = True) -> str:
    full_path = executor_get_python_full_path(script_name)
    cmd: str = f"python3 {full_path}" + (f" {parameters}" if parameters is not None else "")
    if not wait_flag:
        cmd += " > /dev/null 2>&1 &"
    return cmd


def get_json_msg(msg: str, key: str = 'error') -> json:
    return jsonify({key: msg})
# endregion


# region API executor
class ExecutorRequestPythonSchema(Schema):
    """
    Schema of Python request.

    Validates are input fields, see regexp below.
    """
    script_name = fields.String(required=True,
                                validate=validate.Regexp(regex='^[^ \.~\\\/;]+[^ \.;]+.py$',
                                                         error='Script name does not match pattern'))
    parameters = fields.String(required=False, dump_default=None,
                               validate=validate.Regexp(regex="^[^';]+$",
                                                        error="Single quote and semicolon are not allowed"))
    wait_flag = fields.Boolean(required=False, dump_default=True)


class Execution:
    """
    Execution class.

    Has id (random), command and time of creation.
    """

    def __init__(self, cmd: str):
        self.id = ''.join(random.choice(string.ascii_uppercase) for _ in range(8))
        self.cmd = cmd
        self.time_created = time.time()

    def format_message(self, msg: str) -> str:
        return f"{self.id} {msg}"


@api.route('/executor/python/', methods=['POST'])
@token_required
def executor_python_post():
    # Change date of log file if needed
    global apiLogger
    apiLogger.refresh_config()

    # Schema validation
    req = request.get_json()
    schema = ExecutorRequestPythonSchema()
    try:
        req = schema.dump(schema.load(req))
    except ValidationError as err:
        logging.warning(err.messages)
        return jsonify(err.messages), 400

    # Prepare for execution
    script_name = req['script_name']
    wait_flag = req['wait_flag']
    cmd = executor_get_python_cmd(script_name, req['parameters'], wait_flag)
    execution: Execution = Execution(cmd)

    # Validate that script exists
    if not exists(executor_get_python_full_path(script_name)):
        logging.warning(execution.format_message(f"Not found {req}"))
        return get_json_msg(f"{script_name} not found"), 500

    # Execute Command
    logging.info(execution.format_message(f"Executing {req}"))
    with subprocess.Popen(execution.cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as terminal:
        if wait_flag:
            try:
                terminal.wait(timeout=600)
            except subprocess.TimeoutExpired:
                msg: str = "Timeout of 10 minutes expired"
                logging.warning(execution.format_message(msg))
                return get_json_msg(msg), 408
            result = terminal.communicate()
            if terminal.returncode == 0:
                msg: str = "Finished"
                logging.info(execution.format_message(f"{msg} in {round(time.time() - execution.time_created)} seconds"))
                return get_json_msg(msg, "ok"), 200
            else:
                msg: str = str(result)
                logging.warning(execution.format_message(msg))
                return get_json_msg(msg), 500
        else:
            return get_json_msg("Added to queue", "ok"), 200
# endregion


if __name__ == '__main__':
    api.run(host="localhost", port=8090, ssl_context='adhoc')
