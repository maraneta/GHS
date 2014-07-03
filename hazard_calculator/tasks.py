from hazard_calculator.models import *
from hazard_calculator.utils import *

#from hazard_calculator import utils
#use utils.blah

#from hazard_calculator import models as hazard_models etc

#acute_toxicity_list, hazard_list, path_to_labels, hazard_re, ld50_re, eh_re, flammable_re, tost_re, sci_re, edi_re, car_re

import xlrd  # @UnresolvedImport
import re


def create_subhazard_dict(formula_list):

    """
    Given the consolidated leaf weights of a flavor (in the form of FormulaLineItem objects), 
    create a dictionary which contains the total hazard accumulation for each subhazard.
    
    A 'subhazard' is a hazard + category combination; eg. 'skin_corrosion_hazard_1A'.
    
    Input: A list of leafweight objects, corresponding to ingredients and weights for a single flavor
    Output: A dictionary which contains the total 'accumulation' for each subhazard
    
    """
    
    #The KEYS in this dictionary are in the format 'subhazard_category' (eg. 'skin_corrosion_hazard_1A')
    #The VALUES are the accumulation of ingredient weights that correspond to each hazard
    hazard_dict = {}
    
    #include the total weight and unknown weight of the flavor in the dict
    hazard_dict['total_weight'] = 0
    
    
    #initialize all unknown_weights for acute hazards to zero
    #there will be an unknown weight for each hazard; eg. hazard_dict['oral_unknown'], ...
    for hazard in hazard_list[:5]:
        hazard_dict[hazard.split('acute_hazard_')[1] + '_unknown'] = 0
    
    #initialize all the values to zero
    for hazard in hazard_list[5:]:  #I do the list splice because I don't want the acute hazards in here
        for category in GHSIngredient._meta.get_field(hazard).choices:
            if category[0] != 'No':     #category[0] and category[1] are always the same
                hazard_dict[hazard + '_' + category[0]] = 0
                
    '''
    CALCULATING ACUTE TOXICITY HAZARDS (NOT THE SAME AS CALCULATING OTHER HAZARDS)
    
    A BUNCH OF ALGEBRA TO GET THE FINAL FORMULA BELOW 
    
    The formula to obtain the ld50 of a flavor is:
        (100 - unknown_concentration)/flavor_ld50 = Sigma(ingredient_concentration/ingredient_ld50)
        
    To calculate the final sum of the Sigma operation, I would originally do something like:
        
        for ingredient in ingredients_under_the_ld50_threshold:
            sigma += (weight/total_weight * 100) / ingredient.ld50
            
    However, since I'm calculating the total_weight in the same loop, I do not yet have access
        to the total weight.  To work around this, I factor our the 100/total_weight from the sigma
        equation since these remain constant.  I end up with:
        
        for ingredient in ingredients_under_the_ld50_threshold:
            sigma += weight / ingredient.ld50
            
    The value 'sigma' above is what I store in the hazard_dict for each acute hazard.        
                
    We know that:
    
        LD50_flavor = (100 - unknown_concentration) / (100 * sigma/total_weight),
        
        unknown_concentration = (weight_unknown/total_weight) * 100
        
    Substitute everything in:
    
        LD50_flavor = (100 - 100 * (weight_unknown/total_weight)) / 100 * (sigma/total_weight)
        
    Cancel out the 100's: 
    
        LD50_flavor = (1 - weight_unknown/total_weight) / (sigma/total_weight),
    
    Replace the 1 on the left side with total_weight/total_weight, then cancel the total_weights:
    
    FINAL FORMULA ------------------------------------------------------------------------
            
        LD50_flavor = (total_weight - weight_unknown) / sigma
        
            where sigma = sum(ingredient_weights/ingredient_ld50s)
        
    --------------------------------------------------------------------------------------

    Steps to calculate ld50 of a flavor:
    1. Store weight_unknown and sigma in the hazard_dictionary
        -Note: Each acute subhazard (oral, dermal, etc.) needs its own weight_unknown
    2. In the controller, use the total_weight and the final formula above to find LD50_flavor    

            
    '''
    
    #sigma(weight/ld50), explained above
    for acute_hazard, max_ld50 in acute_toxicity_list:
        hazard_dict[acute_hazard] = 0
            
    #for each base ingredient in the flavor, find any hazards it has and add its weight to each of those
    for fli in formula_list:
        
