from django.contrib.auth import get_user_model
from django.urls import reverse
from core.tests import test_factory
from core import models


import pytest

pytestmark = pytest.mark.django_db

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token_obtain_pair')
ME_URL = reverse('user:me')

def create_user(**params):
    return get_user_model().objects.create_user(**params)

class TestPublicUserApi:

    def test_create_user_success(self, api_client):
        payload = {
            'email' : 'test@example.com',
            'password': '123123123',
            'name': 'test user',
        }

        res = api_client.post(CREATE_USER_URL, payload)
        assert res.status_code == 201

        user = get_user_model().objects.get(email = payload["email"])
        assert user.check_password(payload["password"])
        assert 'password' not in res.data

    def test_user_with_email_exists_error(self, api_client):
        payload = {
            'email': 'test@example.com',
        }
        user = test_factory.UserFactory.create(email = payload['email'])

        res = api_client.post(CREATE_USER_URL, payload)
        assert res.status_code == 400

    def password_is_too_short_error(self, api_client):
        payload = {
            'email': 'test@example.com',
            'password': '1',
            'name': 'testtest'
        }

        res = api_client.post(CREATE_USER_URL, payload)
        assert res.status_code == 400
        user_exists = get_user_model().objects.filter(
            email = payload["email"]
        ).exists()
        assert user_exists == True

    def test_create_token_for_user(self, api_client):

        user = test_factory.UserFactory.create(password="123asd123!123")
        payload = {
            'email': user.email,
            'password': "123asd123!123",
        }
        res = api_client.post(TOKEN_URL, payload)
        assert 'access' in res.data
        assert res.status_code == 200

    def test_create_token_bad_credentials(self, api_client):
        test_factory.UserFactory.create(email="test@example.com", password="123asd123!123")

        payload = {'email': 'test@example.com', 'password': 'badpass'}
        res = api_client.post(TOKEN_URL, payload)
        assert 'access' not in res.data
        assert res.status_code == 401
    
    def test_create_token_email_not_found(self, api_client):
        payload = {'email': 'test@example.com', 'password': 'pass123'}
        res = api_client.post(TOKEN_URL, payload)
        assert 'access' not in res.data
        assert res.status_code == 401

    def test_create_token_blank_password(self, api_client):
        payload = {'email': 'test@example.com', 'password': ''}
        res = api_client.post(TOKEN_URL, payload)
        assert 'access' not in res.data
        assert res.status_code == 400

    def test_retrieve_user_unauthorized(self, api_client):
        res = api_client.get(ME_URL)
        assert res.status_code == 401
    

class TestPrivateUserApi:

    def test_retrieve_profile_success(self, auth_client, user):
        res = auth_client.get(ME_URL)
        assert res.status_code == 200
        assert res.data == {'name': user.name,
                            'email': user.email}

    def test_post_me_not_allowed(self, auth_client):
        res = auth_client.post(ME_URL, {})
        assert res.status_code == 405

    def test_update_user_profile(self, auth_client, user):
        payload = {'name': 'Updated name', 'password': 'newpassword123'}
        res = auth_client.patch(ME_URL, payload)
        user.refresh_from_db()
        assert user.name == payload["name"]
        assert user.check_password(payload["password"]) is True
        assert res.status_code == 200
