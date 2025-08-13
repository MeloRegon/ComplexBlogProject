from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.views.decorators.cache import cache_page, never_cache
from functools import wraps


from .models import Post, Tag
from .forms import PostForm


def cache_if_anonymous(timeout):
    """Cache this view only for anonymous users."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.is_authenticated:
                # no cache for logged-in users
                return view(request, *args, **kwargs)
            # anonymous: use per-URL cache
            return cache_page(timeout)(view)(request, *args, **kwargs)

        return wrapped

    return decorator

@cache_if_anonymous(60)
def post_list(request):
    q = (request.GET.get('q') or '').strip()  # read search query
    print('Rendering post_list view...')

    qs = Post.objects.all().order_by('-created_at')
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(tags__name__icontains=q) |
            Q(author__username__icontains=q)
        ).distinct()

    paginator = Paginator(qs, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        template_name='blog/post_list.html',
        context={
            'posts': page_obj.object_list,
            'page_obj': page_obj,
            'current_query': q,     # для value= в input и для JS
        }
    )


@cache_if_anonymous(60)
def post_detail(request, pk):
    post = Post.objects.get(pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            form.save_m2m()

            new_tags_str = form.cleaned_data.get('new_tags', '')
            if new_tags_str:
                tag_name = [tag.strip() for tag in new_tags_str.split(',')]
                for name in tag_name:
                    tag, created = Tag.objects.get_or_create(name=name)
                    post.tags.add(tag)
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request, 'blog/create_post.html', {'form': form})


@login_required
def update_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # if request.user != post.author:
    #     return HttpResponseForbidden()

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            form.save_m2m()

            new_tags_str = form.cleaned_data.get('new_tags', '')
            if new_tags_str:
                tag_name = [tag.strip() for tag in new_tags_str.split(',')]
                for name in tag_name:
                    tag, created = Tag.objects.get_or_create(name=name)
                    post.tags.add(tag)
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form':form})


@login_required
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if request.user != post.author:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    if request.method == 'POST':
        post.delete()
        return redirect('post_list')

    return render(request, 'blog/post_confirm_delete.html', {'post': post})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('post_list')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_view(request):
    user = request.user
    posts = Post.objects.filter(author=user).order_by('-created_at')
    return render(request, 'registration/profile.html', {'user': user, 'posts': posts})


def home_view(request):
    if request.user.is_authenticated:
        return redirect('profile')
    return redirect('post_list')


@never_cache
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('post_list')


def posts_by_tag(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    posts = Post.objects.filter(tags=tag)
    return render(request, 'blog/posts_by_tag.html', {'tag': tag, 'posts': posts})


@cache_if_anonymous(60)
def post_list_fragment(request):
    q = (request.GET.get('q') or '').strip()

    qs = Post.objects.all().order_by('-created_at')
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(tags__name__icontains=q) |
            Q(author__username__icontains=q)
        ).distinct()

    paginator = Paginator(qs, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    html = render_to_string('blog/_posts_chunk.html',
                            {'posts': page_obj.object_list},
                            request=request)

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'current_page': page_obj.number,
    })

@login_required
def settings_view(request):
    pwd_form = PasswordChangeForm(user=request.user, data=request.POST or None)

    if request.method == 'POST' and 'change_password' in request.POST:
        if pwd_form.is_valid():
            user = pwd_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated successfully.')
            return redirect('settings')
        else:
            messages.error(request, 'Please correct the errors below.')

    return render(request, 'registration/settings.html', {'pwd_form': pwd_form})