from hazard_calculator.models import *

import xlrd  # @UnresolvedImport
import re

acute_toxicity_list = [('acute_hazard_oral', 2000),
                       ('acute_hazard_dermal', 2000),
                       ('acute_hazard_gases', 20000),
                       ('acute_hazard_vapors', 20.0),
                       ('acute_hazard_dusts_mists', 5.0)]


hazard_list = ['acute_hazard_oral',
               'acute_hazard_dermal',
               'acute_hazard_gases',
               'acute_hazard_vapors',
               'acute_hazard_dusts_mists',               
               'skin_corrosion_hazard', 
               'eye_damage_hazard', 
               'germ_cell_mutagenicity_hazard', 
               'carcinogenicty_hazard', 
               'reproductive_hazard',
               'tost_single_hazard',
               'tost_repeat_hazard',
               'respiratory_hazard',
               'skin_sensitization_hazard']







path_to_labels = '/home/matta/label.xls'

#use regular expressions to match tokens with expected hazards

hazard_re = re.compile('([^(,\n]*(?:(?:\([^)]*\))*[^,(\n]*)*)[,\n]?')


"""
LD50 RE: covers ATI, ATO, and ATD; returns category and ld50
examples: ATI 5(300), ATO 3(300), ATI 4(3350 ppm), 

will match '#anything ATI #anything (digit) #anything ( #anything digits #anything )
"""

ld50_re = re.compile('AT([IOD])[^\d]*(\d)[^(\d]*\([^\d]*([\d]+)[^)]*')


        
"""        
EH RE: covers EH A and EH C; returns chronic/acute and category

there must be ONE SPACE between 'EH' and either 'A' or 'C' and no space between A/C and the category
"""

eh_re = re.compile('EH ([AC])(\d)')



"""
flammable_re: covers FL, FS, and FG

will find the first digit after either fl, fg, or fs
will not match if it does not contain fl fg or fs, or if there are no digits afterward
"""
flammable_re = re.compile('F([LGS])[^\d]*(\d)')


"""
tost_re: covers STO - SE and STO - RE

will find the first digit after SE or SR
will match '#ANYTHING STO #ANYTHING - #ANYTHING (S or R) E #ANYTHING digit

"""

tost_re = re.compile('STO[^-]-[^SR]([SR])E[^\d]*(\d)')

"""
These are the re's for SCI, EDI, and CAR
These are simpler to parse since each re covers one hazard, only need to find the category
"""

sci_re = re.compile('SCI[^\d]*(\d)')
edi_re = re.compile('EDI[^\d]*(\d)')
car_re = re.compile('CAR[^\d]*(\d)')


#this file defines the main function of this application
#it takes the path to the labels file, calculates the hazards, execute the callback function if it is defined,
#and return a dictionary of calculated hazards

def calculate_hazards(path_to_labels, callback_function = None):
    
    parsed_data = parse_hazards(path_to_labels)
    
    if callback_function != None:
        callback_function(parsed_data)



"""
CREATE SUBHAZARD DICT

Given the consolidated leaf weights of a flavor, create a dictionary which contains the total hazard accumulation
for each subhazard.

A 'subhazard' is a hazard + category combination; eg. 'skin_corrosion_hazard_1A'.

Input: A list of leafweight objects, corresponding to ingredients and weights for a single flavor
Output: A dictionary which contains the total 'accumulation' for each subhazard

"""

def create_subhazard_dict(leafweight_list):
    
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
    for ingredient, weight in self.consolidated_leafs.iteritems():
       
        hazard_dict['total_weight'] += weight
        
        for hazard in hazard_list:
            ingredient_hazard_category = getattr(ingredient, hazard)
            if ingredient_hazard_category != '':
                hazard_dict[hazard + '_' + ingredient_hazard_category] += weight
        
        #here I add weight/ld50 for each of the acute hazards
        for acute_hazard, max_ld50 in acute_toxicity_list:
            ld50_property = acute_hazard.split('acute_hazard_')[1] + '_ld50'
            unknown_weight_key = acute_hazard.split('acute_hazard_')[1] + '_unknown'
            
            ingredient_ld50 = getattr(ingredient, ld50_property)
            
            if ingredient_ld50 == None:
                #only add the weight to unknown_weight if its concentration is >10%
                #here I just assume that the total_weight is 1000 because it would be hard to do this check in the controller
                if (weight/1000) * 100 > 10: 
                    hazard_dict[unknown_weight_key] += weight
            elif ingredient_ld50 < max_ld50:
                hazard_dict[acute_hazard] += weight/getattr(ingredient, ld50_property)
            
                
    return hazard_dict



