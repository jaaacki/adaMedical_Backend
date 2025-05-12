# app/core/error_handlers.py
from flask import jsonify
from .errors import APIError

def register_error_handlers(app):
    """Register error handlers to the Flask app."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({
            'status': 'error',
            'message': 'Bad request.'
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        return jsonify({
            'status': 'error',
            'message': 'Authentication required.'
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        return jsonify({
            'status': 'error',
            'message': 'Permission denied.'
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found.'
        }), 404
    
    @app.errorhandler(500)
    def handle_server_error(error):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error.'
        }), 500