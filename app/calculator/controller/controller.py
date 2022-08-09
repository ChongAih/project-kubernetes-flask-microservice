from flask import request
from flask_restplus import Resource

import app
from app.calculator.computation.api import handle_evaluate, handle_status, handle_result
from app.calculator.serializer.dto import Dto

calculator_api = Dto.api
evaluate_request_model = Dto.evaluate_request_model
status_request_model = Dto.status_request_model
result_request_model = Dto.result_request_model
response_model = Dto.response_model
result_model = Dto.result_model


# run_calculator_qm_task()


@calculator_api.route("/evaluate")
class EvaluateRequestHandler(Resource):
    @calculator_api.expect(evaluate_request_model, validate=True)
    @calculator_api.doc("to submit computation request and request response will be returned for subsequent query")
    @calculator_api.marshal_with(response_model)
    def post(self):
        return handle_evaluate(data=request.json, qm=app.calculator_qm)


@calculator_api.route("/status")
class EvaluateRequestHandler(Resource):
    @calculator_api.expect(status_request_model, validate=True)
    @calculator_api.doc("to check status of the submitted request")
    @calculator_api.marshal_with(response_model)
    def post(self):
        req = request.json
        return handle_status(task_id=req["task_id"])


@calculator_api.route("/result")
class EvaluateRequestHandler(Resource):
    @calculator_api.expect(result_request_model, validate=True)
    @calculator_api.doc("to check result of the submitted request")
    @calculator_api.marshal_with(result_model)
    def post(self):
        req = request.json
        return handle_result(task_id=req["task_id"])
