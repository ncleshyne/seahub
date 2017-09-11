# Copyright (c) 2012-2016 Seafile Ltd.

from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from django.template.defaultfilters import filesizeformat

from seaserv import seafile_api

from seahub.api2.authentication import TokenAuthentication
from seahub.api2.throttling import UserRateThrottle
from seahub.api2.utils import api_error
from seahub.utils import is_org_context
from seahub.utils.timeutils import timestamp_to_isoformat_timestr
from seahub.views import list_inner_pub_repos
from seahub.views.ajax import get_groups_by_user, get_group_repos


class SearchRepo(APIView):
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    throttle_classes = (UserRateThrottle, )

    def get(self, request):
        init_total_repos = []
        q = request.GET.get('q', '')
        if not q:
            error_msg = 'keywords can not be empty'
            return api_error(status.HTTP_400_BAD_REQUEST, error_msg)

        email = request.user.username
        if is_org_context(request):
            org_id = request.user.org.org_id
            init_total_repos.extend(seafile_api.get_org_owned_repo_list(org_id, email, 
                                                          ret_corrupted=True))
            init_total_repos.extend(seafile_api.get_org_share_in_repo_list(org_id, email, 
                                                             -1, -1))
        else:
            init_total_repos.extend(seafile_api.get_owned_repo_list(email, 
                                                      ret_corrupted=True))
            init_total_repos.extend(seafile_api.get_share_in_repo_list(email, -1, -1))
        groups = get_groups_by_user(request)
        init_total_repos.extend(get_group_repos(request, groups))
        if request.user.permissions.can_view_org():
            init_total_repos.extend(list_inner_pub_repos(request))
        total_repos = []
        for repo in init_total_repos:
            exists = False
            for r in total_repos:
                if repo.id == r.id:
                    exists = True
                    break
            if not exists:
                total_repos.append(repo)

        total_repos.sort(lambda x, y: cmp(y.last_modify, x.last_modify))
        res_total_repos = []
        for r in total_repos:
            # do not return virtual repos
            if r.is_virtual:
                continue

            if q.lower() in r.name.lower():
                repo = {
                    "id": r.id,
                    "name": r.name,
                    "mtime": r.last_modify,
                    "mtime_relative": timestamp_to_isoformat_timestr(r.last_modify),
                    "size": r.size,
                    "size_formatted": filesizeformat(r.size),
                    "encrypted": r.encrypted,
                    "permission": 'rw',  # Always have read-write permission to owned repo
                    "virtual": False,
                    "root": '',
                    "head_commit_id": r.head_cmmt_id,
                    "version": r.version,
                }
                res_total_repos.append(repo)

        return Response({'repos': res_total_repos})
