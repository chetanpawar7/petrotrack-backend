from user.models import UserMaster, RoleMaster, SubRoleMaster

def get_user(user_id):
    try:
        user = UserMaster.objects.filter(id=user_id,is_active=True).first()
        return user
    except UserMaster.DoesNotExist:
        return None
    
