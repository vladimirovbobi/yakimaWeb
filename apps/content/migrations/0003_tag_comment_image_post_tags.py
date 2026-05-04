"""Sprint 5: Tag model, Post.tags M2M, Comment.image."""
from django.db import migrations, models

import apps.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0002_alter_post_hero_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=80)),
            ],
            options={
                "verbose_name": "Tag",
                "verbose_name_plural": "Tags",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="post",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="posts", to="content.tag"),
        ),
        migrations.AddField(
            model_name="comment",
            name="image",
            field=models.ImageField(
                blank=True,
                help_text="Optional image attachment. Image moderation runs post-save.",
                null=True,
                upload_to="content/comments/",
                validators=[apps.core.validators.MaxFileSizeValidator(10)],
            ),
        ),
    ]
