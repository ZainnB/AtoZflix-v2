from app.models.models import User, Movie, MovieLog, UserLog
import logging
from sqlalchemy.exc import IntegrityError
from app import db
from datetime import datetime
logging.basicConfig(level=logging.DEBUG)



def MovieLog_action(session, admin_id, movie_id, action, details):
    log = MovieLog(admin_id=admin_id, action=action, details=details, timestamp=datetime.utcnow())
    try:
        session.add(log)
        session.commit()
    except IntegrityError as e:
        logging.error(f"IntegrityError: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"Error: {e}")
        session.rollback()

def UserLog_action(session, admin_id, user_id, action, old_data=None, new_data=None):
    log = UserLog(admin_id=admin_id, user_id=user_id, action=action, old_data=old_data, new_data=new_data, timestamp=datetime.utcnow())
    try:
        session.add(log)
        session.commit()
    except IntegrityError as e:
        logging.error(f"IntegrityError: {e}")
        session.rollback()
    except Exception as e:
        logging.error(f"Error: {e}")
        session.rollback()