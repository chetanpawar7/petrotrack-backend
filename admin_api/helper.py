from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from user.models import PageDetail, PageMaster, RoleMaster, SubRoleMaster
from utils import error_msg, response_translator, success_msg


def get_bool_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ("true", "1", "yes"):
            return True
        if value in ("false", "0", "no"):
            return False
    return bool(value)


def get_positive_int(value):
    try:
        value = int(value)
        if value <= 0:
            raise ValueError
        return value
    except (TypeError, ValueError):
        return None


def get_page_source(value, default=None):
    source = str(value or default or "").strip().lower()
    if source in ("admin", "client"):
        return source
    return None


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
    source = get_page_source(data.get("source"), "admin")
    if not source:
        return Response(response_translator.error_response(message="Invalid page source"), status=status.HTTP_400_BAD_REQUEST)

    if PageMaster.objects.filter(page_code__iexact=page_code).exists():
        return Response(response_translator.error_response(message=error_msg.PAGE_CODE_ALREADY_EXISTS), status=status.HTTP_400_BAD_REQUEST)
    if PageMaster.objects.filter(route_path=route_path).exists():
        return Response(response_translator.error_response(message=error_msg.ROUTE_PATH_ALREADY_EXISTS), status=status.HTTP_400_BAD_REQUEST)

    parent = None
    if data.get("parent_id") is not None:
        parent = PageMaster.objects.filter(id=data["parent_id"], is_active=True).first()
        if not parent:
            return Response(response_translator.error_response(message=error_msg.PARENT_PAGE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)
        if parent.source and parent.source.lower() != source:
            return Response(response_translator.error_response(message="Parent page source must match page source"), status=status.HTTP_400_BAD_REQUEST)

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
        source=source,
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
        "source": page.source,
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
    page_id = get_positive_int(data.get("page_id"))
    if not page_id:
        return Response(response_translator.error_response(message=error_msg.PAGE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

    page = PageMaster.objects.filter(id=page_id).first()
    if not page:
        return Response(response_translator.error_response(message=error_msg.PAGE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

    page_updated = False
    if "page_is_active" in data:
        page_is_active = get_bool_value(data.get("page_is_active"))
        PageMaster.objects.filter(id=page.id).update(
            is_active=page_is_active,
            updated_by_id=request.user.id,
        )
        page.is_active = page_is_active
        page_updated = True

    control_types = data.get("permissions", [])
    if not isinstance(control_types, list) or not control_types:
        if page_updated:
            result = {
                "page_id": page.id,
                "page_name": page.page_name,
                "page_is_active": page.is_active,
                "page_updated": page_updated,
                "permissions": [],
                "created": [],
                "updated": [],
            }
            return Response(
                response_translator.success_response(
                    data=result, message="Page permissions assigned successfully"
                ),
                status=status.HTTP_200_OK,
        )
        return Response(response_translator.error_response(message=error_msg.PERMISSIONS_LIST_REQUIRED), status=status.HTTP_400_BAD_REQUEST)

    role_id = get_positive_int(data.get("role_id"))
    if not role_id:
        return Response(response_translator.error_response(message=error_msg.ROLE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

    role = RoleMaster.objects.filter(id=role_id, is_active=True).first()
    if not role:
        return Response(response_translator.error_response(message=error_msg.ROLE_NOT_FOUND), status=status.HTTP_404_NOT_FOUND)

    sub_role = None
    if data.get("sub_role_id") is not None:
        sub_role_id = get_positive_int(data.get("sub_role_id"))
        if not sub_role_id:
            return Response(response_translator.error_response(message=error_msg.SUB_ROLE_NOT_FOUND_FOR_ROLE), status=status.HTTP_404_NOT_FOUND)

        sub_role = SubRoleMaster.objects.filter(
            id=sub_role_id, role=role, is_active=True
        ).first()
        if not sub_role:
            return Response(response_translator.error_response(message=error_msg.SUB_ROLE_NOT_FOUND_FOR_ROLE), status=status.HTTP_404_NOT_FOUND)

    allowed = {choice[0] for choice in PageDetail.CONTROL_TYPE_CHOICES}
    normalized = {}
    invalid = []
    for item in control_types:
        if isinstance(item, dict):
            control_type = str(item.get("control_type") or "").strip().upper()
            is_active = get_bool_value(item.get("is_active", True))
        else:
            control_type = str(item).strip().upper()
            is_active = True

        if control_type not in allowed:
            invalid.append(control_type)
            continue
        normalized[control_type] = is_active

    if invalid:
        return Response(response_translator.error_response(message=error_msg.INVALID_PERMISSIONS.format(", ".join(invalid))), status=status.HTTP_400_BAD_REQUEST)

    created = []
    updated = []
    for control_type, is_active in normalized.items():
        permission_qs = PageDetail.objects.filter(
            page=page, role=role, sub_role=sub_role, control_type=control_type
        )
        permission = permission_qs.first()
        if permission:
            permission_qs.update(is_active=is_active, updated_by_id=request.user.id)
            permission.is_active = is_active
            updated.append(
                {
                    "permission_id": permission.id,
                    "control_type": permission.control_type,
                    "is_active": permission.is_active,
                }
            )
        else:
            permission = PageDetail.objects.create(
                page=page,
                role=role,
                sub_role=sub_role,
                control_type=control_type,
                is_active=is_active,
                created_by=request.user,
                updated_by=request.user,
            )
            created.append(
                {
                    "permission_id": permission.id,
                    "control_type": permission.control_type,
                    "is_active": permission.is_active,
                }
            )

    result = {
        "page_id": page.id,
        "page_name": page.page_name,
        "page_is_active": page.is_active,
        "page_updated": page_updated,
        "role_id": role.id,
        "sub_role_id": sub_role.id if sub_role else None,
        "permissions": list(normalized.keys()),
        "created": created,
        "updated": updated,
    }
    return Response(
        response_translator.success_response(
            data=result, message="Page permissions assigned successfully"
        ),
        status=status.HTTP_201_CREATED,
    )


def get_page_list(request):
    if not request.user.is_admin:
        return Response(response_translator.error_response(message=error_msg.ADMIN_ACCESS_REQUIRED), status=status.HTTP_403_FORBIDDEN)

    data = request.data
    try:
        limit = int(data.get("limit", 10))
        offset = int(data.get("offset", 0))
        if limit <= 0 or offset < 0:
            raise ValueError
    except (TypeError, ValueError):
        return Response(
            response_translator.error_response(message="Invalid limit or offset"),
            status=status.HTTP_400_BAD_REQUEST,
        )

    source = get_page_source(data.get("source"), "admin")
    if not source:
        return Response(response_translator.error_response(message="Invalid page source"), status=status.HTTP_400_BAD_REQUEST)

    source_filter = Q(source__iexact=source)
    if source == "admin":
        source_filter |= Q(source__isnull=True) | Q(source="")

    pages = (
        PageMaster.objects.select_related("parent")
        .filter(source_filter)
        .order_by("display_order", "id")
    )

    if data.get("page_id"):
        pages = pages.filter(id=data.get("page_id"))
    
    search_text = str(data.get("search_text") or "").strip()
    if search_text:
        pages = pages.filter(
            Q(page_name__icontains=search_text)
            | Q(page_code__icontains=search_text)
            | Q(route_path__icontains=search_text)
        )

    total_count = pages.count()
    page_list = list(pages[offset:offset + limit])
    page_ids = [page.id for page in page_list]

    permissions = (
        PageDetail.objects.select_related("role", "sub_role")
        .filter(page_id__in=page_ids)
        .order_by("page_id", "role__role_name", "sub_role__sub_role_name", "control_type")
    )

    if data.get("role_id"):
        permissions = permissions.filter(role_id=data.get("role_id"))
    if "sub_role_id" in data:
        if data.get("sub_role_id") is None:
            permissions = permissions.filter(sub_role__isnull=True)
        else:
            permissions = permissions.filter(sub_role_id=data.get("sub_role_id"))
    if "is_active" in data:
        permissions = permissions.filter(is_active=get_bool_value(data.get("is_active")))

    permissions_by_page = {}
    for permission in permissions:
        role = permission.role
        sub_role = permission.sub_role

        permissions_by_page.setdefault(permission.page_id, []).append(
            {
                "permission_id": permission.id,
                "role_id": role.id,
                "role_name": role.role_name,
                "sub_role_id": sub_role.id if sub_role else None,
                "sub_role_name": sub_role.sub_role_name if sub_role else None,
                "control_type": permission.control_type,
                "is_active": permission.is_active,
            }
        )

    result = [
        {
            "page_id": page.id,
            "page_name": page.page_name,
            "page_code": page.page_code,
            "route_path": page.route_path,
            "icon": page.icon,
            "parent_id": page.parent_id,
            "parent_name": page.parent.page_name if page.parent else None,
            "display_order": page.display_order,
            "is_menu": page.is_menu,
            "is_active": page.is_active,
            "source": page.source,
            "permissions": permissions_by_page.get(page.id, []),
        }
        for page in page_list
    ]

    return Response(
        response_translator.success_response(
            data=result,
            message=success_msg.PAGE_PERMISSIONS_FETCHED_SUCCESSFULLY,
            total_count=total_count,
        ),
        status=status.HTTP_200_OK,
    )
