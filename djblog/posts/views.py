from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect

from comments.forms import CommentForm
from comments.models import Comment
from .forms import PostForm
from .models import Post


def post_create(request):
    # if not request.user.is_staff or not request.user.is_superuser:
    #     raise Http404
    storage = messages.get_messages(request)
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.user = request.user
        instance.save()
        messages.success(request, 'Post successfully created!')
        return redirect(instance.get_absolute_url())
    else:
        messages.error(request, 'Not successfully created!')
    context = {
        'form': form,
        'title': 'Create post',
        'messages': storage
    }
    return render(request, 'posts/post_form.html', context)


def post_detail(request, id=None):
    instance = get_object_or_404(Post, id=id)
    if instance.draft:
        if not request.user.is_staff or not request.user.is_superuser:
            raise Http404

    initial_data = {
        'content_type': instance.get_content_type,
        'object_id': instance.id
    }

    form = CommentForm(request.POST or None, initial=initial_data)
    # auth = request.user.is_authenticated
    # if not auth:
    #     messages.warning(request, 'You need to log in!')
    #     return redirect('accounts:login')
    if form.is_valid():
        c_type = form.cleaned_data.get('content_type')
        content_type = ContentType.objects.get(model=c_type.lower())
        obj_id = form.cleaned_data.get('object_id')
        content_data = form.cleaned_data.get('content')
        new_comment, created = Comment.objects.get_or_create(user=request.user, content_type=content_type,
                                                             object_id=obj_id, content=content_data)
        return redirect(instance.get_success_url())

    comments = instance.comments

    context = {
        'instance': instance,
        'title': 'Detail',
        'comments': comments,
        'comment_form': form,
    }
    return render(request, 'posts/post_detail.html', context)


def post_list(request):
    list_queryset = Post.active.all()
    if request.user.is_staff or request.user.is_superuser:
        list_queryset = Post.objects.all()

    query = request.GET.get('query')
    if query:
        list_queryset = list_queryset.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        ).distinct()
    paginator = Paginator(list_queryset, 4)
    page = request.GET.get('page')
    try:
        lists = paginator.page(page)
    except PageNotAnInteger:
        lists = paginator.page(1)
    except EmptyPage:
        lists = paginator.page(paginator.num_pages)

    context = {
        'object_list': lists,
        'title': 'List of posts'
    }
    return render(request, 'posts/post_list.html', context)


@login_required(login_url='accounts:login')
def post_edit(request, id=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, id=id)
    form = PostForm(request.POST or None, request.FILES or None, instance=instance)
    if form.is_valid():
        instance.save()
        messages.success(request, 'Post successfully edited!')
        return redirect(instance.get_absolute_url())
    else:
        messages.success(request, 'Not successfully edited!')
    context = {
        'title': 'Edit post',
        'instance': instance,
        'form': form
    }
    return render(request, 'posts/post_form.html', context)


@login_required
def post_delete(request, id=None):
    if not request.user.is_staff or not request.user.is_superuser:
        raise Http404
    instance = get_object_or_404(Post, id=id)
    instance.delete()
    messages.info(request, 'Post succesfully deleted')
    return redirect(instance.get_absolute_url())