"""
CALCULATE_FLAVOR_HAZARDS

input: dictionary containing a list of flavors and their formulas
output: dictionary containing list of flavors and their hazards

"""

test_dictionary = {
                    'test flavor': {''}
                   
                   }

# def calculate_flavor_hazards():
    
    


"""
SAVE_INGREDIENT_HAZARDS

uses the parse_hazards function and saves the resulting data into the GHSIngredient model
"""

def save_ingredient_hazards():
    ingredient_hazard_dict = parse_hazards(path_to_labels)
    
    for cas in ingredient_hazard_dict:
        if ingredient_hazard_dict[cas]: #if the hazard dictionary for the corresponding cas number is NOT empty:
            g = GHSIngredient()
            g.cas = cas
            
            ingredient_hazards = ingredient_hazard_dict[cas]
            
            for hazard in ingredient_hazards:
                setattr(g, hazard, ingredient_hazards[hazard])
                
            g.save()
                              




        
"""
PARSE_HAZARDS

input: labels.xls
result: dictionary with cas numbers as keys, hazard info as values
"""


def parse_hazards(path_to_labels):
    
    
    labels = xlrd.open_workbook(path_to_labels)
    sheet = labels.sheets()[0]
    
    complete_hazard_dict = {}
    
    """
    ex: complete_hazard_dict = { 8851: 
                                    {
                                        'acute_aquatic_toxicity_hazard': 1
                                        'acute_hazard_oral': 3
                                        'oral_ld50': 100
                                    },
                                ...
                               }
    """
    for row in range(sheet.nrows):
        
        cas_number = sheet.cell(row, 0).value
        
        #each cas number should only appear once in the document
        #if not, have to change this code to account for a cas number appearing twice;
        #    currently, if a cas number appears twice, the hazards from the first occurence will be erased
        
        complete_hazard_dict[cas_number] = {}    
        ingredient_hazards = complete_hazard_dict[cas_number]  #easier to understand
        
        contents = sheet.cell(row, 3).value
        
        for token in hazard_re.findall(contents):
            for hazard, value in parse_token(token): #a single token may represent multiple fields
                ingredient_hazards[hazard] = value        #namely, ld50 hazards correspond to ld50 field and hazard field
            
            
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

def parse_token(token):
    
    """
    input: a token
    output: a list of (hazard, value) tuples 
    
    the output will most likely be a single tuple
    instances where there will be multiple tuples:
        - the token corresponds to an ld50 hazard
        - for some reason there are multiple hazards in the same token
            (this might happen if a typo caused two hazards to not be separated by comma)
            ex. token = 'ATO 5(4700) ATI 3(1000)'
    """

    hazard_list = []

    """
    
    First option: This is the 'less redundant' implementation, which uses the dictionary 're_dict' above.
    
    It can be hard to understand and uses a confusing data structure...
    

    
    """
    
    for re in re_dict:
        if re.search(token):
            re_results = re.findall(token)
            
            if len(re_results[0]) == 3: #ld50 hazards
                
                for hazard, category, ld50 in re_results:
                    for hazard_letter in re_dict[re]:
                        if hazard == hazard_letter:
                            hazard_list.append((re_dict[re][hazard_letter][0], category))
                            hazard_list.append((re_dict[re][hazard_letter][1], ld50))
                            
            elif len(re_results[0]) == 2: #tost, eh, flammable hazards
                
                for hazard, category in re_results:
                    for hazard_letter in re_dict[re]:
                        if hazard == hazard_letter:
                            hazard_list.append((re_dict[re][hazard_letter], category))
                            
            elif len(re_results[0]) == 1: #sci, edi, car hazards
                
                category = re_results[0]
                
                hazard_list.append((re_dict[re], category))
            
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
        
        
        
        
        
        

