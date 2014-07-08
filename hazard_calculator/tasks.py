from hazard_calculator.models import *
from hazard_calculator.utils import *

#from hazard_calculator import utils
#use utils.blah

#from hazard_calculator import models as hazard_models etc

#acute_toxicity_list, hazard_list, path_to_labels, hazard_re, ld50_re, eh_re, flammable_re, tost_re, sci_re, edi_re, car_re

import os, sys, errno, logging
import xlrd  # @UnresolvedImport
import re


"""Setting up logging"""

LOG_PATH = '/var/log/django/'
try:
    os.makedirs(LOG_PATH)
except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir(LOG_PATH):
        pass
    else:
        raise
LOG_FILENAME = '/var/log/django/ghs.log'

LOG_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"

logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO, format=LOG_FILE_FORMAT, datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger()
#logger.setFormatter(LOG_FILE_FORMAT)



#add a log handler that prints to stdout

STDOUT_LOG_FORMAT = logging.Formatter('%(message)s') 

log_handler = logging.StreamHandler(sys.stdout)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(STDOUT_LOG_FORMAT)

logger.addHandler(log_handler)




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
    
    



def save_ingredient_hazards(document_path):
    
    """
    This function uses the parse_hazards function and
    saves the resulting data into the GHSIngredient model.
    """    
    
    ingredient_hazard_dict = parse_hazards(document_path)
    
    if ingredient_hazard_dict == None:
        logger.warning("Ingredients will not be imported.  Fix the errors above.\n")
    
    else:
    
        for cas in ingredient_hazard_dict:
            
            '''This is where the placeholder ingredient is created.'''
            if cas == '00-00-00':
                g = GHSIngredient(cas=cas)
    
            
            elif ingredient_hazard_dict[cas]: #if the hazard dictionary for the corresponding cas number is NOT empty:
                g = GHSIngredient()
                g.cas = cas
                
                ingredient_hazards = ingredient_hazard_dict[cas]
                
                for hazard in ingredient_hazards:
                    setattr(g, hazard, ingredient_hazards[hazard])
                    
            g.save()
                              
            logger.info("Ingredients and hazards imported successfully.\n")

def parse_hazards(path):
    
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
    
    
    labels = xlrd.open_workbook(path)
    sheet = labels.sheets()[0]
    
    complete_hazard_dict = {}
    
    multiplephase_list = []
    duplicatehazard_dict = {}
    
    
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
                
        except MultiplePhaseError as e:
            multiplephase_list.append(cas_number)
        
        except DuplicateHazardError as e:
#             print "The ingredient with cas number %s has the following duplicate hazards: " % cas_number
#             for hazard in e.duplicate_hazards:
#                 print hazard
            for hazard in e.duplicate_hazards:
                if cas_number in duplicatehazard_dict:
                    duplicatehazard_dict[cas_number].append(hazard)
                else:
                    duplicatehazard_dict[cas_number] = [hazard]
                    
    print "\n"
    if multiplephase_list:
        logger.warning("The following cas numbers contain multiple sets of hazards.  Alter the input document to have only one set of hazards per cas number.\n%s\n" % ', '.join(multiplephase_list)) 

        
    if duplicatehazard_dict:
        
        duplicate_rows = []
        for cas in duplicatehazard_dict:
            duplicate_rows.append("%s: %s" % (cas, ', '.join(duplicatehazard_dict[cas])))
        
        logger.warning("The following ingredients have duplicate hazards.\n%s\n" % ('\n'.join(duplicate_rows)))
   
    
    """Only return the hazard dictionary if nothing has to be fixed in the document."""
    if not multiplephase_list and not duplicatehazard_dict:
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

class MultiplePhaseError(Exception):
    def __str__(self):
        return "Foo"
         

