from hazard_calculator.models import GHSIngredient, HazardAccumulator, MultiplePhaseError
from hazard_calculator.utils import acute_toxicity_list, hazard_list, cas_re
from hazard_calculator.mylogger import logger

#from hazard_calculator import utils
#use utils.blah

#from hazard_calculator import models as hazard_models etc

#acute_toxicity_list, hazard_list, path_to_labels, cas_re, hazard_re, ld50_re, eh_re, flammable_re, tost_re, sci_re, edi_re, car_re


import xlrd  # @UnresolvedImport
import re




# """
# CALCULATE_FLAVOR_HAZARDS
# 
# input: 
# output: dictionary containing list of flavors and their hazards
# 
# """
# 

def calculate_flavor_hazards(formula_list):
    subhazard_dict = create_subhazard_dict(formula_list)
          
    accumulator = HazardAccumulator(subhazard_dict)
      
    hazard_dict = accumulator.get_hazard_dict()
    
    return hazard_dict
    
    
    
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
                
                
                """
                Here I attempt to correct any instances where a parsed category is not a possible
                category defined in our database.  If we parse category '2' and our database only
                contains '2A' and '2B', we just add an 'A' to the key (assume it is the most 
                hazardous option).  This would not work if the most hazardous alternative is not
                just suffixed with 'A'; in that case you would get another KeyError.
                """
                
                try:
                    hazard_dict[hazard + '_' + ingredient_hazard_category] += weight
                except KeyError: 
                    hazard_dict[hazard + '_' + ingredient_hazard_category + 'A'] += weight
        
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
            
    #logger.info(hazard_dict)
    return hazard_dict    
    
    
    
    
    
def import_GHS_ingredients_from_document(path_to_document):
    
    GHSIngredient.objects.all().delete()
    
    labels = xlrd.open_workbook(path_to_document)
    sheet = labels.sheets()[0]    

    ghs_list = []
    multiplephase_list = []
    
    for row in range(sheet.nrows):
        
        try:    
            g = import_row(sheet, row)
            if g == None: #this happens when it's not a cas number row
                pass
            else:
                ghs_list.append(g)
                
        except MultiplePhaseError as e:
            multiplephase_list.append(e.cas)
            
    if multiplephase_list:
        logger.warning("The following cas numbers contain multiple sets of hazards.  Alter the input document to have only one set of hazards per cas number.\n%s\n" % ', '.join(multiplephase_list))
        logger.warning("Ingredients were not imported.")
        
         
    else:
        for imported_ghsingredient in ghs_list:
            imported_ghsingredient.save()
        
        #create placeholder ingredient here
        p = GHSIngredient(cas = '00-00-00')
        p.name = 'Placeholder Ingredient (ignore this)'
        p.save()
        
        logger.info("Ingredients imported successfully.")


    
def import_row(sheet, row):
    
    cas_number = sheet.cell(row, 0).value
    
    #ignore rows that do not contain a cas number (table headers, footnote rows, etc)
    if cas_re.search(cas_number):
        
        reach = sheet.cell(row, 1).value
        name = sheet.cell(row, 2).value
        ghs_hazard_category = sheet.cell(row, 3).value
        ghs_change_indicators = sheet.cell(row, 4).value
        ghs_signal_words = sheet.cell(row, 5).value
        ghs_codes = sheet.cell(row, 6).value
        ghs_pictogram_codes = sheet.cell(row, 7).value
        synonyms = sheet.cell(row, 8).value
        
        
        g = GHSIngredient(cas=cas_number,
                          reach=reach,
                          name=name,
                          ghs_hazard_category=ghs_hazard_category,
                          ghs_change_indicators=ghs_change_indicators,
                          ghs_signal_words=ghs_signal_words,
                          ghs_codes=ghs_codes,
                          ghs_pictogram_codes=ghs_pictogram_codes,
                          synonyms=synonyms,)
        
        g.parse_ghs_hazard_category_cell()
        
        return g
    
    #else, None is returned



         


     

    
  
        