#         try:
        ingredient = GHSIngredient.objects.get(cas = fli.cas)
#         except:
#             print fli.cas
            
        weight = fli.weight
        
        hazard_dict['total_weight'] += weight
        
        #for each NON-acute hazard that the ingredient has, add the ingredient's weight to the correct subhazard key 
        for hazard in hazard_list[5:]:
            ingredient_hazard_category = getattr(ingredient, hazard)
            if ingredient_hazard_category != '':
                print ingredient.cas, ingredient.skin_corrosion_hazard
                hazard_dict[hazard + '_' + ingredient_hazard_category] += weight
        
        #here I add weight/ld50 for each of the acute hazards
        for acute_hazard, max_ld50 in acute_toxicity_list:
            ld50_property = acute_hazard.split('acute_hazard_')[1] + '_ld50' #ex. oral_ld50
            unknown_weight_key = acute_hazard.split('acute_hazard_')[1] + '_unknown' #ex. oral_unknown
            
            ingredient_ld50 = getattr(ingredient, ld50_property)
            
            if ingredient_ld50 == None:
                #only add the weight to unknown_weight if its concentration is >10%
                #here I just assume that the total_weight is 1000 because it would be hard to do this check in the controller
                if (weight/1000) * 100 > 10: 
                    hazard_dict[unknown_weight_key] += weight
            elif ingredient_ld50 < max_ld50:
                hazard_dict[acute_hazard] += weight/getattr(ingredient, ld50_property)
            

    return hazard_dict



# """
# CALCULATE_FLAVOR_HAZARDS
# 
# input: dictionary containing a list of flavors and their formulas
# output: dictionary containing list of flavors and their hazards
# 
# """
# 
# test_dictionary = {
#                     'test flavor': {''}
#                    
#                    }
# 
# # def calculate_flavor_hazards():
    
    



def save_ingredient_hazards():
    
    """
    This function uses the parse_hazards function and
    saves the resulting data into the GHSIngredient model.
    """    
    
    ingredient_hazard_dict = parse_hazards(path_to_labels)
    
    for cas in ingredient_hazard_dict:
        
        if cas == '00-00-00':
            g = GHSIngredient(cas=cas)

        
        elif ingredient_hazard_dict[cas]: #if the hazard dictionary for the corresponding cas number is NOT empty:
            g = GHSIngredient()
            g.cas = cas
            
            ingredient_hazards = ingredient_hazard_dict[cas]
            
            for hazard in ingredient_hazards:
                setattr(g, hazard, ingredient_hazards[hazard])
                
        g.save()
                              

def parse_hazards(path_to_labels):
    
    """
    Input: labels.xls
    Output: dictionary where keys are cas numbers and values are 
            hazard dictionaries for that ingredient
            
    ex: complete_hazard_dict = { 8851: 
                                    {
                                        'acute_aquatic_toxicity_hazard': 1
                                        'acute_hazard_oral': 3
                                        'oral_ld50': 100
                                    },
                                ...
                               }            
            
    """
    
    
    labels = xlrd.open_workbook(path_to_labels)
    sheet = labels.sheets()[0]
    
    complete_hazard_dict = {}
    
    for row in range(sheet.nrows):
        
        cas_number = sheet.cell(row, 0).value
        
        #each cas number should only appear once in the document
        #if not, have to change this code to account for a cas number appearing twice;
        #    currently, if a cas number appears twice, the hazards from the first occurence will be erased
        
        complete_hazard_dict[cas_number] = {}    
        ingredient_hazards = complete_hazard_dict[cas_number]  #easier to understand
        
        contents = sheet.cell(row, 3).value
        
        #print contents
        
        try:
            for hazard, value in parse_token(contents):
                ingredient_hazards[hazard] = value
        except DuplicateHazardError as e:
            print "The ingredient with cas number %s has the following duplicate hazards: \n" % cas_number
            for hazard in e.duplicate_hazards:
                print hazard
            print "Please change the input document and ensure those hazards are not repeated."
        
