from django import forms

class FormulaRow(forms.Form):
    cas = forms.CharField(max_length=60,required=False)  
    name = forms.CharField(max_length=60,required=False)  
    weight = forms.DecimalField(label="", max_digits=9, decimal_places=5)

    