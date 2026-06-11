from django import forms

_INPUT = (
    "w-full rounded-xl border border-luxury-line bg-white px-4 py-3.5 text-sm "
    "text-luxury-black placeholder:text-luxury-mid outline-none transition "
    "focus:border-luxury-black focus:ring-2 focus:ring-luxury-black/10"
)


class ContactForm(forms.Form):
    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Your name'}),
        error_messages={'required': 'Please enter your name.'},
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': _INPUT, 'placeholder': 'you@example.com'}),
        error_messages={
            'required': 'Please enter your email address.',
            'invalid': 'Please enter a valid email address.',
        },
    )
    phone = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Phone (optional)'}),
    )
    subject = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'How can we help?'}),
        error_messages={'required': 'Please add a subject.'},
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': _INPUT, 'rows': 5, 'placeholder': 'Your message'}),
        error_messages={'required': 'Please write your message.'},
    )

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError('Please provide a little more detail (at least 10 characters).')
        return message
