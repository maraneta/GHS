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

    product_hazards = None

    if request.method == 'POST':
        formset = FormulaFormSet(request.POST)
        if formset.is_valid():
            formula_list = []
            for form in formset.forms:
                try:
                    fli = FormulaLineItem(cas = form.cleaned_data['cas'],
                                       weight = form.cleaned_data['weight'])
                    formula_list.append(fli)
                except KeyError:
                    continue


            product_hazards = calculate_flavor_hazards(formula_list, human_readable=True)

            #formula_details contains information that will be displayed to the user
            formula_details = []

            total_weight = sum([fli.weight for fli in formula_list])
            for fli in formula_list:
                formula_details.append((fli.cas, GHSIngredient.objects.get(cas=fli.cas).name, fli.weight, fli.weight/total_weight * 100))

            return render_to_response('hazard_calculator/hazard_results.html',
                                 {'formset': formset.forms,
                                  'formula_list': formula_list,
                                  'product_hazards': product_hazards,
                                  'formula_details': formula_details,
                                  'management_form': formset.management_form,
                                  },
                                 context_instance=RequestContext(request))
            
    else:
        formset = FormulaFormSet()


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
