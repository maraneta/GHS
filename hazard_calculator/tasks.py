import xlrd  # @UnresolvedImport
import re, copy

from django.db.models import Sum

from hazard_calculator.models import GHSIngredient, HazardAccumulator
from hazard_calculator.utils import acute_toxicity_list, hazard_list, cas_re, \
  re_dict, ld50_re, eh_re, flammable_re, tost_re, sci_re, edi_re, car_re, ss_re, gas_re, solution_re
from hazard_calculator.mylogger import logger




            
 

def calculate_flavor_hazards(formula_list):
    
    """
    The main function of this app; generates hazards given the formula of a flavor.
    
    input: a list of formula line item objects
    output: dictionary containing list of flavors and their hazards
    
    """
    
    
    subhazard_dict = create_subhazard_dict(formula_list)
          
    accumulator = HazardAccumulator(subhazard_dict)
      
    hazard_dict = accumulator.get_hazard_dict()
    
    return hazard_dict
    
    



empty_subhazard_dict = {}   

def get_empty_subhazard_dict():
    
    """
    This functions returns a copy of the empty subhazard dict.  The first time this function
    executes, it will iterate through the hazard lists, create the dict, and return a copy of it.  
    Once the dict is cached in memory, the function just returns a copy without having to create it again.
    """    
    
    if empty_subhazard_dict != {}:
        return copy.copy(empty_subhazard_dict)
    
    else:
        #The KEYS in this dictionary are in the format 'subhazard_category' (eg. 'skin_corrosion_hazard_1A')
        #The VALUES are the accumulation of ingredient weights that correspond to each hazard
        #empty_subhazard_dict = {}
        
        
        #initialize all unknown_weights for acute hazards to zero
        #there will be an unknown weight for each hazard; eg. hazard_dict['oral_unknown'], ...

        for acute_hazard, ld50_property, unknown_weight_key, max_ld50 in acute_toxicity_list:
            empty_subhazard_dict[unknown_weight_key] = 0
            empty_subhazard_dict[acute_hazard] = 0 #sigma(weight/ld50)
        
        #initialize all the values to zero
        for hazard in hazard_list:  
            for category in GHSIngredient._meta.get_field(hazard).choices:
                if category[0] != 'No':     #category[0] and category[1] are always the same
                    empty_subhazard_dict[hazard + '_' + category[0]] = 0
                       
        return copy.copy(empty_subhazard_dict)
    
    
    
def create_subhazard_dict(formula_list):

#     #use a django aggregate function (Sum) to find the total weight of the formula_list queryset
#     total_weight = formula_list.aggregate(Sum('weight'))
   
   
    total_weight = sum([fli.weight for fli in formula_list])
    
    """
    Given the consolidated leaf weights of a flavor (in the form of FormulaLineItem objects), 
    create a dictionary which contains the total hazard accumulation for each subhazard.
    
    A 'subhazard' is a hazard + category combination; eg. 'skin_corrosion_hazard_1A'.
    
    Input: A list of leafweight objects, corresponding to ingredients and weights for a single flavor
    Output: A dictionary which contains the total 'accumulation' for each subhazard
    
    """
    
    #create a copy of an empty subhazard dict
    #this allows us to avoid the process of creating the empty dict every time
    hazard_dict = get_empty_subhazard_dict()
            
    hazard_dict['total_weight'] = total_weight
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
    
           
    #for each base ingredient in the flavor, find any hazards it has and add its weight to each of those
    for fli in formula_list:
        
        ingredient = GHSIngredient.objects.get(cas = fli.cas)
            
        weight = fli.weight

                
        #for each NON-acute hazard that the ingredient has, add the ingredient's weight to the correct subhazard key 
        for hazard in hazard_list:
            ingredient_hazard_category = getattr(ingredient, hazard)
            
            if ingredient_hazard_category != '':
                add_weight_to_subhazard_dict(hazard_dict, hazard, ingredient_hazard_category, weight)
        
        
        
        #here I add weight/ld50 for each of the acute hazards
        for acute_hazard, ld50_property, unknown_weight_key, max_ld50 in acute_toxicity_list:
            
            
            
            ingredient_ld50 = getattr(ingredient, ld50_property)
            
            if ingredient_ld50 == None:
                #for each ingredient, only add its weight to the unknown key for each acute hazard 
                # if that ingredients concentration is >10%    
                if (weight/hazard_dict['total_weight']) * 100 > 10: 
                    hazard_dict[unknown_weight_key] += weight
            elif ingredient_ld50 < max_ld50:
                hazard_dict[acute_hazard] += weight/getattr(ingredient, ld50_property)
                
        
    #logger.info(hazard_dict)
    return hazard_dict    
    

def add_weight_to_subhazard_dict(hazard_dict, hazard, ingredient_hazard_category, weight):
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


class MultiplePhaseError(Exception):
    def __init__(self, cas=None):
        self.cas = cas
    
    def __str__(self):
        if self.cas != None:
            return "Cas number: %s, MultiplePhaseError" % self.cas
    
    
def import_row(sheet, row):

    cas_number = sheet.cell(row, 0).value

    #ignore rows that do not contain a cas number (table headers, footnote rows, etc)
    if cas_re.search(cas_number):
        
        g_dict = parse_row(sheet, row, cas_number)
        g = GHSIngredient(**g_dict)

        return g
    
    #else, None is returned





