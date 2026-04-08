from django import forms
from django.contrib.auth.models import User
from .models import Student, DisciplinaryRecord, Section
from .models import Student, Section

# Used in the Staff Dashboard (XP UI)
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_number', 'last_name', 'first_name', 'sex', 'section']

# Used in the Disciplinary Module
class DisciplinaryRecordForm(forms.ModelForm):
    offense_level = forms.CharField(max_length=50, required=False)
    details = forms.CharField(widget=forms.Textarea, required=False)
    class Meta:
        model = DisciplinaryRecord
        fields = ['date_of_incident', 'demerits']

    def clean(self):
        cleaned_data = super().clean()
        offense_level = cleaned_data.get('offense_level', 'Offense')
        details = cleaned_data.get('details', '')
        cleaned_data['remarks'] = f"[{offense_level}] {details}".strip()
        return cleaned_data

# Used in Maintenance: Staff Creation
class StaffAccountForm(forms.ModelForm):
    employee_id = forms.CharField(max_length=20, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_staff = True
        if commit:
            user.save()
        return user

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['grade_level', 'name']

class StudentMaintenanceForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_number', 'first_name', 'last_name', 'sex', 'section']