def parse_token(token):
    
    if gas_re.search(token) or solution_re.search(token):
        raise MultiplePhaseError()
    
    
    
    
    '''
    I use this function to keep track of which hazards appear twice in the same cell.
    
    I exploit the fact that default arguments are only evaluated one time - when the function is defined.
    Therefore, function keeps the state of the lists and appends to the same lists in each successive call.
    '''
    
    def find_duplicate_hazards(hazard_field=None, unique_list=[], duplicate_list=[]):
        
        if hazard_field == None:
            pass
        
        elif hazard_field not in unique_list:
            unique_list.append(hazard_field)
        
        elif hazard_field in unique_list and hazard_field not in duplicate_list:
            duplicate_list.append(hazard_field)
            
        return duplicate_list
    
    
    
    
    
    
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
    '''
    
    

        

            
    
    

        
    
    
    
#     for re in re_dict:
#         if re.search(token):
#             re_results = re.findall(token)
# 
#     
#             if re == ld50_re:
    
    
    for re in [ld50_re]:
        if re.search(token):
            re_results = re.findall(token)
             
            for hazard, category, ld50 in re_results:
                for hazard_letter in re_dict[re]:
                    if hazard == hazard_letter:
                        
                        
                        '''
                        Added a bunch of extra lines trying to name variables that might
                        not be clear... Should I do this for all of them?  Or not do it at all?
                        '''
                        
                        #hazard field is the actual field name of the hazard 
                        #eg. 'acute_hazard_oral', 'acute_hazard_dermal'
                        hazard_field = re_dict[re][hazard_letter][0]
                        
                        #ld50 field is the ld50 field name; eg. 'oral_ld50'
                        ld50_field = re_dict[re][hazard_letter][1]
                        
                        hazard_list.append((hazard_field, category))
                        hazard_list.append((ld50_field, ld50))            
                        
                        find_duplicate_hazards(hazard_field)
        
        
        #elif re == tost_re:
        
    for re in [tost_re]:
        if re.search(token):
            re_results = re.findall(token)
            
            """
            The Target Organ Systemic Toxicity (TOST) hazards contain a special case that has to be 
            treated differently.  The single exposure hazard can have two different options when it is
            category 3; 3-RI and 3-NE.  The difference here is that one chemical can be either 3-RI,
            3-NE, or BOTH.  If it is both, both STO-SE 3-NE and STO-SE 3-RI will appear in the document.
            
            When an ingredient is both 3-NE and 3-RI, it conflicts with the duplicate hazard checker 
            I implemented.  In this case the STO-SE hazard will appear twice, but instead of raising 
            a duplicate hazard error, I want the STO-SE hazard to be saved with category '3-NE, 3-RI'.            

            ----------------------------------------------------------------------------------------
            
            High-level pseudocode!
            
            IF the hazard is 'S' AND the category is ('3' or '3-NE' or '3-RI'), then we need to do 
            something differently.
            
            ELSE, we do the same thing as we do for the rest of the hazards.
            
            -----------------------------------------------------------------------------------------
            
            Ann example:
            
            Let's say we're on the tost_re and re_results yields [('R', '2'), ('S', '3-NE'), ('S', '3-RI')]
            
            Proceeding... 
            -First the loop finds ('R', '2').
            -Not 'S' or '3 something' so it jumps to the 'else' statement.
            -('tost_repeat_hazard', '2') is correctly added to the hazard_list
            -'tost_repeat_hazard' is added to the unique list
            
            -The loop then reaches ('S', '3-NE').
            -The hazard is 'S' and the category is '3-something'.
            -Now we check to see if there are any duplicates of ('S', '3-NE') in the re_results list;
                -We check for exact duplicates because if we only check for the same hazard, we would
                    get a duplicate error when both ('S', '3-NE') and ('S', '3-RI') are in re_results,
                    and we do NOT want that
            -There are no duplicates, so we check if both ('S', '3-NE') and ('S', '3-RI') are in 
                re_results.  If True, then add ('tost_single_hazard', '3-NE, 3-RI') to the hazard_list
                because it has not already been appended.
            -Add 'tost_single_hazard' to the unique_list, so if any other instances of 'tost_single_hazard'
                appear, a duplicate hazard error will be raised.
                
            -The loop reaches ('S', '3-RI').
            -The hazard is 'S' and the category is '3-something'.
            -Once again, check for exact duplicates.  There are none.
                -If there were exact duplicates, duplicate_hazard_field would be called for every duplicate
                    that has category '3-something', which means it would be called at least twice.
                    By calling duplicate_hazard_field twice with 'tost_single_hazard' as a parameter,
                    it adds 'tost_single_hazard' to the duplicate_list.
            -Check if both ('S', '3-NE') and ('S', '3-RI') are in re_results.  They are, but since 
                ('tost_single_hazard', '3-NE, 3-RI') has already been added to the hazard_list,
                do nothing.
    
            There is probably a more efficient/less complex way to do this =] 
            
            """

        
            for hazard, category in re_results:
                #print hazard, category
                
                if hazard == 'S' and category in ['3', '3-NE', '3-RI']: 
                    hazard_field = re_dict[re][hazard] # = tost_single_hazard
                    
                    
                    #we need this in the case of ['STO-SE 3-RI, STO-SE 3-RI']
                    if len(re_results) != len(set(re_results)): #if true, there are duplicates
                        find_duplicate_hazards(hazard_field) #this will be run at least twice
                        #print '1'
                    
                    if (('S', '3-RI') and ('S', '3-NE')) in re_results:
                        if ('tost_single_hazard', '3-NE, 3-RI') not in hazard_list:
                            hazard_list.append(('tost_single_hazard', '3-NE, 3-RI'))
                            find_duplicate_hazards(hazard_field) #this can only happen once
                            
                    else:
                        hazard_list.append((hazard_field, category))
                        find_duplicate_hazards(hazard_field) #this can only happen once
                        
                else: #normal case
                    hazard_list.append((re_dict[re][hazard], category))
                    
                    find_duplicate_hazards(re_dict[re][hazard])                            

                    #print '2'
                            
        #elif re == (eh_re or flammable_re):
    for re in [eh_re, flammable_re]:
        if re.search(token):
            re_results = re.findall(token)            
             
            for hazard, category in re_results:
                for hazard_letter in re_dict[re]:
                    if hazard == hazard_letter:
                        hazard_list.append((re_dict[re][hazard_letter], category))
                        
                        find_duplicate_hazards(re_dict[re][hazard_letter])
                         
        #elif re == (sci_re or edi_re or car_re):
    
    for re in [sci_re, edi_re, car_re]:
        if re.search(token):
            re_results = re.findall(token)
             
            for category in re_results: #there should only be one unless the same hazard is repeated
                hazard_list.append((re_dict[re], category))
                
                find_duplicate_hazards(re_dict[re])
                        
    '''
    Here I check if any hazards for one ingredient have been duplicated.  
    
    If so, raise an exception which is caught by parse_hazards.  Then add the cas number to a list of
    invalid rows.
    '''
    
    if len(find_duplicate_hazards()) > 0:
        raise DuplicateHazardError(find_duplicate_hazards())
     
    return hazard_list 
     

    
  
        



