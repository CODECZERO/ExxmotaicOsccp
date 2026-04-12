from functools import wraps
from flask import flash, render_template, has_request_context
import logging 

logger=logging.getLogger(__name__)
logging.basicConfig(filename="app.log",encoding="utf-8",level=logging.DEBUG)

def error_handler(error_message="Something went wrong", log_trace=True, internal_error=0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            try:
                return func (*args,**kwargs)
            except Exception as e:
                if log_trace:
                    print(f"\n[ERROR] Function:{func.__name__}\nException:{e}\n")
                    user_message=""

                    if has_request_context() and internal_error == 0:
                            try:
                                user_message=f"{error_message}:{str(e)}"    
                                flash(user_message,"error")
                                return render_template("error.html",error_message=user_message)
                            except RuntimeError:
                                pass 
                
                if internal_error==1:
                      logger.error(f'{str(e)}')
                return None 
            return wrapper
        return decorator


