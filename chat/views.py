from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Message
from .forms import MessageForm
from django.db.models import Q
from .utils import call_openai_chat
from django.conf import settings


@login_required
def conversations_list(request):
    """List distinct conversation partners for the logged-in user."""
    user = request.user
    # Get users who sent to or received from current user
    partners = User.objects.filter(Q(sent_messages__recipient=user) | Q(received_messages__sender=user)).distinct()
    return render(request, 'chat/list.html', {'partners': partners})


@login_required
def thread_view(request, pk):
    other = get_object_or_404(User, pk=pk)
    user = request.user

    # Only allow messaging between alumni and students (both are users); app-level permission check could be added

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            body = form.cleaned_data['body']
            Message.objects.create(sender=user, recipient=other, body=body)

            # If this thread is with the configured bot user, call OpenAI
            bot_username = getattr(settings, 'CHAT_BOT_USERNAME', 'openai_bot')
            try:
                if str(other.username) == str(bot_username):
                    try:
                        reply = call_openai_chat(body)
                    except Exception as e:
                        reply = f"Sorry, I couldn't reach the AI service: {e}"
                    # Save the bot reply into the thread
                    Message.objects.create(sender=other, recipient=user, body=reply)
            except Exception:
                # Defensive: don't break user flow on unexpected errors
                pass

            return redirect('chat_thread', pk=other.pk)
    else:
        form = MessageForm()

    # messages between the two users
    messages = Message.objects.filter(
        Q(sender=user, recipient=other) | Q(sender=other, recipient=user)
    ).order_by('timestamp')

    # mark unread messages addressed to current user as read
    unread = messages.filter(recipient=user, read=False)
    unread.update(read=True)

    return render(request, 'chat/thread.html', {'other': other, 'messages': messages, 'form': form})


@login_required
def openai_chat(request):
    """Simple chat endpoint that sends user message to OpenAI and stores bot reply.

    This creates/uses a local user `openai_bot` as the message sender for replies.
    After posting it redirects to the thread view between the user and the bot.
    """
    user = request.user
    if request.method != 'POST':
        return redirect('chat_list')

    body = request.POST.get('body', '').strip()
    if not body:
        return redirect('chat_list')

    # Ensure bot user exists
    bot_username = getattr(settings, 'CHAT_BOT_USERNAME', 'openai_bot')
    bot_user, created = User.objects.get_or_create(username=bot_username, defaults={'email': 'bot@example.com'})
    if created:
        bot_user.set_unusable_password()
        bot_user.save()

    # Save user's message to bot
    Message.objects.create(sender=user, recipient=bot_user, body=body)

    # Call OpenAI
    try:
        reply = call_openai_chat(body)
    except Exception as e:
        # In case of error, store an error message as bot reply
        reply = f"Sorry, I couldn't reach the AI service: {e}"

    # Save bot reply
    Message.objects.create(sender=bot_user, recipient=user, body=reply)

    return redirect('chat_thread', pk=bot_user.pk)
