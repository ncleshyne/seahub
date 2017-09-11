import json
from mock import patch

from django.core.urlresolvers import reverse
from django.template.defaultfilters import filesizeformat

from seahub.test_utils import BaseTestCase
from seahub.utils.timeutils import timestamp_to_isoformat_timestr

from seaserv import seafile_api


class SearchRepoTest(BaseTestCase):
    def setUp(self):
        self.clear_cache()
        self.logout()
        self.login_as(self.user)
        self.url = reverse('search-repo')
        self.repo_id = self.repo

    def test_can_search(self):
        resp = self.client.get(self.url + "?q=t")
        resp_json = json.loads(resp.content)
        resp_json = resp_json['repos']
        assert self.repo.id in [e['id'] for e in resp_json]
        res_repo = [e for e in resp_json if e['id'] == self.repo.id][0]
        assert res_repo['id'] == self.repo.id
        #assert res_repo['owner'] == self.user.email
        assert res_repo['name'] == self.repo.name
        assert res_repo['mtime'] == self.repo.last_modify
        assert res_repo['mtime_relative'] == timestamp_to_isoformat_timestr(self.repo.last_modify)
        assert res_repo['size'] == self.repo.size
        assert res_repo['size_formatted'] == filesizeformat(self.repo.size)
        assert res_repo['encrypted'] == self.repo.encrypted
        assert res_repo['permission'] == 'rw'
        assert res_repo['virtual'] == False
        assert res_repo['root'] == ''
        assert res_repo['head_commit_id'] == self.repo.head_cmmt_id
        assert res_repo['version'] == self.repo.version

    def test_can_not_case_sensitive(self):
        resp = self.client.get(self.url + "?q=T")
        resp_json = json.loads(resp.content)
        resp_json = resp_json['repos']
        assert self.repo.id in [e['id'] for e in resp_json]
        res_repo = [e for e in resp_json if e['id'] == self.repo.id][0]
        assert res_repo['id'] == self.repo.id
        #assert res_repo['owner'] == self.user.email
        assert res_repo['name'] == self.repo.name
        assert res_repo['mtime'] == self.repo.last_modify
        assert res_repo['mtime_relative'] == timestamp_to_isoformat_timestr(self.repo.last_modify)
        assert res_repo['size'] == self.repo.size
        assert res_repo['size_formatted'] == filesizeformat(self.repo.size)
        assert res_repo['encrypted'] == self.repo.encrypted
        assert res_repo['permission'] == 'rw'
        assert res_repo['virtual'] == False
        assert res_repo['root'] == ''
        assert res_repo['head_commit_id'] == self.repo.head_cmmt_id
        assert res_repo['version'] == self.repo.version

    def test_can_search_be_shared(self):
        self.logout()
        self.login_as(self.admin)
        share_repo = seafile_api.get_repo(self.create_repo(
            name='test-share-repo', desc='', username=self.admin.username,
            passwd=None))
        share_url = reverse('api2-dir-shared-items', kwargs=dict(repo_id=share_repo.id))
        data = "share_type=user&permission=rw&username=%s" % self.user.username
        self.client.put(share_url, data, 'application/x-www-form-urlencoded')

        self.logout()
        self.login_as(self.user)
        resp = self.client.get(self.url + "?q=s")
        resp_json = json.loads(resp.content)
        resp_json = resp_json['repos']
        assert self.repo.id in [e['id'] for e in resp_json]
        res_repo = [e for e in resp_json if e['id'] == share_repo.id][0]
        assert res_repo['id'] == share_repo.id
        #assert res_repo['owner'] == self.admin.username
        assert res_repo['name'] == share_repo.name
        assert res_repo['mtime'] == share_repo.last_modify
        assert res_repo['mtime_relative'] == timestamp_to_isoformat_timestr(share_repo.last_modify)
        assert res_repo['size'] == share_repo.size
        assert res_repo['size_formatted'] == filesizeformat(share_repo.size)
        assert res_repo['encrypted'] == share_repo.encrypted
        assert res_repo['permission'] == 'rw'
        assert res_repo['virtual'] == False
        assert res_repo['root'] == ''
        assert res_repo['head_commit_id'] == share_repo.head_cmmt_id
        assert res_repo['version'] == share_repo.version

    def test_can_search_be_shared_to_group(self):
        self.logout()
        self.login_as(self.admin)
        share_repo = seafile_api.get_repo(self.create_repo(
            name='test-group-repo', desc='', username=self.admin.username,
            passwd=None))
        share_group_url = reverse('api2-dir-shared-items', kwargs=dict(repo_id=share_repo.id))
        data = "share_type=group&permission=rw&group_id=%s" % self.group.id
        self.client.put(share_group_url, data, 'application/x-www-form-urlencoded')

        self.logout()
        self.login_as(self.user)
        resp = self.client.get(self.url + "?q=s")
        resp_json = json.loads(resp.content)
        resp_json = resp_json['repos']
        assert self.repo.id in [e['id'] for e in resp_json]
        res_repo = [e for e in resp_json if e['id'] == share_repo.id][0]
        assert res_repo['id'] == share_repo.id
        #assert res_repo['owner'] == self.admin.username
        assert res_repo['name'] == share_repo.name
        assert res_repo['mtime'] == share_repo.last_modify
        assert res_repo['mtime_relative'] == timestamp_to_isoformat_timestr(share_repo.last_modify)
        assert res_repo['size'] == share_repo.size
        assert res_repo['size_formatted'] == filesizeformat(share_repo.size)
        assert res_repo['encrypted'] == share_repo.encrypted
        assert res_repo['permission'] == 'rw'
        assert res_repo['virtual'] == False
        assert res_repo['root'] == ''
        assert res_repo['head_commit_id'] == share_repo.head_cmmt_id
        assert res_repo['version'] == share_repo.version

    @patch('seahub.base.accounts.UserPermissions.can_view_org')
    def test_can_search_public_repos(self, mock_can_view_org):
        mock_can_view_org.return_value = True
        self.logout()
        self.login_as(self.admin)
        share_repo = seafile_api.get_repo(self.create_repo(
            name='test-public-repo', desc='', username=self.admin.username,
            passwd=None))
        share_group_url = reverse('api2-pub-repos')
        data = "name=public-repo"
        pub_repo = self.client.post(share_group_url, data, 'application/x-www-form-urlencoded')
        print json.loads(pub_repo.content)

        self.logout()
        self.login_as(self.user)
        resp = self.client.get(self.url + "?q=s")
        resp_json = json.loads(resp.content)
        resp_json = resp_json['repos']
        assert self.repo.id in [e['id'] for e in resp_json]
        res_repo = [e for e in resp_json if e['id'] == share_repo.id][0]
        assert res_repo['id'] == share_repo.id
        #assert res_repo['owner'] == self.admin.username
        assert res_repo['name'] == share_repo.name
        assert res_repo['mtime'] == share_repo.last_modify
        assert res_repo['mtime_relative'] == timestamp_to_isoformat_timestr(share_repo.last_modify)
        assert res_repo['size'] == share_repo.size
        assert res_repo['size_formatted'] == filesizeformat(share_repo.size)
        assert res_repo['encrypted'] == share_repo.encrypted
        assert res_repo['permission'] == 'rw'
        assert res_repo['virtual'] == False
        assert res_repo['root'] == ''
        assert res_repo['head_commit_id'] == share_repo.head_cmmt_id
        assert res_repo['version'] == share_repo.version
