from functools import wraps
from flask import request, jsonify
from app.utils.jwt_auth import extract_token_from_header, get_user_from_token, verify_token

def token_required(f):
    """
    Decorator to verify JWT token in request.
    Adds user info to flask.g.current_user
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = extract_token_from_header()
        
        if not token:
            return jsonify({'message': 'Token is missing', 'error': 'unauthorized'}), 401
        
        user_info = get_user_from_token(token)
        if not user_info:
            return jsonify({'message': 'Token is invalid or expired', 'error': 'unauthorized'}), 401
        
        # Add user info to request context
        from flask import g
        g.current_user = user_info
        
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """
    Decorator to verify user has admin role.
    Must be used after @token_required
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g
        
        # Check if token_required was applied first
        if not hasattr(g, 'current_user'):
            token = extract_token_from_header()
            if not token:
                return jsonify({'message': 'Token is missing', 'error': 'unauthorized'}), 401
            user_info = get_user_from_token(token)
            if not user_info:
                return jsonify({'message': 'Token is invalid or expired', 'error': 'unauthorized'}), 401
            g.current_user = user_info
        
        # Check admin role
        if g.current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required', 'error': 'forbidden'}), 403
        
        return f(*args, **kwargs)
    return decorated

def verify_user_ownership(f):
    """
    Decorator to verify user_id in token matches user_id in request.
    Must be used after @token_required
    Can be used with user_id in URL params, query params, or JSON body
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import g
        
        # Check if token_required was applied first
        if not hasattr(g, 'current_user'):
            token = extract_token_from_header()
            if not token:
                return jsonify({'message': 'Token is missing', 'error': 'unauthorized'}), 401
            user_info = get_user_from_token(token)
            if not user_info:
                return jsonify({'message': 'Token is invalid or expired', 'error': 'unauthorized'}), 401
            g.current_user = user_info
        
        token_user_id = g.current_user.get('user_id')
        
        # Check user_id from various sources
        request_user_id = None
        
        # From URL parameters (kwargs)
        if 'user_id' in kwargs:
            request_user_id = kwargs['user_id']
        
        # From query parameters
        if not request_user_id:
            request_user_id = request.args.get('user_id', type=int)
        
        # From JSON body.
        #
        # get_json(silent=True) rather than request.json: a GET carrying a
        # Content-Type of application/json but no body (which is what fetch
        # sends when default headers are set) made request.json raise, and Flask
        # turned that into a 400 before the route ever ran. silent=True returns
        # None instead of raising.
        if not request_user_id and request.is_json:
            body = request.get_json(silent=True) or {}
            request_user_id = body.get('user_id')
        
        # Verify ownership
        if request_user_id and int(request_user_id) != int(token_user_id):
            return jsonify({'message': 'You can only access your own data', 'error': 'forbidden'}), 403
        
        # Replace user_id in kwargs/request with token user_id for security
        if request_user_id is None:
            # No user_id in the request, so fall back to the token's. Routes
            # read the id from g.current_user regardless; this only keeps the
            # kwargs signature consistent for routes that take it in the path.
            if 'user_id' in kwargs:
                kwargs['user_id'] = token_user_id
        
        return f(*args, **kwargs)
    return decorated

