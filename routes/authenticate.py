from routes.base_route_handler import BaseRouteHandler
from flask import request
import os

class AuthenticateRouteHandler(BaseRouteHandler):
    """Handler for authentication requests"""
    
    def __init__(self):
        super().__init__('auth')
        self.api_key = os.environ.get('API_KEY')
        self.create_auth_route()
        
    def create_auth_route(self):
        """Create the authentication route"""
        @self.blueprint.route('/authenticate', methods=['GET'])
        @queue_task_wrapper(bypass_queue=True)
        def authenticate_endpoint(**kwargs):
            api_key = request.headers.get('X-API-Key')
            if api_key == self.api_key:
                return "Authorized", "/authenticate", 200
            return "Unauthorized", "/authenticate", 401

# Create and export the blueprint
auth_bp = AuthenticateRouteHandler().blueprint
