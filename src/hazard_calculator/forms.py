from django import forms
from django.core.exceptions import ValidationError

from hazard_calculator.models import GHSIngredient

def validate_cas_number(cas):
    if GHSIngredient.objects.filter(cas=cas).count() == 0:
        raise ValidationError(u'Invalid CAS Number')

class CasNumberField(forms.CharField):
    default_validators = [validate_cas_number]

class FormulaRow(forms.Form):
    cas = CasNumberField(max_length=60,required=False)
    name = forms.CharField(max_length=60,required=False)  
    weight = forms.DecimalField(label="", max_digits=10, decimal_places=5)

