from app.models.models import User, Movie, MovieLog, UserLog
import logging
from sqlalchemy.exc import IntegrityError
from app import db
from datetime import datetime

# NOTE: no logging.basicConfig() here. Calling it at import time sets the ROOT
# logger for the whole process, which switched every third-party library to
# DEBUG - urllib3 was logging every outbound TMDb URL. Log level belongs to the
# application entry point, not to a utility module.
logger = logging.getLogger(__name__)



def MovieLog_action(session, admin_id, action, details):
    log = MovieLog(admin_id=admin_id, action=action, details=details, timestamp=datetime.utcnow())
    try:
        session.add(log)
        session.commit()
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Error: {e}")
        session.rollback()

def UserLog_action(session, admin_id, user_id, action, old_data=None, new_data=None):
    log = UserLog(admin_id=admin_id, user_id=user_id, action=action, old_data=old_data, new_data=new_data, timestamp=datetime.utcnow())
    try:
        session.add(log)
        session.commit()
    except IntegrityError as e:
        logger.error(f"IntegrityError: {e}")
        session.rollback()
    except Exception as e:
        logger.error(f"Error: {e}")
        session.rollback()