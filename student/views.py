from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import StudentProfileUpdateForm 

from .models import Student,skills
from comments.models import Comment
from django.contrib.auth.models import User

from .forms import StudentCreationForm, StudentUploadForm,skillform

from django.views.generic import ListView
from django.views.generic.base import TemplateView,View
from django.views.generic.edit import CreateView, FormView, DeleteView,UpdateView
from django.shortcuts import render,redirect,HttpResponseRedirect
from base.file_handlers import handle_student_csv
from .parsers import parse_query
from django.db.models import Q,Count
from posts.models import Post
from alumni.models import Alumni,Job,Higherstudies,Category
from admin.models import Event
import os
import requests
import json
from django.db.models import Count

import openai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings

def response(request):
    return HttpResponse('Hello')
def AllAlumniView(request):
    alumni = Alumni.objects.all()
    context = {'alumni': alumni}
    return render(request, 'student/all_alumni.html', context)

def response(request):
    return HttpResponse('Hello')

class StudentHomeView(View):
    def get(self,request):
        posts=Post.objects.all().order_by('-time_posted')[:2]
        # show upcoming events (same as alumni dashboard, but students cannot create events)
        events = Event.objects.all().order_by('-time_posted')[:2]
        context={'posts':posts, 'event': events}
        return render(request,"student/home.html",context)
    



def StudentListView(request):
    if'q'in request.GET:
        q=request.GET['q']
        #data=Internship.objects.filter(Full_name__icontains=q)
        multiple_q=Q(Q(usn__icontains=q)|Q(name__icontains=q)|Q(branch__icontains=q))
        data=Student.objects.filter(multiple_q).order_by('-usn')
    else:
        data=Student.objects.all().order_by('-usn')    
    context={'students':data}
    return render(request,"student/list.html",context)    

class StudentSearchView(ListView):
    model = Student
    template_name = 'student/list.html'
    context_object_name = 'students'
    arg = {}

    def get(self, request):
        self.__class__.arg = parse_query(request.GET['query'])
        return super().get(self, request)

    ordering = ['user']

    def get_queryset(self):
        return Student.objects.filter(**self.__class__.arg)

class StudentCommentView(ListView):
    model = Comment
    template_name = 'comments/list.html'
    context_object_name = 'posts'
    ordering = ['posted_by']

    def get_queryset(self):
        return Comment.objects.filter(posted_by=self.request.user)


class StudentCreateView(CreateView):
    model = Student
    form_class = StudentCreationForm
    template_name = 'student/new.html'

    def get_success_url(self):
        return reverse('list_student')

class StudentUploadView(FormView):
    form_class = StudentUploadForm
    template_name = 'student/upload.html'

    def form_valid(self, form):
        handle_student_csv(self.request.FILES["file"])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('list_student')

class StudentDeleteView(DeleteView):
    model = User

    def get_success_url(self):
        return reverse('list_student')

class StudentUpdateView(UpdateView):
    model=Student
    form_class = StudentCreationForm
    template_name = 'student/update.html'


    def get_success_url(self):
        return reverse('list_student')
def StudentProfileUpdateView(request):
    # Allow staff users to edit another student's profile by passing ?student_id=<id>
    student_id = request.GET.get('student_id') or request.POST.get('student_id')
    if student_id and request.user.is_staff:
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return redirect('list_student')
    else:
        student = Student.objects.get(user=request.user)

    skill_list = skills.objects.filter(stud=student)

    if request.method == "POST":
        form = StudentProfileUpdateForm(request.POST, request.FILES, instance=student)

        if form.is_valid():
            form.save()

            # Add new skill (optional)
            new_skill = request.POST.get("skill")
            if new_skill and new_skill.strip() != "":
                skills.objects.create(stud=student, skill=new_skill)

            # If staff edited another student, go back to student list; otherwise go to own profile
            if request.user.is_staff and student_id:
                return redirect('list_student')
            return redirect("sprofile")

    else:
        form = StudentProfileUpdateForm(instance=student)

    return render(request, "student/update_profile.html", {
        "form": form,
        "skills": skill_list,
        "editing_student": student,
    })


def SkillView(request):
    if request.method == 'POST':
        form=skillform(request.POST)
        if form.is_valid():
            instance=form.save(commit=False)
            instance.stud=Student.objects.get(user = request.user)
            instance.save()
            return redirect('/students/sprofile')
    else:        
        form=skillform()
    return render(request,'student/skillform.html',{'form':form})        

def sprofile(request):
    data=Student.objects.get(user=request.user)
    item=skills.objects.filter(stud=data)

    
    return render(request,'student/profile.html',{'data':data,'item':item})    

def view_student_profile(request, pk):
    """Public view to display any student's profile by primary key.

    This is used by other apps (e.g., alumni) to view a student's full profile and
    will render the same `student/profile.html` template.
    """
    try:
        data = Student.objects.get(pk=pk)
    except Student.DoesNotExist:
        return redirect('list_student')

    item = skills.objects.filter(stud=data)
    return render(request, 'student/profile.html', {'data': data, 'item': item})

def AlumniList(request):
    if'q'in request.GET:
        q=request.GET['q']
        
        #data=Internship.objects.filter(Full_name__icontains=q)
        multiple_q=Q(Q(usn__icontains=q)|Q(name__icontains=q)|Q(branch__icontains=q)|Q(job__company_name__icontains=q)|Q(job__role__icontains=q)|Q(higherstudies__specialization__icontains=q)|Q(higherstudies__degree__icontains=q)|Q(higherstudies__college_name__icontains=q))
        data=Alumni.objects.filter(multiple_q).order_by('-usn')
        context={'alumni':data}
        return render(request,"student/alsearch.html",context)
    else:
           
    
        return render(request,"student/alsearch.html",)    


openai.api_key = settings.OPENAI_API_KEY  # Store API key securely in settings.py

@csrf_exempt
def chatbot(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")

            if not user_message.strip():
                return JsonResponse({"error": "Empty message"}, status=400)

            # Generate interactive response using OpenAI API
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a friendly and knowledgeable assistant for a student-alumni portal. Provide helpful, clear, and engaging responses."},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.8,
                max_tokens=300
            )

            bot_reply = completion["choices"][0]["message"]["content"]

            return JsonResponse({"response": bot_reply})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        # For GET requests, show the chatbot UI (if you have chatbot.html)
        com = Job.objects.all().values('company_name').annotate(total=Count('id')).order_by('-total', 'company_name')[:1]
        alumni = Alumni.objects.all().count()
        uni = Higherstudies.objects.all().values('college_name').annotate(total=Count('id')).order_by('-total', 'college_name')[:1]

        context = {
            'com': com,
            'uni': uni,
            'alumni': alumni,
        }
        return render(request, 'student/chatbot.html', context)