#         for token in hazard_re.findall(contents):
#             for hazard, value in parse_token(token): #a single token may represent multiple fields
#                 ingredient_hazards[hazard] = value        #namely, ld50 hazards correspond to ld50 field and hazard field
#             
    
    #create a placeholder ingredient for ingredients with no cas number
    complete_hazard_dict['00-00-00'] = {}
          
    return complete_hazard_dict
          

   
    
re_dict = {
                ld50_re:
                    {
                        'O': ('acute_hazard_oral', 'oral_ld50'),
                        'D': ('acute_hazard_dermal', 'dermal_ld50'),
                        'I': ('acute_hazard_inhalation', 'inhalation_ld50')
                     },
                eh_re: 
                    {
                        'A': 'acute_aquatic_toxicity_hazard',
                        'C': 'chronic_aquatic_toxicity_hazard'
                     },
                flammable_re:
                    {
                        'L': 'flammable_liquid_hazard',
                        'G': 'emit_flammable_hazard',
                        'S': 'flammable_solid_hazard'
                     },
                tost_re:
                    {
                        'S': 'tost_single_hazard',
                        'R': 'tost_repeat_hazard'
                    },
                sci_re: 'skin_corrosion_hazard',
                edi_re: 'eye_damage_hazard',
                car_re: 'carcinogenicty_hazard,'
                
                
          }


class DuplicateHazardError(Exception):
    def __init__(self, duplicate_hazards):
        self.duplicate_hazards = duplicate_hazards
    def __str__(self):
        return repr(self.duplicate_hazards)
         


