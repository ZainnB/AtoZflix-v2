from app.models.models import User
from app import db
from flask import Blueprint,request,jsonify
from app.utils.validators import is_valid_email
from app.utils.helpers import hash_password,check_password_hash


user_bp=Blueprint('user',__name__)

# Register logic
@user_bp.route('/api/register',methods=['POST'])
def register():
    data=request.json
    email=data.get('email')
    username=data.get('username')
    password=data.get('password')

    if(not email or not username or not password):
        return jsonify({'message':'All fields are required'}),400
    if(not is_valid_email(email)):
        return jsonify({'message':'Invalid email format'}),400
    
    existing_user=User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'message':'User already exists'}),400
    
    hashed_password=hash_password(password)
    new_user=User(email=email,username=username,password=hashed_password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message':'User registered successfully'}),200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message':f'An error occured: {str(e)}'}),500
    
    
# Sign up logic
@user_bp.route('/api/signin',methods=['POST'])
def signin():
    data=request.json
    input_name=data.get('username')
    password=data.get('password')
    if(is_valid_email(input_name)):
        user=User.query.filter_by(email=input_name).first()
    else:
        user=User.query.filter_by(username=input_name).first()
    if not user:
        jsonify({'message':'User not found'}),404
    print(user)
    if user and check_password_hash(user.password,password):
        return jsonify({
            'user_id':user.user_id,
            'role':user.role,
            'success':True,
            'message':'Login successful'
        })
    else:
        return jsonify({'success':False,'message':'Invalid username or password'})
    
