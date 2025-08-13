from django import forms

from .models import Post, Tag

class PostForm(forms.ModelForm):
    # tags = forms.ModelMultipleChoiceField(
    #     queryset=Tag.objects.all(),
    #     widget=forms.CheckboxSelectMultiple,
    #     required=False,
    #     label="Select tags"
    # )

    new_tags = forms.CharField(
        max_length=200,
        required=False,
        label='Enter new tags separated by commas'
    )

    class Meta:
        model = Post
        fields = ['title', 'content', 'tags', 'image']