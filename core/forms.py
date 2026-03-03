# core/forms.py
from django import forms
from .models import Student, Enrollment, DisciplinaryRecord

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_number', 'last_name', 'first_name', 'middle_initial', 'sex', 'date_of_birth', 'address']

class DisciplinaryRecordForm(forms.ModelForm):
    offense_level = forms.CharField(max_length=50, required=False)
    details = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = DisciplinaryRecord
        fields = ['date_of_incident', 'demerits', 'action_taken']

    def clean(self):
        cleaned_data = super().clean()
        offense_level = cleaned_data.get('offense_level', 'Offense')
        details = cleaned_data.get('details', '')
        
        # We handle the legacy combined string logic safely here
        cleaned_data['remarks'] = f"[{offense_level}] {details}".strip()
        
        # Ensure demerits are safe
        if not cleaned_data.get('demerits'):
            cleaned_data['demerits'] = 0
            
        return cleaned_data