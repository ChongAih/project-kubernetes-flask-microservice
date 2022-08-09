from flask import Blueprint
from flask import Flask
from flask_restplus import Api

from app.calculator.computation.db import create_table
from app.calculator.computation.service import run_calculator_qm_task
from app.calculator.controller.controller import calculator_api


def start_app():
    create_table()
    run_calculator_qm_task()
    app = Flask(__name__)
    blueprint = register_blueprint_v1()
    app.register_blueprint(blueprint)
    return app


def register_blueprint_v1():
    blueprint = Blueprint('api', __name__)
    api = Api(
        blueprint,
        title='Calculator Computation',
        version='1.0',
        description='The system contains models to compute given user defined input'
    )
    api.add_namespace(calculator_api, path='/v1/calculator')
    return blueprint
