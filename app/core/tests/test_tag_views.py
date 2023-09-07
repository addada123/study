from core.tests import test_factory
from core import models
import pytest

from django.urls import reverse
from recipe import serializers

pytestmark = pytest.mark.django_db

TAGS_URL = reverse('recipe:tag-list')

def detail_url(model_name, item_id):
    return reverse(f"recipe:{model_name}-detail", args=[item_id])

class TestTagsWOAuth:

    def test_retrieve_tags(self, api_client):
        test_factory.TagsFactory.create_batch(2)
        res = api_client.get(TAGS_URL)
        assert res.status_code == 401

class TestsTagsWAuth:
    
    def test_retrieve_tags(self, auth_client, user):
        test_factory.TagsFactory.create_batch(2, user=user)
        res = auth_client.get(TAGS_URL)
        tags = models.Tag.objects.all().order_by('-name')
        serializer = serializers.TagSerializer(tags, many=True)
        assert res.status_code == 200
        assert res.data == serializer.data
        
    def test_tags_limited_to_user(self, auth_client, user):
        user2 = test_factory.UserFactory()
        test_factory.TagsFactory.create(user=user2)

        tag = test_factory.TagsFactory.create(user=user)
        res = auth_client.get(TAGS_URL)

        assert res.status_code == 200
        assert len(res.data) == 1
        assert res.data[0]["name"] == tag.name
        assert res.data[0]["id"] == tag.id

    def test_tags_update(self, auth_client, user):
        tag = test_factory.TagsFactory.create(user=user)
        payload = {
            'name': "another tag"
        }
        url = detail_url("tag", tag.id)
        res = auth_client.patch(url, payload)
        assert res.status_code == 200
        tag.refresh_from_db()
        assert tag.name == payload["name"]


    def test_delete_tag(self, auth_client, user):
        tag = test_factory.TagsFactory.create(user=user)
        url = detail_url("tag", tag.id)
        res = auth_client.delete(url)

        assert res.status_code == 204
        tags = models.Tag.objects.filter(user=user)
        assert tags.exists() == False

    def test_filter_tags_assigned_to_recipes(self, auth_client, user):
        tag1 = test_factory.TagsFactory.create(user=user)
        tag2 = test_factory.TagsFactory.create(user=user)
        test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes = [tag1])
        res = auth_client.get(TAGS_URL, {'assigned_only': 1})
        s1 = serializers.TagSerializer(tag1)
        s2 = serializers.TagSerializer(tag2)
        assert s1.data in res.data
        assert s2.data not in res.data

    def test_filtered_tags_unique(self, auth_client, user):
        tag = test_factory.TagsFactory.create(user=user)
        test_factory.TagsFactory.create(user=user)
        test_factory.RecipeFactory.create_batch(2, user=user, ingredients_and_tags_and_likes = [tag])

        res = auth_client.get(TAGS_URL, {'assigned_only': 1})
        assert len(res.data) == 1

    