from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView

from newsletters.models import Newsletter
from users.forms import UserRegisterForm, UserProfileForm
from users.models import User


class LoginView(BaseLoginView):
    template_name = 'users/login.html'


class LogoutView(BaseLogoutView):
    pass


def activate_user(request, user_pk):
    """
    Activates user by link provided with verification email
    """
    user = User.objects.get(pk=user_pk)
    user.is_active = True
    user.save()
    # Add user to a USER group for newsletter and client management
    user_group = Group.objects.get(name='user_group')
    user_group.user_set.add(user)
    return HttpResponse('Thank you for your email confirmation.')


class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    success_url = reverse_lazy('users:login')
    template_name = 'users/register.html'

    # User validation for email verification
    def form_valid(self, form):
        self.object = form.save(commit=False)
        # Disable user
        self.object.is_active = False
        self.object.save()
        # Define mail subject
        subject = 'Email verification for Newsletter website'
        # Get current domain
        current_site = get_current_site(self.request)
        # Compose mail message
        message = render_to_string('users/email_verification.html',{
            'domain': current_site.domain,
            'pk': self.object.pk,
        })
        # Send email to a registered user
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[self.object.email]
        )
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user


@login_required
def deactivate_newsletter(request, pk):
    newsletter = Newsletter.objects.get(pk=pk)
    newsletter.status = 'finished'
    newsletter.save()
    return redirect(reverse('newsletters:newsletter_list'))


class UserListView(LoginRequiredMixin, ListView):
    model = User

    # Display only user's clients
    def get_queryset(self):
        return super().get_queryset().exclude(pk=self.request.user.pk)

@login_required
def deactivate_user(request, pk):
    user = User.objects.get(pk=pk)
    if user.is_active:
        user.is_active = False
    else:
        user.is_active = True
    user.save()
    return redirect(reverse('users:user_list'))