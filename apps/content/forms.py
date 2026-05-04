"""Forms for post authoring + comment submission."""
from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    publish = forms.BooleanField(
        required=False,
        help_text="Publish now (still goes through moderation).",
    )

    class Meta:
        model = Post
        fields = ["title", "excerpt", "body", "hero_image"]
        widgets = {
            "title":   forms.TextInput(attrs={"class": "input", "maxlength": 200}),
            "excerpt": forms.TextInput(attrs={"class": "input", "maxlength": 300,
                                               "placeholder": "1–2 sentences for cards + meta"}),
            "body":    forms.Textarea(attrs={"class": "input", "rows": 18,
                                              "placeholder": "# Markdown supported\n\nWrite your post here…"}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "input", "rows": 4,
                                           "placeholder": "Add to the conversation…"}),
        }
