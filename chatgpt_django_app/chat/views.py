from django.urls import reverse
from django.views import View
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from django.http import HttpResponseRedirect
from turbo_helper import turbo_stream

from .models import Chat, Message
from .forms import MessageForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin


from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib import messages
from .forms import UserRegisterForm


from django.contrib.auth import authenticate, login
from .forms import UserLoginForm


@method_decorator(csrf_exempt, name='dispatch')
class IndexView(LoginRequiredMixin,View):
    
    def get(self, request):
        # If no chat exists, create a new chat and redirect to the message list page.
        chat = Chat.objects.first()
        if not chat:
            chat = Chat.objects.create()

        return HttpResponseRedirect(reverse("chat:message-list", args=[chat.pk]))

    def post(self, request, *args, **kwargs):
        # create new chat object and redirect to message list view
        instance = Chat.objects.create()
        return HttpResponseRedirect(reverse("chat:message-list", args=[instance.pk]))


index_view = IndexView.as_view()

class MessageListView(LoginRequiredMixin,ListView):
    model = Message
    template_name = "message_list_page.html"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(chat_id=self.kwargs["chat_pk"])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["chats"] = Chat.objects.all()
        return context


message_list_view = MessageListView.as_view()

# this is the view that creates a new message
class MessageCreateView(LoginRequiredMixin,CreateView):
    model = Message
    template_name = "message_create.html"
    form_class = MessageForm

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    # get_success_url is the url that the user will be redirected to after creating a new message
    def get_success_url(self):
        return None
    
    # get_form_kwargs is the kwargs that are passed to the form
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["chat_pk"] = self.kwargs.get("chat_pk")
        kwargs["role"] = Message.USER
        return kwargs
    
    # get_empty_form is the empty form that is passed to the form
    def get_empty_form(self):
        """
        Return empty form so we can reset the form
        """
        form_class = self.get_form_class()
        kwargs = self.get_form_kwargs()
        kwargs.pop("data")
        kwargs.pop("files")
        kwargs.pop("instance")
        return form_class(**kwargs)
    
    # this method is called when the form is valid
    def form_valid(self, form):
        super().form_valid(form)

        return turbo_stream.response(
            turbo_stream.replace(
                "message_create",
                template=self.template_name,
                context={
                    "form": self.get_empty_form(),
                    "view": self,
                },
                request=self.request,
            ),
        )


message_create_view = MessageCreateView.as_view()



@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(FormView):
    template_name = 'register.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('login')  # Redirect to login page after successful registration

    def form_valid(self, form):
        # Save the new user
        form.save()
        username = form.cleaned_data.get('username')
        messages.success(self.request, f'Account created for {username}!')
        return super().form_valid(form)
    


@method_decorator(csrf_exempt, name='dispatch')
class UserLoginView(FormView):
    template_name = 'login.html'
    form_class = UserLoginForm
    #success_url = reverse_lazy('chat:index')  # Redirect to message list after successful login

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Welcome back, {username}!')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Invalid username or password.')
            return self.form_invalid(form)
        


