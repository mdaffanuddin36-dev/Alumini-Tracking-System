from django import forms


class MessageForm(forms.Form):
    body = forms.CharField(widget=forms.Textarea(attrs={'rows':3, 'class':'form-control', 'placeholder':'Type a message...'}), max_length=2000)
