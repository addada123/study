import os
import tempfile
import json

from PIL import Image

from django.utils import timezone
from django.urls import reverse
from django.urls import reverse

from core.tests import test_factory
from recipe import serializers
from core import models

import pytest

from decimal import Decimal


pytestmark = pytest.mark.django_db

INGREDIENTS_URL = reverse('recipe:ingredient-list')
TAGS_URL = reverse('recipe:tag-list')
RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(model_name, item_id):
    return reverse(f"recipe:{model_name}-detail", args=[item_id])

class TestIngredientsViewsWOAuth:

    def test_private_get(self, api_client):
        ingredients = api_client.get(INGREDIENTS_URL)
        recipes = api_client.get(RECIPES_URL) #Everyone can see recipes
        tags = api_client.get(TAGS_URL)
        assert [ingredients.status_code, recipes.status_code, tags.status_code] == [401, 200, 401] 

class TestIngredientsViewsWAuth:

    def test_login_permission(self, auth_client, user):
        ingredients = auth_client.get(INGREDIENTS_URL)
        tags = auth_client.get(TAGS_URL)
        assert [ingredients.status_code, tags.status_code] == [200, 200]

    """def test_create_endpoints(self, api_client, user):
        api_client.force_authenticate(user)
        ingredient_data = test_factory.IngredientsFactory(user=user)
        tag_data = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory()
        serialized_recipe = RecipeSerializer(recipe_data)
        print(serialized_recipe)
        ingredients = api_client.post(RECIPES_URL, json.dumps(serialized_recipe), content_type='application/json')
        assert ingredients.status_code == 201"""
    
    def test_create_recipe(self, auth_client, user):
        tag = test_factory.TagsFactory(user = user)
        ingredient = test_factory.IngredientsFactory(user = user)
        payload = {
            "title": "Sample recipe",
            "time_minutes": 30,
            "price": Decimal("5.99"),
            "tags": [tag.id],
            "ingredients": [ingredient.id]
        }
        #payload = test_factory.RecipeFactory.build(user = user, tags = [tag.id], ingredients = [ingredient.id])
        res_recipe = auth_client.post(RECIPES_URL, payload)
        assert res_recipe.status_code == 201
        assert models.Recipe.objects.count() == 1
        
    def test_delete_recipe(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory(user=user)
        tags = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes=(ingredients, tags))
        recipe_url = detail_url("recipe", recipe_data.id)
        assert models.Recipe.objects.count() == 1
        response = auth_client.delete(recipe_url)
        assert [models.Recipe.objects.count(), response.status_code] == [0, 204]

    def test_patch_recipe(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory(user=user)
        tags = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes=(ingredients, tags))
        starting_title = recipe_data.title
        payload = {"title": "TEST!"}
        url = detail_url("recipe", recipe_data.id)
        auth_client.patch(url, payload)
        recipe_data.refresh_from_db()
        assert recipe_data.title != starting_title
        assert recipe_data.title == payload["title"]

    def test_update_recipe(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory(user=user)
        tags = test_factory.TagsFactory(user=user)
        recipe_data = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes=(ingredients, tags))
        recipe_data_payload = test_factory.RecipeFactory.build(user=user)
        assert recipe_data != recipe_data_payload
        payload = {"title": recipe_data_payload.title,
                   "time_minutes": recipe_data_payload.time_minutes,
                   "price": recipe_data_payload.price}
        url = detail_url("recipe", recipe_data.id)
        auth_client.put(url, payload)
        recipe_data.refresh_from_db()
        assert recipe_data.title == payload["title"]
        assert recipe_data.time_minutes == payload["time_minutes"]
        assert recipe_data.price == payload["price"]

    def test_recipe_get(self, user, api_client): #RETURN BACK AND ASK 
        test_factory.RecipeFactory.create_batch(3, user=user)
        url = reverse("recipe:recipe-list")
        res = api_client.get(url)
        response_json = json.loads(res.content)
        print("/n")
        print(response_json)
        print("/n")
        recipes = models.Recipe.objects.all()
        serializer = serializers.RecipeSerializer(recipes, many=True)
        print(serializer.data)
        assert res.status_code == 200
        assert len(serializer.data) == 3


    def test_update_user_returns_error(self, auth_client, user):
        """Test changing the recipe user results in an error."""
        new_user = test_factory.UserFactory()
        recipe = test_factory.RecipeFactory.create(user=user)

        payload = {'user': new_user.id}
        url = detail_url("recipe", recipe.id)
        auth_client.patch(url, payload)

        recipe.refresh_from_db()
        assert recipe.user == user

    
    def test_create_recipe_with_new_tags(self, auth_client, user):
        recipe_data = test_factory.RecipeFactory.build()
        tags_data = test_factory.TagsFactory.build_batch(2)
        payload = {
            'title': recipe_data.title,
            'time_minutes': recipe_data.time_minutes,
            'price': recipe_data.price,
            'tags': [{'name': tags_data[0].name}, {'name': tags_data[1].name}],
        }
        res = auth_client.post(RECIPES_URL, payload, format='json')
        assert res.status_code == 201
        recipes = models.Recipe.objects.filter(user=user)
        assert recipes.count() == 1
        recipe = recipes[0]
        assert recipe.tags.count() == 2

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=user,
            ).exists()
            assert exists == True


    def test_create_recipe_with_existing_tags(self, auth_client, user):
        tags_data = test_factory.TagsFactory.create_batch(2, user=user)
        recipe_data = test_factory.RecipeFactory.build()
        payload = {
            'title': recipe_data.title,
            'time_minutes': recipe_data.time_minutes,
            'price': recipe_data.price,
            'tags': [{'name': tags_data[0].name}, {'name': tags_data[1].name}],
        }
        res = auth_client.post(RECIPES_URL, payload, format='json')
        assert res.status_code == 201
        recipes = models.Recipe.objects.filter(user=user)
        assert recipes.count() == 1
        recipe = recipes[0]
        assert recipe.tags.count() == 2
        assert tags_data[0] in recipe.tags.all()

        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=user,
            ).exists()
            assert exists == True

    def test_create_tag_on_update(self, auth_client, user):
        recipe = test_factory.RecipeFactory.create(user=user)
        tag_data = test_factory.TagsFactory.build(user=user)
        payload = {'tags': [{'name': tag_data.name}]}
        url = detail_url("recipe", recipe.id)
        res = auth_client.patch(url, payload, format='json')
        assert res.status_code == 200
        new_tag = models.Tag.objects.get(user=user, name=tag_data.name)
        assert new_tag in recipe.tags.all()

    def test_update_recipe_assign_tag(self, auth_client, user):
        tag_breakfast = test_factory.TagsFactory.create(user=user, name="Breakfast")
        recipe = test_factory.RecipeFactory.create(user=user)

        recipe.tags.add(tag_breakfast)

        tag_lunch = test_factory.TagsFactory.create(user=user, name = "Lunch")

        payload = {'tags': [{'name': tag_lunch.name}]}
        url = detail_url("recipe", recipe.id)
        res = auth_client.patch(url, payload, format='json')

        assert res.status_code == 200
        assert tag_lunch in recipe.tags.all()
        assert tag_breakfast not in recipe.tags.all()

    def test_clear_recipe_tags(self, auth_client, user):
        tag = test_factory.TagsFactory.create(user=user)
        recipe = test_factory.RecipeFactory.create(user=user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url("recipe", recipe.id)
        res = auth_client.patch(url, payload, format='json')

        assert res.status_code == 200
        assert recipe.tags.count() == 0

    def test_create_recipe_with_new_ingredients(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory.create_batch(2, user=user)
        recipe = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes=ingredients)
        recipes = models.Recipe.objects.filter(user=user)
        assert recipes.count() == 1
        recipe = recipes[0]
        assert recipe.ingredients.count() == 2
        for ingredient in recipe.ingredients.all():
            exists = recipe.ingredients.filter(
                name=ingredient.name,
                user=user,
            ).exists()
            assert exists == True

    def test_create_recipe_with_existing_ingredient(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory.create_batch(2, user=user)
        test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes = ingredients)

        recipes = models.Recipe.objects.filter(user=user)
        assert recipes.count() == 1

        recipe = recipes[0]
        assert recipe.ingredients.count() == 2
        for i in list(ingredients):
            assert i in recipe.ingredients.all()

        for ingredient in recipe.ingredients.all():
            exists = recipe.ingredients.filter(
                name=ingredient.name,
                user=user,
            ).exists()
            assert exists == True

    def test_create_ingredient_on_update(self, auth_client, user):
        recipe = test_factory.RecipeFactory.create(user=user)
        ingredient = test_factory.IngredientsFactory.build(user=user)
        payload = {'ingredients': [{'name': ingredient.name}]}
        url = detail_url("recipe", recipe.id)
        res = auth_client.patch(url, payload, format='json')
        assert res.status_code == 200
        new_ingredient = models.Ingredient.objects.get(user=user, name=ingredient.name)
        assert new_ingredient in recipe.ingredients.all()

    
    def test_update_recipe_assign_ingredient(self, auth_client, user):
        ingredients = test_factory.IngredientsFactory.create_batch(2, user=user)
        recipe = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes = [ingredients])
        payload = {'ingredients': [{'name': ingredients[1].name}]}
        url = detail_url("recipe", recipe.id)
        res = auth_client.patch(url, payload, format='json')

        assert res.status_code == 200
        assert ingredients[1] in recipe.ingredients.all()
        assert ingredients[0] not in recipe.ingredients.all()

    def test_clear_recipe_ingredients(self, auth_client, user):
        ingredient = test_factory.IngredientsFactory.create(user=user)
        recipe = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes = [ingredient])
        payload = {'ingredients': []}
        url = detail_url("recipe", recipe.id)
        res = auth_client.patch(url, payload, format='json')
        assert res.status_code == 200
        assert recipe.ingredients.count() == 0

    def test_created_at_default_now(self, user):
        recipe = test_factory.RecipeFactory.create(user=user)
        assert recipe.created_at is not None
        assert isinstance(recipe.created_at, timezone.datetime) is True
        assert recipe.created_at == pytest.approx(recipe.created_at, abs=timezone.timedelta(seconds=1))

    def test_created_at_not_editable(self, auth_client, user):
        recipe = test_factory.RecipeFactory.create(user=user)
        original_created_at = recipe.created_at
        new_created_at = original_created_at - timezone.timedelta(days=1)
        patch_data = {"created_at": new_created_at}
        res = auth_client.patch(RECIPES_URL, patch_data, content_type="application/json")
        assert res.status_code == 405
        recipe.refresh_from_db()
        assert recipe.created_at != new_created_at
        assert recipe.created_at == original_created_at
        

    def test_order_by_created_at(self,user):
        test_factory.RecipeFactory.create_batch(5, user=user)

        recipes1 = models.Recipe.objects.all().order_by('-created_at')
        recipes2 = models.Recipe.objects.all()
        assert recipes1 != recipes2

    def test_filter_by_created_at(self, auth_client, user):
        recipe = test_factory.RecipeFactory.create(user=user, created_at = "2023-01-16T22:44:35.334860+03:00")
        test_factory.RecipeFactory.create(user=user)
        created_at_date = recipe.created_at
        res = auth_client.get(RECIPES_URL, {'created_at': created_at_date})
        filtered_recipes = models.Recipe.objects.filter(created_at=created_at_date)
        assert res.status_code == 200
        assert len(res.data) == filtered_recipes.count()

    def test_query_by_name(self, user):
        test_factory.RecipeFactory.create(user = user, title = 'aabbcc')
        test_factory.RecipeFactory.create(user = user, title = 'aaweacc')
        test_factory.RecipeFactory.create(user = user, title = 'bbccaqsd')
        query = 'aa'
        results = models.Recipe.objects.filter(title__icontains=query) # research better method

        assert results.count() == 2

    def test_like_recipe(self, user):
        recipe = test_factory.RecipeFactory.create(user = user, title = 'test like')
        like = test_factory.LikeFactory.create(user = user, recipe=recipe)
        initial_like_count = recipe.likes_count.count()
        recipe.likes_count.add(like)
        updated_like_count = recipe.likes_count.count()
        assert updated_like_count == initial_like_count + 1

    def test_unlike_recipe(self, user):
        recipe = test_factory.RecipeFactory.create(user = user, title = 'test like')
        like = test_factory.LikeFactory.create(user = user, recipe=recipe)
        recipe.likes_count.add(like)
        initial_like_count = recipe.likes_count.count()
        recipe.likes_count.filter(user=user).delete()
        updated_like_count = recipe.likes_count.count()
        assert updated_like_count == initial_like_count - 1

    def test_filter_by_tags_or_by_ingredients(self, auth_client, user):
        tags = test_factory.TagsFactory.create_batch(3, user=user)
        ingredients = test_factory.IngredientsFactory.create_batch(3, user=user)

        recipes = []
        for i in range(3):
            recipe = test_factory.RecipeFactory.create(user=user, ingredients_and_tags_and_likes = (tags[i], ingredients[i]))
            recipes.append(recipe)

        params_tag = {'tags': f'{tags[0].id},{tags[1].id}'}
        res_tag = auth_client.get(RECIPES_URL, params_tag)
        params_ing = {'ingredients': f'{ingredients[0].id},{ingredients[1].id}'}
        res_ing = auth_client.get(RECIPES_URL, params_ing)


        expected_recipes = [serializers.RecipeSerializer(recipe).data for recipe in recipes[:2]]

        base_url = 'http://testserver'        
        for recipe in expected_recipes:
            image_path = recipe.get('image', '')
            if image_path:
                recipe['image'] = f'{base_url}{image_path}' 
                #add base_url to image field it because generates automatically in response data and dunno why
        
        response_data_tag = json.loads(json.dumps(res_tag.data))
        response_data_ing = json.loads(json.dumps(res_ing.data))
        for expected_recipe in expected_recipes:
            assert expected_recipe in response_data_tag
            assert expected_recipe in response_data_ing

        assert serializers.RecipeSerializer(recipes[2]).data not in response_data_tag
        assert serializers.RecipeSerializer(recipes[2]).data not in response_data_ing


class TestsImageUpload:
    def test_upload_image(self, auth_client, recipe):
        with tempfile.NamedTemporaryFile(suffix='.png') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
            'title': recipe.title,
            'time_minutes': recipe.time_minutes,
            'price': recipe.price,
            'image': image_file,
        }
            res = auth_client.post(RECIPES_URL, payload, format='multipart')
            recipe.refresh_from_db()
            assert res.status_code == 201
            assert 'image' in res.data
            assert os.path.exists(recipe.image.path)

        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {
            'title': recipe.title,
            'time_minutes': recipe.time_minutes,
            'price': recipe.price,
            'image': image_file,
        }
            res = auth_client.post(RECIPES_URL, payload, format='multipart')
            print(res.data)
            recipe.refresh_from_db()
            assert res.status_code == 400
            assert "Only PNG images are allowed." in res.data['image'][0]

        
