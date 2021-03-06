import re, copy
from xlrd import open_workbook

from django.db.models import Sum

from hazard_calculator.models import GHSIngredient, HazardAccumulator
from hazard_calculator.utils import acute_toxicity_list, hazard_list, cas_re, gas_re, solution_re
from hazard_calculator.mylogger import get_my_logger

from hazard_calculator.hazards import hazard_class_list, hazards_in_document_but_not_calculated




            
 

def calculate_flavor_hazards(formula_list):
    
    """
    The main function of this app; generates hazards given the formula of a flavor.
    
    1. In your main application, import hazard_calculator.models and hazard_calculator.tasks.
    2. Instantiate a list of FormulaLineItem objects with cas numbers and flavors corresponding
        to the formula of a flavor/product.
    3. Call this function with the FormulaLineItem list as an argument.
    4. Your output will be a dictionary containing the hazards of the product.
    
    """

    subhazard_dict = create_subhazard_dict(formula_list)
    accumulator = HazardAccumulator(subhazard_dict)
    hazard_dict = accumulator.get_hazard_dict()
    
    return hazard_dict



def get_hazard_list(formula_list):

    """
    This function is identical to calculate_flavor_hazards, but it is only meant for use in the
    GHS hazard_calculator view.  It returns a list rather than a dict (can control order), and
    rounds the ld50 values if there are any.
    """

    subhazard_dict = create_subhazard_dict(formula_list)
    accumulator = HazardAccumulator(subhazard_dict)
    hazard_list = accumulator.get_hazard_list()

    return hazard_list
    

def print_sds(hazard_dict):
    pass


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
                    
        for HazardClass in hazard_class_list:
            keys_to_add = HazardClass.get_subhazard_dict_keys()
            
            for key in keys_to_add:
                empty_subhazard_dict[key] = 0
                       
        return copy.copy(empty_subhazard_dict)
    
    
    
def create_subhazard_dict(formula_list):
       
    """
    Given the consolidated leaf weights of a flavor (in the form of FormulaLineItem objects), 
    create a dictionary which contains the total hazard accumulation for each subhazard.
    
    A 'subhazard' is a hazard + category combination; eg. 'skin_corrosion_hazard_1A'.
    
    Input: A list of leafweight objects, corresponding to ingredients and weights for a single flavor
    Output: A dictionary which contains the total 'accumulation' for each subhazard
    
    The output of this function is passed to the HazardAccumulator class, which uses these
    'accumulations' to calculate the final product's hazards.
    
    """
    
    total_weight = sum([fli.weight for fli in formula_list])
    
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

        for HazardClass in hazard_class_list:
            weights_to_add = HazardClass.add_weight_to_subhazard_dict(ingredient, weight, total_weight)
            
            for key in weights_to_add:
                hazard_dict[key] += weights_to_add[key]
        
    #get_my_logger().info(hazard_dict)    
    return hazard_dict    
    

def import_GHS_ingredients_from_document(path_to_document):
    """
    This function is used to import GHS Ingredient hazard information from a document.
    This function will delete ALL existing GHS Ingredient information in the database
    and replace it with the hazard information from the given document.
    
    There are two options for doing this:
        1. Call this function from a shell.
        2. Use the management command 'import_hazards' from the project directory
        
        In either case, pass the path to the hazard document as an argument.
    
    """
    
    
    labels = open_workbook(path_to_document)
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
        get_my_logger().warning("The following cas numbers contain multiple sets of hazards.  Alter the input document to have only one set of hazards per cas number.\n%s\n" % ', '.join(multiplephase_list))
        get_my_logger().warning("Ingredients were not imported.")
        
         
    else:
        
        GHSIngredient.objects.all().delete()
        
        for imported_ghsingredient in ghs_list:
            imported_ghsingredient.save()
        
        #create placeholder ingredient here
        p = GHSIngredient(cas = '00-00-00')
        p.name = 'Placeholder Ingredient (ignore this)'
        p.save()
        
        get_my_logger().info("Ingredients imported successfully.")


class MultiplePhaseError(Exception):
    def __init__(self, cas=None):
        self.cas = cas
    
    def __str__(self):
        if self.cas != None:
            return "Cas number: %s, MultiplePhaseError" % self.cas
    
    
def import_row(sheet, row):
    """
    This function is a helper function for the main import function 'import_GHS_ingredients_from_document'.
    It takes one of the rows of the document as an input, and returns the list of hazards that are specified in that row.
    """

    cas_number = sheet.cell(row, 0).value

    #ignore rows that do not contain a cas number (table headers, footnote rows, etc)
    if cas_re.search(cas_number):
        
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
        
        g = GHSIngredient(**g_dict)

        return g
    
    #else, None is returned





def parse_ghs_hazard_category_cell(cell_contents, cas_number):
    """
    This function actually parses the 'tokens' found in the document.
    
    It is given the actual string contents of a cell, and it returns a dictionary of hazards that 
    any of the tokens in the cell correspond to (if there are any).
    """


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
    

    hazard_list = []

    
    for HazardClass in hazard_class_list + hazards_in_document_but_not_calculated: 
        hazards_found = HazardClass.process_re(cell_contents)
        
        hazard_list += hazards_found #add the hazards found to the hazard_list
        
        for hazard, category in hazards_found:
            find_duplicate_hazards(hazard, category)
        
        
        
    
    '''
    Here I check if any hazards for one ingredient have been duplicated.  
    
    If so, delete all duplicates, and use the duplicate with the most hazardous category.
    '''
    
    if len(find_duplicate_hazards()) > 0: #do i even need this if statement
                
                
        for hazard, potential_categories in find_duplicate_hazards().iteritems():
            
            get_my_logger().info("Found duplicate hazards for CAS number %s" % cas_number) 
            get_my_logger().info("Hazard: %s, Potential Categories: %s" % (hazard, potential_categories))
            
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
            
            get_my_logger().info("Using most hazardous category: (%s: %s)\n" % (hazard, most_hazardous_category))
                
                        
    #return hazard_list
    
    hazard_dict = {}
    for hazard, category in hazard_list:
        hazard_dict[hazard] = category
    
    return hazard_dict
    
  
        



