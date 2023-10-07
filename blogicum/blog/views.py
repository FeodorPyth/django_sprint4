import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.urls import reverse

from .models import Post, Category, Comment, User
from .forms import CommentForm, PostForm, ProfileForm


class PostMixin(LoginRequiredMixin):
    model = Post
    template_name = 'blog/create.html'


class CommentMixin(LoginRequiredMixin):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Comment,
            id=kwargs['comment_id'],
        )
        if instance.author != request.user:
            return redirect('blog:post_detail', id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs['post_id']}
        )


class PostListView(ListView):
    model = Post
    queryset = Post.objects.select_related(
        'author', 'category', 'location').filter(
            pub_date__lte=datetime.datetime.now(),
            is_published=True,
            category__is_published=True
    )
    template_name = 'blog/index.html'
    paginate_by = 10


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'id'

    def get_object(self, queryset=None):
        obj = super(PostDetailView, self).get_object(queryset=queryset)
        if obj.author == self.request.user:
            return get_object_or_404(
                Post, id=self.kwargs['id']
            )
        else:
            return get_object_or_404(
                Post.objects.select_related('author', 'category', 'location')
                .filter(
                    pub_date__lte=datetime.datetime.now(),
                    is_published=True,
                    category__is_published=True
                ),
                id=self.kwargs['id']
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class CategoryListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/category.html'

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return category.posts.filter(
            is_published=True,
            pub_date__lte=datetime.datetime.now()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug']
        )
        return context


class PostCreateView(PostMixin, CreateView):
    form_class = PostForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user])


class PostUpdateView(PostMixin, UpdateView):
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(Post, id=kwargs['post_id'])
        if instance.author != request.user:
            return redirect('blog:post_detail', id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs['post_id']}
        )


class PostDeleteView(PostMixin, DeleteView):
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Post,
            id=kwargs['post_id']
        )
        if instance.author != request.user:
            return redirect('blog:post_detail', id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user])


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    template_name = 'blog/comment.html'
    object = None
    form_class = CommentForm
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Post, id=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        post = Post.objects.get(id=self.kwargs['post_id'])
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'id': self.kwargs['post_id']}
        )


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    ...


class ProfileListView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        return Post.objects.select_related('author').filter(
            author__username=self.kwargs['username']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.request.user])
