import json
from flask import url_for

from spendb.core import db
from spendb.tests.helpers import csvimport_fixture_path
from spendb.tests.base import ControllerTestCase
from spendb.tests.helpers import load_fixture, make_account
from spendb.tests.helpers import data_fixture


class TestSourceApiController(ControllerTestCase):

    def setUp(self):
        super(TestSourceApiController, self).setUp()
        self.cra = load_fixture('cra')
        self.user = make_account('test')
        self.auth_qs = {'api_key': self.user.api_key}
        self.cra.managers.append(self.user)
        self.cra_url = csvimport_fixture_path('../data', 'cra.csv')
        db.session.commit()

    def test_source_index(self):
        url = url_for('sources_api.index', dataset=self.cra.name)
        res = self.client.get(url)
        assert res.json['total'] == 0, res.json

    def test_source_upload_anon(self):
        url = url_for('sources_api.upload', dataset=self.cra.name)
        fh = data_fixture('cra')
        res = self.client.post(url, data={
            'file': (fh, 'cra.csv')
        })
        assert '403' in res.status, res.status

    def test_source_upload_no_file(self):
        url = url_for('sources_api.upload', dataset=self.cra.name)
        res = self.client.post(url, data={}, query_string=self.auth_qs)
        assert '400' in res.status, res.status

    def test_source_upload(self):
        url = url_for('sources_api.upload', dataset=self.cra.name)
        fh = data_fixture('cra')
        res = self.client.post(url, data={
            'file': (fh, 'cra.csv')
        }, query_string=self.auth_qs)
        assert '403' not in res.status, res.status

    def test_source_sign(self):
        # TODO: how to properly test this?
        url = url_for('sources_api.sign', dataset=self.cra.name)
        req = {'file_name': 'cra.csv'}
        res = self.client.post(url, data=req,
                               query_string=self.auth_qs)
        assert '200' in res.status, res.status
        assert 'status' in res.json, res.json
        assert res.json['status'] == 'error', res.json

    def test_source_submit_anon(self):
        url = url_for('sources_api.submit', dataset=self.cra.name)
        res = self.client.post(url, data={
            'url': self.cra_url
        })
        assert '403' in res.status, res.status

    def test_source_submit(self):
        url = url_for('sources_api.submit', dataset=self.cra.name)
        res = self.client.post(url, data={
            'url': self.cra_url
        }, query_string=self.auth_qs)
        assert '200' in res.status, res.status

    def test_source_load(self):
        url = url_for('sources_api.upload', dataset=self.cra.name)
        fh = data_fixture('cra')
        res = self.client.post(url, data={
            'file': (fh, 'cra.csv')
        }, query_string=self.auth_qs)

        self.client.post(url_for('sessions_api.logout'))

        url = url_for('sources_api.load', dataset=self.cra.name,
                      name='cra.csv')
        res = self.client.post(url)
        assert '403' in res.status, res.status
        res = self.client.post(url, query_string=self.auth_qs)
        assert '200' in res.status, res.status

    def test_source_load_non_existing(self):
        url = url_for('sources_api.load', dataset=self.cra.name,
                      name='foo.csv')
        res = self.client.post(url, query_string=self.auth_qs)
        assert '400' in res.status, res.json

    def test_source_view(self):
        url = url_for('sources_api.upload', dataset=self.cra.name)
        fh = data_fixture('cra')
        res = self.client.post(url, data={
            'file': (fh, 'cra.csv')
        }, query_string=self.auth_qs)
        assert res.json['extension'] == 'csv', res.json
        assert res.json['mime_type'] == 'text/csv', res.json
        url = url_for('sources_api.index', dataset=self.cra.name)
        res = self.client.get(url)
        assert res.json['total'] == 1, res.json
        frst = res.json['results'][0]
        assert frst['extension'] == 'csv', res.json
        assert frst['mime_type'] == 'text/csv', res.json
        assert frst['api_url'], res.json

    def test_source_serve(self):
        url = url_for('sources_api.upload', dataset=self.cra.name)
        fh = data_fixture('cra')
        res = self.client.post(url, data={
            'file': (fh, 'cra.csv')
        }, query_string=self.auth_qs)
        url = url_for('sources_api.serve', dataset=self.cra.name,
                      name=res.json['name'])
        res = self.client.get(url, query_string=self.auth_qs)
        assert 'text/csv' in res.headers['Content-Type'], res.json
