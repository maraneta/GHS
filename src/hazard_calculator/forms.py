from django import forms

from hazard_calculator.models import GHSIngredient

import autocomplete_light

# class FormulaRow(autocomplete_light.ModelForm):
#     cas = forms.CharField(max_length=60,required=False,
#                           widget=autocomplete_light.TextWidget('CASAutocomplete'))  
#     name = forms.CharField(max_length=60,required=False)  
#     weight = forms.DecimalField(label="", max_digits=9, decimal_places=5)

# class FormulaRow(forms.Form):
#     cas = forms.ModelChoiceField(choices=GHSIngredient.objects.all(),
#                                  widget=autocomplete_light.ChoiceWidget('CASAutocomplete', GHSIngredient))  
#     name = forms.CharField(max_length=60,required=False)  
#     weight = forms.DecimalField(label="", max_digits=9, decimal_places=5)




class FormulaRow(forms.Form):
    cas = forms.CharField(max_length=60,required=False)
    name = forms.CharField(max_length=60,required=False)  
    weight = forms.DecimalField(label="", max_digits=9, decimal_places=5)



# class FormulaRow(autocomplete_light.ModelForm):
#     class Meta:
#         model = GHSIngredient
#         
#         autocomplete_fields = ('cas')