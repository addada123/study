import factory
import factory.fuzzy

import pytz

from factory.django import DjangoModelFactory

from core import models

class UserFactory(DjangoModelFactory):
    class Meta:
        model = models.User
    
    email = factory.Faker("email")
    name = factory.Faker("name")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or factory.Faker(
            "password",
            length=8,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        ).evaluate(None, None, extra={"locale": None})
        self.set_password(password)

class RecipeFactory(DjangoModelFactory):
    class Meta:
        model = models.Recipe
    user = factory.SubFactory("core.tests.test_factory.UserFactory")
    title = factory.Faker("sentence", nb_words = 15)
    description = factory.Faker("text")
    time_minutes = factory.Faker("random_int", min = 5, max = 150)
    price = factory.fuzzy.FuzzyDecimal(low=0, high=50, precision=2)
    link = factory.Faker("url")
    image = factory.django.ImageField(
        width=400, height=300, format='JPEG', color='blue', filename='example.jpg'
    )


    @factory.post_generation
    def ingredients_and_tags_and_likes(self, create, extracted, **kwargs):
        if not create:
            return
        for item in extracted:
            if isinstance(item, models.Ingredient):
                self.ingredients.add(item)
            elif isinstance(item, models.Tag):
                self.tags.add(item)
            elif isinstance(item, models.Like):
                self.likes.add(item)


class IngredientsFactory(DjangoModelFactory):
    class Meta:
        model = models.Ingredient

    name = factory.Faker("pystr", min_chars=1, max_chars=5)
    user = factory.SubFactory(UserFactory)

class TagsFactory(DjangoModelFactory):
    class Meta:
        model = models.Tag

    name = factory.Faker("pystr", min_chars=1, max_chars=5)
    user = factory.SubFactory(UserFactory)

class LikeFactory(DjangoModelFactory):
    class Meta:
        model = models.Like

    user = factory.SubFactory("core.tests.test_factory.UserFactory")
    
    @factory.post_generation
    def recipes(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for item in extracted:
            if isinstance(item, models.Recipe):
                self.recipe.add(item)