def parse_row(sheet, row, cas_number):
            
    g_dict = {}
    
    g_dict['cas'] = cas_number
    g_dict['reach'] = sheet.cell(row, 1).value
    g_dict['name'] = sheet.cell(row, 2).value
    g_dict['ghs_hazard_category'] = sheet.cell(row, 3).value
    g_dict['ghs_change_indicators'] = sheet.cell(row, 4).value
    g_dict['ghs_signal_words'] = sheet.cell(row, 5).value
    g_dict['ghs_codes'] = sheet.cell(row, 6).value
    g_dict['ghs_pictogram_codes'] = sheet.cell(row, 7).value
    g_dict['synonyms'] = sheet.cell(row, 8).value


    ingredient_hazard_dict = parse_ghs_hazard_category_cell(g_dict['ghs_hazard_category'], cas_number)
    g_dict.update(ingredient_hazard_dict)
    
    return g_dict


     
def parse_ghs_hazard_category_cell(cell_contents, cas_number):

    cell_contents = cell_contents
    
    #currently, if both gas AND solution are found in the contents, error is raised
    #so if they delete one it'll work.
    #however, if in the future someone puts in something other than gas or solution 
    #the multiple sets won't be detected
    if gas_re.search(cell_contents) and solution_re.search(cell_contents): #should i do and?  or OR? 
        raise MultiplePhaseError(cas_number)
    
    
   
    
    '''
    In the case of duplicate hazards, we just want to save the more severe category and 
    ignore the lesser category.
    '''
    
    def find_duplicate_hazards(hazard_field = None, category = None, hazard_dict = {}, duplicate_dict = {}):
        
        '''
        just keep track of hazard_dict, where key = hazard_field, value = [category_list]
        
        any key that has a category_list with more than one category represents a duplicate hazard
        
        when the function is called, return all duplicate hazards (duplicate_dict)

        '''
        
        
        #if no parameter is passed, just return duplicate list
        if hazard_field == None:
            pass
        
        else:
            #if the field is not in the hazard_list, append a tuple
            if hazard_field not in hazard_dict:
                hazard_dict[hazard_field] = [category]
            
            #if the field IS in the hazard_list, append to the category list
            else:
                hazard_dict[hazard_field].append(category)
                
        #return duplicate hazards and potential categories
        for key, value in hazard_dict.iteritems():
            if len(value) >= 2:
                duplicate_dict[key] = value

            
        return duplicate_dict
    
    
    
    """
    input: cell_contents 
    output: save hazards to ghsingredient
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
        -re.findall(cell_contents) returns [('O', '3', '100')]
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
    


    
    for re in [ld50_re]:
        if re.search(cell_contents):
            re_results = re.findall(cell_contents)
             
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
                        
                        find_duplicate_hazards(hazard_field, category)
        
        
    for re in [tost_re]:
        if re.search(cell_contents):
            re_results = re.findall(cell_contents)
            
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
                        find_duplicate_hazards(hazard_field, category) #this will be run at least twice
                        #print '1'
                    
                    if (('S', '3-RI') and ('S', '3-NE')) in re_results:
                        if ('tost_single_hazard', '3-NE, 3-RI') not in hazard_list:
                            hazard_list.append(('tost_single_hazard', '3-NE, 3-RI'))
                            find_duplicate_hazards(hazard_field, category) #this can only happen once
                            
                    else:
                        hazard_list.append((hazard_field, category))
                        find_duplicate_hazards(hazard_field, category) #this can only happen once
                        
                else: #normal case
                    hazard_list.append((re_dict[re][hazard], category))
                    
                    find_duplicate_hazards(re_dict[re][hazard], category)                            

                    #print '2'
                            
    for re in [eh_re, flammable_re]:
        if re.search(cell_contents):
            re_results = re.findall(cell_contents)            
             
            for hazard, category in re_results:
                for hazard_letter in re_dict[re]:
                    if hazard == hazard_letter:
                        hazard_list.append((re_dict[re][hazard_letter], category))
                        
                        find_duplicate_hazards(re_dict[re][hazard_letter], category)
                         
    for re in [sci_re, edi_re, car_re, ss_re]:
        if re.search(cell_contents):
            re_results = re.findall(cell_contents)
             
            for category in re_results: #there should only be one unless the same hazard is repeated
                hazard_list.append((re_dict[re], category))
                
                find_duplicate_hazards(re_dict[re], category)
                        
    '''
    Here I check if any hazards for one ingredient have been duplicated.  
    
    If so, delete all duplicates, and use the duplicate with the most hazardous category.
    '''
    
    if len(find_duplicate_hazards()) > 0: #do i even need this if statement
                
                
        for hazard, potential_categories in find_duplicate_hazards().iteritems():
            
            logger.info("Found duplicate hazards for CAS number %s" % cas_number) 
            logger.info("Hazard: %s, Potential Categories: %s" % (hazard, potential_categories))
            
            lowest_index = 1000000 #any number > 7 will work
            for category in potential_categories:
                
                index = GHSIngredient._meta.get_field(hazard).choices.index((category, category))
                if index < lowest_index:
                    lowest_index = index
                    
                #find any instances of the hazard in the hazard_list and delete them
                try:
                    hazard_list.remove((hazard, category))
                except:
                    pass
            
            most_hazardous_category = GHSIngredient._meta.get_field(hazard).choices[lowest_index][0]
            
            #append the hazard with its most hazardous category 
            hazard_list.append((hazard, most_hazardous_category))
            
            logger.info("Using most hazardous category: (%s: %s)\n" % (hazard, most_hazardous_category))
                
                        
    #return hazard_list
    
    hazard_dict = {}
    for hazard, category in hazard_list:
        hazard_dict[hazard] = category
    
    return hazard_dict
    
  
        



