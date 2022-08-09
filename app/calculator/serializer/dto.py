from flask_restplus import Namespace, fields


class Dto:
    api = Namespace('Calculator',
                    description='It computes the output based on the default functions and user defined inputs')

    # {number: int}
    evaluate_request_model = api.model('evaluate_request_model', {
        'model': fields.String(required=True, description='the name of computation model'),
        'number': fields.Float(readOnly=True, required=True, description='the user defined input')
    })

    # {task_id: str}
    status_request_model = api.model('status_request_model', {
        'task_id': fields.String(required=True, description='the task unique identifier')
    })

    # {task_id: str}
    result_request_model = api.model('result_request_model', {
        'task_id': fields.String(required=True, description='the task unique identifier')
    })

    # {task_id: str}
    kill_request_model = api.model('kill_request_model', {
        'task_id': fields.String(required=True, description='the task unique identifier')
    })

    common_response_model = api.model('common_response_model', {
        'retcode': fields.Integer(required=True,
                                  description='the computation returned code; '
                                              '0: success, 1: naming error, -1: internal error'),
        'status': fields.String(required=True, description='the computation status'),
        'message': fields.String(required=True,
                                 description='the computation message if error encountered; '
                                             'NA if no error encountered')
    })

    # {task_id: str, status: {retcode: int, message: str}}
    response_model = api.model('response_model', {
        'task_id': fields.String(required=True, description='the task unique identifier'),
        'response': fields.Nested(common_response_model)
    })

    # {status: int, status: {retcode: int, message: str}, result: float}
    result_model = api.model('result_model', {
        'task_id': fields.String(required=True, description='the task unique identifier'),
        'response': fields.Nested(common_response_model),
        'output': fields.Float(required=True,
                               description='the computation output; '
                                           '-1.0 is returned if error encountered'),
    })
