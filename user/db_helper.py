from user.models import UserMaster


def get_user(user_id):
    try:
        user = UserMaster.objects.filter(id=user_id,is_active=True).first()
        return user
    except UserMaster.DoesNotExist:
        return None
    

def create_supabase_user(email, password):
    try:
        from petrotrack_backend.supabase_client import supabase

        response = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        return response
    except Exception as e:
        return None


def login_supabase_user(email, password):
    try:
        from petrotrack_backend.supabase_client import supabase

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response
    except Exception:
        return None


def logout_supabase_user(access_token):
    try:
        from petrotrack_backend.supabase_client import supabase

        supabase.auth.admin.sign_out(access_token)
        return True
    except Exception:
        return False


def get_supabase_user_id(supabase_response):
    try:
        user = getattr(supabase_response, "user", None)
        if not user:
            return None
        return getattr(user, "id", None)
    except Exception:
        return None


def get_supabase_session_data(auth_response):
    try:
        session = getattr(auth_response, "session", None)
        if not session:
            return None

        return {
            "access_token": getattr(session, "access_token", None),
            "refresh_token": getattr(session, "refresh_token", None),
            "expires_in": getattr(session, "expires_in", None),
            "expires_at": getattr(session, "expires_at", None),
            "token_type": getattr(session, "token_type", None),
        }
    except Exception:
        return None
