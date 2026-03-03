from django.contrib import admin
from .models import SchoolYear, Student, DisciplinaryRecord

admin.site.register(SchoolYear)
admin.site.register(Student)
admin.site.register(DisciplinaryRecord)