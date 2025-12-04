from app.models.models import User
from app import db
from flask import Blueprint,request,jsonify, current_app
from app.utils.validators import is_valid_email
from app.utils.helpers import hash_password,check_password_hash
from app.utils.jwt_auth import generate_token, verify_token, get_user_from_token
from app.utils.decorators import token_required

user_bp=Blueprint('user',__name__)

# Register logic
@user_bp.route('/api/register',methods=['POST'])
def register():
    data=request.json
    email=data.get('email')
    username=data.get('username')
    password=data.get('password')
    created_at=data.get('created_at')

    if(not email or not username or not password):
        return jsonify({'message':'All fields are required'}),400
    if(not is_valid_email(email)):
        return jsonify({'message':'Invalid email format'}),400
    
    existing_user=User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message':'User already exists'}),400
    
    hashed_password=hash_password(password)
    new_user=User(email=email,username=username,password=hashed_password, created_at=created_at)

    try:
        db.session.add(new_user)
        db.session.commit()
        
        # Generate JWT tokens after successful registration
        tokens = generate_token(new_user.user_id, new_user.role)
        return jsonify({
            'message':'User registered successfully',
            'success': True,
            'user_id': new_user.user_id,
            'role': new_user.role,
            **tokens
        }),200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message':f'An error occured: {str(e)}'}),500
    
    
# Sign in logic
@user_bp.route('/api/signin',methods=['POST'])
def signin():
    data=request.json
    input_name=data.get('username')
    password=data.get('password')
    
    if not input_name or not password:
        return jsonify({'success':False,'message':'Username and password are required'}),400
    
    if(is_valid_email(input_name)):
        user=User.query.filter_by(email=input_name).first()
    else:
        user=User.query.filter_by(username=input_name).first()
    
    if not user:
        return jsonify({'success':False,'message':'Invalid username or password'}),401
    
    if check_password_hash(user.password,password):
        # Generate JWT tokens
        tokens = generate_token(user.user_id, user.role)
        return jsonify({
            'user_id':user.user_id,
            'role':user.role,
            'success':True,
            'message':'Login successful',
            **tokens
        }),200
    else:
        return jsonify({'success':False,'message':'Invalid username or password'}),401

# Refresh token endpoint
@user_bp.route('/api/refresh',methods=['POST'])
def refresh():
    data=request.json
    refresh_token=data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'message':'Refresh token is required','error':'unauthorized'}),401
    
    user_info = get_user_from_token(refresh_token)
    if not user_info or user_info.get('token_type') != 'refresh':
        return jsonify({'message':'Invalid or expired refresh token','error':'unauthorized'}),401
    
    # Generate new access token
    tokens = generate_token(user_info['user_id'], user_info['role'])
    return jsonify({
        'success': True,
        'message': 'Token refreshed successfully',
        'access_token': tokens['access_token']
    }),200

# Get current user info (protected endpoint)
@user_bp.route('/api/me',methods=['GET'])
@token_required
def get_current_user():
    from flask import g
    user_id = g.current_user.get('user_id')
    user = User.query.filter_by(user_id=user_id).first()
    
    if not user:
        return jsonify({'message':'User not found','error':'not_found'}),404
    
    return jsonify({
        'user_id': user.user_id,
        'email': user.email,
        'username': user.username,
        'role': user.role
    }),200
    