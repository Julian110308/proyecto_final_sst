import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sst_proyecto.settings')
django.setup()

from django.contrib.auth.forms import AuthenticationForm

form = AuthenticationForm()
print("Campos esperados por Django AuthenticationForm:")
for field_name in form.fields:
    print(f"  - {field_name}")
