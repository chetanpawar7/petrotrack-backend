from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from user.models import PageDetail, PageMaster, RoleMaster, SubRoleMaster
from utils import error_msg, response_translator


@transaction.atomic
def create_page(request):
    if not request.user.is_admin:
        return Response(response_translator.error_response(message=error_msg.ADMIN_ACCESS_REQUIRED), status=status.HTTP_403_FORBIDDEN)

    data = request.data
    required_fields = ("page_name", "page_code", "route_path")
    if any(not data.get(field) for field in required_fields):
        return Response(response_translator.error_response(message=error_msg.PAGE_REQUIRED_FIELDS), status=status.HTTP_400_BAD_REQUEST)

    page_code = str(data["page_code"]).strip().upper()
    route_path = str(data["route_path"]).strip()
    if PageMaster.objects.filter(page_code__iexact=page_code).exists():
        return Response(response_translator.error_response(message=error_msg.PAGE_CODE_ALREADY_EXISTS), status=status.HTTP_400_BAD_REQUEST)
    if PageMaster.objects.filter(route_path=route_path).exists():
        return Response(response_translator.error_response(message=error_msg.ROUTE_PATH_ALREADY_EXISTS), status=status.HTTP_400_BAD_REQUEST)

    parent = None
    if data.get("parent_id") is not None:
        parent = PageMaster.objects.filter(id=data["parent_id"], is_active=True).first()
        if not parent:
            return Response(response_translator.error_response(message=error_msg.PARENT_PAGE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

    try:
        display_order = int(data.get("display_order", 0))
        if display_order < 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response(response_translator.error_response(message=error_msg.INVALID_DISPLAY_ORDER), status=status.HTTP_400_BAD_REQUEST)

    page = PageMaster.objects.create(
        page_name=str(data["page_name"]).strip(),
        page_code=page_code,
        route_path=route_path,
        icon=data.get("icon"),
        parent=parent,
        display_order=display_order,
        is_menu=data.get("is_menu", True),
        is_active=data.get("is_active", True),
        created_by=request.user,
        updated_by=request.user,
    )
    result = {
        "id": page.id,
        "page_name": page.page_name,
        "page_code": page.page_code,
        "route_path": page.route_path,
        "icon": page.icon,
        "parent_id": page.parent_id,
        "display_order": page.display_order,
        "is_menu": page.is_menu,
        "is_active": page.is_active,
    }
    return Response(
        response_translator.success_response(data=result, message="Page created successfully"),
        status=status.HTTP_201_CREATED,
    )


@transaction.atomic
def assign_page_permissions(request):
    if not request.user.is_admin:
        return Response(response_translator.error_response(message=error_msg.ADMIN_ACCESS_REQUIRED), status=status.HTTP_403_FORBIDDEN)

    data = request.data
    page = PageMaster.objects.filter(id=data.get("page_id"), is_active=True).first()
    if not page:
        return Response(response_translator.error_response(message=error_msg.PAGE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

    role = RoleMaster.objects.filter(id=data.get("role_id"), is_active=True).first()
    if not role:
        return Response(response_translator.error_response(message=error_msg.ROLE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

    sub_role = None
    if data.get("sub_role_id") is not None:
        sub_role = SubRoleMaster.objects.filter(
            id=data["sub_role_id"], role=role, is_active=True
        ).first()
        if not sub_role:
            return Response(response_translator.error_response(message=error_msg.SUB_ROLE_NOT_FOUND_FOR_ROLE), status=status.HTTP_404_NOT_FOUND)

    control_types = data.get("permissions")
    if not isinstance(control_types, list) or not control_types:
        return Response(response_translator.error_response(message=error_msg.PERMISSIONS_LIST_REQUIRED), status=status.HTTP_400_BAD_REQUEST)

    allowed = {choice[0] for choice in PageDetail.CONTROL_TYPE_CHOICES}
    normalized = list(dict.fromkeys(str(item).strip().upper() for item in control_types))
    invalid = [item for item in normalized if item not in allowed]
    if invalid:
        return Response(response_translator.error_response(message=error_msg.INVALID_PERMISSIONS.format(", ".join(invalid))), status=status.HTTP_400_BAD_REQUEST)

    created = []
    existing = []
    for control_type in normalized:
        permission = PageDetail.objects.filter(
            page=page, role=role, sub_role=sub_role, control_type=control_type
        ).first()
        if permission:
            if not permission.is_active:
                permission.is_active = True
                permission.updated_by = request.user
                permission.save(update_fields=["is_active", "updated_by", "updated_at"])
            existing.append(control_type)
        else:
            PageDetail.objects.create(
                page=page,
                role=role,
                sub_role=sub_role,
                control_type=control_type,
                created_by=request.user,
                updated_by=request.user,
            )
            created.append(control_type)

    result = {
        "page_id": page.id,
        "role_id": role.id,
        "sub_role_id": sub_role.id if sub_role else None,
        "permissions": normalized,
        "created": created,
        "already_assigned": existing,
    }
    return Response(
        response_translator.success_response(
            data=result, message="Page permissions assigned successfully"
        ),
        status=status.HTTP_201_CREATED,
    )
