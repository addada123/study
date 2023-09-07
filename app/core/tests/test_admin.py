from django.urls import reverse
import pytest

pytestmark = pytest.mark.django_db

class TestsAdminsite:
    def test_users_lists(self, admin_auth_client, admin_user):
        url = reverse('admin:core_user_changelist')
        res = admin_auth_client.get(url, user=admin_user.id, follow=True)
        assert res.status_code == 200  # Check if the name is present in the content ASK HERE

    def test_edit_user_page(self, admin_auth_client, admin_user):
        url = reverse('admin:core_user_change', args=[admin_user.id])
        res = admin_auth_client.get(url, follow=True)
        assert res.status_code == 200

    def test_create_user_page(self, admin_auth_client):
        url = reverse('admin:core_user_add')
        res = admin_auth_client.get(url, follow=True)
        assert res.status_code == 200