def parse_token(token):
    
    """
    input: a token (here, a token represents the content in a cell)
    output: a list of (hazard, value) tuples 
    
    the output will most likely be a single tuple.
    instances where there will be multiple tuples:
        - the token corresponds to an ld50 hazard
        - for some reason there are multiple hazards in the same token
            (this might happen if a typo caused two hazards to not be separated by comma)
            ex. token = 'ATO 5(4700) ATI 3(1000)'
    """

    hazard_list = []

    """
    
    First option: Less code, harder to understand
    
    My attempt to explain what is going on here:
    
    1. The outer for loop goes through all the keys in the re_dict, which are regular expressions.
    2. Each regular expression matches what it can in the content string.
    3. Each 're.findall' will return a list of tuples, where each tuple corresponds to a hazard.
    4. The tuples that are returned will be different sizes depending on the regular expression.
        -the ld50_re will return tuples of length 3 (contains hazard, category, and ld50)
        -the tost, eh, and flammable re's will return tuples of length 2 (hazard, category)
        -the sci, edi, and car re's do not return tuples, just a list of strings
            >in this case, I just check to see if the first item in the list is a string and not a tuple.
    5. Once I determine the size of the tuples, I use the captured information to add the correct data
        to the hazard_list (by using re_dict).
        
    EXAMPLE: 
        -we are iterating through the re's and reach the ld50_re 
        -re.findall(token) returns [('O', '3', '100')]
        -since the tuple is of length 3, we know it is an ld50 hazard
        -we set the variables in the returned tuple (for hazard, category, ld50 in re_results):
            hazard = '0'
            category = '3'
            ld50 = 100
        -using re_dict[re], we find the letter that matches the hazard 'O', and 
            obtain the corresponding hazards to return: ('acute_hazard_oral', 'oral_ld50')
        -we append the two hazards to the hazard_list as (hazard, value) tuples:
            -('acute_hazard_oral', '3')
            -('oral_ld50', 100)
    
    
    """
    
    
    '''
    write a class for each set of re's?
    
    
    
    change the structure of re_dict so I don't have to determine the length of the returned tuples
    losing information; dont need if statements
    just split re_dict into three different groups and iterate over those groups
    '''
    
    for re in re_dict:
        if re.search(token):
            re_results = re.findall(token)

        #re_results = re.findall(token)
            

            if len(re_results[0]) == 3: #ld50 hazards
                 
                for hazard, category, ld50 in re_results:
                    for hazard_letter in re_dict[re]:
                        if hazard == hazard_letter:
                            hazard_list.append((re_dict[re][hazard_letter][0], category))
                            hazard_list.append((re_dict[re][hazard_letter][1], ld50))
                             
            elif len(re_results[0]) == 2 and not isinstance(re_results[0], basestring): #tost, eh, flammable hazards
                 
                print re, re_results[0]
                 
                for hazard, category in re_results:
                    for hazard_letter in re_dict[re]:
                        if hazard == hazard_letter:
                            hazard_list.append((re_dict[re][hazard_letter], category))
                             
            elif isinstance(re_results[0], basestring): #sci, edi, car hazards
                 
                category = re_results[0]
                
                for category in re_results: #there should only be one unless the same hazard is repeated
                    hazard_list.append((re_dict[re], category))
                        
    '''
    Here I check if any hazards for one ingredient have been duplicated.  
    
    If so, raise an exception which is caught by parse_hazards.  Then add the cas number to a list of
    invalid rows.
    '''
            
    unique_list = []
    duplicate_list = []
    for hazard, value in hazard_list:
        if hazard in unique_list and hazard not in duplicate_list:
            duplicate_list.append(hazard)
        elif hazard not in unique_list:
            unique_list.append(hazard)
        
    if len(duplicate_list) > 0:
        raise DuplicateHazardError(duplicate_list)
                                
            
    return hazard_list
            
    """
    
    This implementation, while easier to understand, uses many similar if statements and takes a lot
        more space than the previous implementation.

    if ld50_re.search(token):
        re_results = ld50_re.findall(token) #
        for hazard, category, ld50 in re_results: #result will be in the form ('D', '5', '4700')

            if hazard == 'O':
                hazard_list.append(('acute_hazard_oral', category))
                hazard_list.append(('oral_ld50', ld50))
            elif hazard == 'D':
                hazard_list.append(('acute_hazard_dermal', category))
                hazard_list.append(('dermal_ld50', ld50))
            elif hazard == 'I':
                hazard_list.append(('acute_hazard_inhalation', category))
                hazard_list.append(('inhalation_ld50', ld50)) #currently no inhalation ld50 in database
            
    
    if eh_re.search(token):
        re_results = eh_re.findall(token)
        
        for hazard, category in re_results:
            
            if hazard == 'A':
                hazard_list.append(('acute_aquatic_toxicity_hazard', category))
            elif hazard == 'C':
                hazard_list.append(('chronic_aquatic_toxicity_hazard', category))

    if flammable_re.search(token):
        re_results = flammable_re.findall(token)
        
        for hazard, category in re_results:
            if hazard == 'L':
                hazard_list.append(('flammable_liquid_hazard', category))
            elif hazard == 'G':
                hazard_list.append(('emit_flammable_hazard', category))
            elif hazard == 'S':
                hazard_list.append(('flammable_solid_hazard', category))
    
    if tost_re.search(token):
        re_results = tost_re.findall(token)
        
        for hazard,_category in re_results:
            if hazard == 'R':
                hazard_list.append(('tost_single_hazard', category))
            elif hazard == 'S':
                hazard_list.append(('tost_repeat_hazard', category))
    
    if len(sci_re.findall(token)) > 0:
        category = sci_re.findall(token)[0] #only one
        
        hazard_list.append(('skin_corrosion_hazard', category))
    
    if len(edi_re.findall(token)) > 0:
        category = edi_re.findall(token)[0]
        
        hazard_list.append(('eye_damage_hazard', category))
        
    if len(car_re.findall(token)) > 0:
        category = car_re.findall(token)[0]
        
        hazard_list.append(('carcinogenicty_hazard', category)) 
        
    return hazard_list

    """        
        
        
        
        
        
        

    
        
        



