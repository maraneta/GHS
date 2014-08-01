# Create your views here.
import re

from django.forms.models import modelformset_factory, formset_factory
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils import simplejson

from hazard_calculator.tasks import calculate_flavor_hazards
from hazard_calculator.models import FormulaLineItem, GHSIngredient
from hazard_calculator.forms import FormulaRow

def hazard_calculator(request):
    page_title = "GHS Hazard Calculator"
    
    FormulaFormSet = formset_factory(FormulaRow, extra=5, can_delete=True)
    
    if request.method == 'POST':
        formset = FormulaFormSet(request.POST)
        if formset.is_valid():
            formula_list = []
            for form in formset.forms:
                fli = FormulaLineItem(cas = form.cleaned_data['cas'],
                                       weight = form.cleaned_data['weight'])
                formula_list.append(fli)
            
            product_hazards = calculate_flavor_hazards(formula_list)
            
    else:
        formset = FormulaFormSet()
        product_hazards = None
        

    return render_to_response('hazard_calculator/hazard_calculator.html', 
                      {'page_title': page_title,
                       'formset': formset.forms,
                       'product_hazards': product_hazards,
                       'management_form': formset.management_form,
                       },
                       context_instance=RequestContext(request))    
    
def ingredient_autocomplete(request):
    """
    This returns a JSON object that is an array of objects that have 
    the following properties: id, label, value. Labels are shown to
    the user in the form of a floating dialog. 
    """
    # this is provided by the jQuery UI widget
    term = request.GET['term']

    ret_array = []

    term = str(term)
    
    if GHSIngredient.objects.filter(cas__icontains=term):
        ingredients = GHSIngredient.objects.filter(cas__icontains=term)
    else:
        ingredients = GHSIngredient.objects.filter(name__icontains=term)
    
        
    for ingredient in ingredients:
        ingredient_json = {}
        ingredient_json["cas"] = ingredient.cas
        ingredient_json["label"] = ingredient.__unicode__()
        ingredient_json["value"] = ingredient_json["cas"]
        ret_array.append(ingredient_json)
    return HttpResponse(simplejson.dumps(ret_array), content_type='application/json; charset=utf-8')    
