from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from user.models import UserMaster


class SupabaseAuthentication(BaseAuthentication):
	"""
	Authenticate requests using a Supabase access token provided in the
	`Authorization: Bearer <token>` header. Maps the Supabase user id to the
	internal `UserMaster` instance via the `supabase_user_id` field.
	"""

	def authenticate(self, request):
		auth_header = None
		# DRF provides .headers in newer versions; Django provides META
		try:
			auth_header = request.headers.get('Authorization')
		except Exception:
			auth_header = None

		if not auth_header:
			auth_header = request.META.get('HTTP_AUTHORIZATION')

		if not auth_header:
			return None

		parts = auth_header.split()
		if len(parts) != 2 or parts[0].lower() != 'bearer':
			raise AuthenticationFailed('Invalid Authorization header.')

		token = parts[1]

		try:
			from petrotrack_backend.supabase_client import supabase

			auth_client = supabase.auth

			# Support both v2 (`auth.get_user(token)`) and older clients
			user_resp = None
			if hasattr(auth_client, 'get_user'):
				user_resp = auth_client.get_user(token)
			elif hasattr(auth_client, 'api') and hasattr(auth_client.api, 'get_user'):
				user_resp = auth_client.api.get_user(token)

			if not user_resp:
				raise AuthenticationFailed('Invalid or expired token.')

			# `user_resp` may be an object with `user` attribute or a dict
			user = getattr(user_resp, 'user', None) or (user_resp.get('user') if isinstance(user_resp, dict) else None)
			if not user:
				raise AuthenticationFailed('Invalid token payload.')

			supabase_user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)
			if not supabase_user_id:
				raise AuthenticationFailed('Invalid token payload.')

			# Find internal user matching this Supabase user id
			user_obj = UserMaster.objects.filter(supabase_user_id=supabase_user_id, is_active=True).first()
			if not user_obj:
				raise AuthenticationFailed('User not found.')

			# DRF expects a `(user, auth)` tuple. We don't use a token object here.
			return (user_obj, None)

		except AuthenticationFailed:
			raise
		except Exception:
			raise AuthenticationFailed('Authentication failed.')

	def authenticate_header(self, request):
		return 'Bearer'

