
from flask import Flask, request, Response, abort
import json
from flask_restful import Resource
from flask_restful import Api
from flasgger import Swagger, swag_from
from routing.app import routing
from routing.services.logging import logger
from routing.settings import APP_NAME

app = Flask(APP_NAME)
api = Api(app=app, prefix='/v1')
swagger = Swagger(app, template_file='open_api/template.yaml')


def swag_error_handler(exception_error, data, schema):
    logger.error(exception_error)
    exception_message = str(exception_error).split('\n')
    exception_response = (f"Open API schema validation error. {exception_message[0]}. {exception_message[2][:-1]}. "
                          "See log for more information.")
    response = {
        'status': 'ERROR',
        'message': exception_response

    }
    abort(Response(json.dumps(response), status=400))


class RouteOptimizer(Resource):
    @swag_from('open_api/routing.yaml', definition='Routing',
               validation=True,
               validation_error_handler=swag_error_handler)
    def get(self):
        input_json = request.json
        solution = routing(input_json)
        return solution.to_json(), 200


api.add_resource(RouteOptimizer, '/routing')
