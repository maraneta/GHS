from django.db import models
from decimal import Decimal

from hazard_calculator.utils import acute_toxicity_list, hazard_list, re_dict, ld50_re, eh_re, flammable_re, tost_re, sci_re, edi_re, car_re, gas_re, solution_re
from hazard_calculator.mylogger import logger


class MultiplePhaseError(Exception):
    def __init__(self, cas):
        self.cas = cas
    
    def __str__(self):
        return "Cas number: %s, MultiplePhaseError" % self.cas


class NoLeafWeightError(Exception):

    def __init__(self, num=None):
        self.num = num
            

    def __str__(self):
        if self.num:
            return "Flavor %s has no leaf weights; cannot calculate hazards (try recalculate_guts)" % self.num



class GHSIngredient(models.Model):
        
    def __unicode__(self):
        return u"%s: %s" % (self.cas, self.name)
        
    def parse_ghs_hazard_category_cell(self):
    
        cell_contents = self.ghs_hazard_category
        
        #currently, if both gas AND solution are found in the contents, error is raised
        #so if they delete one it'll work.
        #however, if in the future someone puts in something other than gas or solution 
        #the multiple sets won't be detected
        if gas_re.search(cell_contents) and solution_re.search(cell_contents): #should i do and?  or OR? 
            raise MultiplePhaseError(self.cas)
        
        
       
        
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
                             
        for re in [sci_re, edi_re, car_re]:
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
                
                logger.info("Found duplicate hazards for CAS number %s" % self.cas) 
                logger.info("Hazard: %s, Potential Categories: %s" % (hazard, potential_categories))
                
                lowest_index = 1000000
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
        
        for hazard, category in hazard_list:
            setattr(self, hazard, category)
        
        
    cas = models.CharField(
        max_length=15,
        blank=True)
    
    #raw data fields parsed straight from the document
    reach = models.CharField(max_length=15, blank=True)
    name = models.TextField(blank=True)
    ghs_hazard_category = models.TextField(blank=True)
    ghs_change_indicators = models.TextField(blank=True)
    ghs_signal_words = models.TextField(blank=True)
    ghs_codes = models.TextField(blank=True)
    ghs_pictogram_codes = models.TextField(blank=True)
    synonyms = models.TextField(blank=True)
     
    
    
    ACUTE_TOXICITY_CHOICES = (
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
        ('No','No'),)
    SKIN_CORROSION_CHOICES = (
        ('1A','1A'),
        ('1B','1B'),
        ('1C','1C'),
        ('2','2'),
        ('3','3'),
        ('No','No'),)
    EYE_DAMAGE_CHOICES = (
        ('1','1'),
        ('2A','2A'),
        ('2B','2B'),
        ('No','No'),)
    RESPIRATORY_SENSITIZATION_CHOICES = (
        ('1','1'),
        ('1A','1A'),
        ('1B','1B'),
        ('No','No'),)
    SKIN_SENSITIZATION_CHOICES = (
        ('1','1'),
        ('1A','1A'),
        ('1B','1B'),
        ('No','No'),)
    GERM_CELL_MUTAGENICITY_CHOICES = (
        ('1A','1A'),
        ('1B','1B'),
        ('2','2'),
        ('No','No'),)
    CARCINOGENICTY_CHOICES = (
        ('1A','1A'),
        ('1B','1B'),
        ('2','2'),
        ('No','No'),)
    REPRODUCTIVE_CHOICES = (
        ('1A','1A'),
        ('1B','1B'),
        ('2','2'),
        ('3','3'),
        ('No','No'),)
    TOST_SINGLE_EXPOSURE_CHOICES = (
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('3-NE','3-NE'),
        ('3-RI','3-RI'),
        ('3-NE, 3-RI','3-NE, 3-RI'),
        ('No','No'),)
    TOST_REPEAT_EXPOSURE_CHOICES = (
        ('1','1'),
        ('2','2'), 
        ('No','No'),)
    ASPIRATION_CHOICES = (
        ('1','1'),
        ('2','2'),
        ('No','No'),)
    ASPHYXIANT_CHOICES = (
        ('Single Category','Single Category'),
        ('No','No'),)
    ACUTE_AQUATIC_TOXICITY_CHOICES = (
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('No','No'),
        )          
    CHRONIC_AQUATIC_TOXICITY_CHOICES = (
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('No','No'),)       
            
    
    
    #for now, their default values are just above the threshold in which they would be counted for the formula
    oral_ld50 = models.DecimalField(decimal_places = 3, max_digits = 10, null=True)
    dermal_ld50 = models.DecimalField(decimal_places = 3, max_digits = 10, null=True)
    gases_ld50 = models.DecimalField(decimal_places = 3, max_digits = 10, null=True)
    vapors_ld50 = models.DecimalField(decimal_places = 3, max_digits = 10, null=True)
    dusts_mists_ld50 = models.DecimalField(decimal_places = 3, max_digits = 10, null=True)
    
    '''
    ALTER TABLE "access_integratedproduct" ADD COLUMN oral_ld50 numeric(10,3);
    ALTER TABLE "access_integratedproduct" ADD COLUMN dermal_ld50 numeric(10,3);
    ALTER TABLE "access_integratedproduct" ADD COLUMN gases_ld50 numeric(10,3);
    ALTER TABLE "access_integratedproduct" ADD COLUMN vapors_ld50 numeric(10,3);
    ALTER TABLE "access_integratedproduct" ADD COLUMN dusts_mists_ld50 numeric(10,3);
    
    ALTER TABLE "Raw Materials" ADD COLUMN oral_ld50 numeric(10,3);
    ALTER TABLE "Raw Materials" ADD COLUMN dermal_ld50 numeric(10,3);
    ALTER TABLE "Raw Materials" ADD COLUMN gases_ld50 numeric(10,3);
    ALTER TABLE "Raw Materials" ADD COLUMN vapors_ld50 numeric(10,3);
    ALTER TABLE "Raw Materials" ADD COLUMN dusts_mists_ld50 numeric(10,3);   
    '''
    
    #NOT IN PACKET
    acute_hazard_not_specified = models.CharField("Acute Toxicity - Type Not Specified", max_length=50,blank=True,
                               choices=ACUTE_TOXICITY_CHOICES)
    acute_hazard_oral = models.CharField("Acute Toxicity - Oral", max_length=50,blank=True,
                               choices=ACUTE_TOXICITY_CHOICES)
    acute_hazard_dermal = models.CharField("Acute Toxicity - Dermal", max_length=50,blank=True,
                               choices=ACUTE_TOXICITY_CHOICES)
    acute_hazard_gases = models.CharField("Acute Toxicity - Gases", max_length=50,blank=True,
                               choices=ACUTE_TOXICITY_CHOICES)
    acute_hazard_vapors = models.CharField("Acute Toxicity - Vapors", max_length=50,blank=True,
                               choices=ACUTE_TOXICITY_CHOICES)
    acute_hazard_dusts_mists = models.CharField("Acute Toxicity - Dust & Mists", max_length=50,blank=True,
                               choices=ACUTE_TOXICITY_CHOICES)
    skin_corrosion_hazard = models.CharField("Skin Corrosion/Irritation", max_length=50,blank=True,
                               choices=SKIN_CORROSION_CHOICES)
    eye_damage_hazard = models.CharField("Serious Eye Damage/Eye Irritation", max_length=50,blank=True,
                               choices=EYE_DAMAGE_CHOICES)
    respiratory_hazard = models.CharField("Respiratory or Skin Sensitization", max_length=50,blank=True,
                               choices=RESPIRATORY_SENSITIZATION_CHOICES)
    germ_cell_mutagenicity_hazard = models.CharField("Germ Cell Mutagenicity",max_length=50,blank=True,
                                choices=GERM_CELL_MUTAGENICITY_CHOICES)
    carcinogenicty_hazard = models.CharField("Carcinogenicty",max_length=50,blank=True,
                                choices=CARCINOGENICTY_CHOICES)
    reproductive_hazard = models.CharField("Reproductive Toxicity",max_length=50,blank=True,
                                choices=REPRODUCTIVE_CHOICES)
    skin_sensitization_hazard = models.CharField("Skin Sensitization", max_length=50, blank=True,
                                choices=SKIN_SENSITIZATION_CHOICES)
    tost_single_hazard = models.CharField("TOST Single Exposure",max_length=50,blank=True,
                                choices=TOST_SINGLE_EXPOSURE_CHOICES)
    tost_repeat_hazard = models.CharField("TOST Repeated Exposure",max_length=50,blank=True,
                                choices=TOST_REPEAT_EXPOSURE_CHOICES) 
    
    
    #NOT IN PACKET
    #CONGRESS SAID WE DONT NEED THESE! #record them in ingredients but don't calculate them for flavors
    acute_aquatic_toxicity_hazard = models.CharField("Acute Aquatic Toxicity", max_length=50, blank=True,
                                            choices=ACUTE_AQUATIC_TOXICITY_CHOICES)
    chronic_aquatic_toxicity_hazard = models.CharField("Chronic Aquatic Toxicity", max_length=50, blank=True,
                                              choices=CHRONIC_AQUATIC_TOXICITY_CHOICES)
     
    
    aspiration_hazard = models.CharField("Aspiration", max_length=50,blank=True,
                               choices=ASPIRATION_CHOICES)
    asphyxiation_hazard = models.CharField("Simple Asphyxiants", max_length=50,blank=True,
                               choices=ASPHYXIANT_CHOICES)

    FLAMMABLE_LIQUID_CHOICES = (
                ('1','1'),
                ('2','2'),
                ('3','3'),
                ('4','4'),
                ('No','No'),)
    FLAMMABLE_SOLID_CHOICES = (
                ('1','1'),
                ('2','2'),
                ('No','No'),)
    SELF_REACTIVE_CHOICES = (
                ('Type A','Type A'),
                ('Type B','Type B'),
                ('Type C','Type C'),
                ('Type D','Type D'),
                ('Type E','Type E'),
                ('Type F','Type F'),
                ('Type G','Type G'),
                ('No','No'),)
    EMIT_FLAMMABLE_GAS_CHOICES = (
                ('1','1'),
                ('2','2'),
                ('3','3'),
                ('No','No'),)
    OXIDIZING_LIQUID_CHOICES = (
                ('1','1'),
                ('2','2'),
                ('3','3'),
                ('No','No'),)
    OXIDIZING_SOLID_CHOICES = (
                ('1','1'),
                ('2','2'),
                ('3','3'),
                ('No','No'),)
    ORGANIC_PEROXIDE_CHOICES = (
                ('Type A','Type A'),
                ('Type B','Type B'),
                ('Type C','Type C'),
                ('Type D','Type D'),
                ('Type E','Type E'),
                ('Type F','Type F'),
                ('Type G','Type G'),
                ('No','No'),)
    CORROSIVE_TO_METAL_CHOICES = (
                ('1','1'),
                ('No','No'),)
    flammable_liquid_hazard = models.CharField("Flammable Liquids", max_length=50,blank=True,
                               choices=FLAMMABLE_LIQUID_CHOICES)
    flamamble_solid_hazard = models.CharField("Flammable Solids", max_length=50,blank=True,
                               choices=FLAMMABLE_SOLID_CHOICES)
    self_reactive_hazard = models.CharField("Self-Reactive Chemicals", max_length=50,blank=True,
                               choices=SELF_REACTIVE_CHOICES)
    emit_flammable_hazard = models.CharField("Chemicals, which in contact with water, emit flammable gas", max_length=50,blank=True,
                               choices=EMIT_FLAMMABLE_GAS_CHOICES)
    oxidizing_liquid_hazard = models.CharField("Oxidizing Liquids", max_length=50,blank=True,
                               choices=OXIDIZING_LIQUID_CHOICES)
    oxidizing_solid_hazard = models.CharField("Oxidizing Solids", max_length=50,blank=True,
                               choices=OXIDIZING_SOLID_CHOICES)
    organic_peroxide_hazard = models.CharField("Organic Peroxides", max_length=50,blank=True,
                               choices=ORGANIC_PEROXIDE_CHOICES)
    metal_corrosifve_hazard = models.CharField("Corrosive to Metals", max_length=50,blank=True,
                               choices=CORROSIVE_TO_METAL_CHOICES)    

class FormulaLineItem(models.Model):
    """
    This model pretty much represents a consolidated leaf weight of a flavor.  
    Each instance of this model will contain a cas number and a weight.
    A list of a FormulaLineItem objects will be passed into the main function of this app.
    """
    
    cas = models.CharField(max_length=15)
    weight = models.DecimalField(decimal_places=3, max_digits=7)
    




class HazardAccumulator():
    """
    Input: Subhazard dict
    Output: A HazardAccumulator object which calculates the final hazards based on the input dictionary
    
    To add another hazard:
    1. Make a function in the HazardAccumulator class below
    2. Add the hazard property to the hazard list above
    """    
    
    def __init__(self, subhazard_dict):
        #self.flavor = flavor
        
        #self.subhazard_dict = self.flavor.accumulate_hazards()
        self.subhazard_dict = subhazard_dict
                
        self.total_weight = self.subhazard_dict['total_weight']
        
        self.calculate_ld50s()
        
        if self.total_weight == 0:
            raise NoLeafWeightError()
        
    #Each hazard has a function below which describes the requirements/criteria the ingredients must meet in order for 
    #the flavor to be in a specific hazard category.  
    @property
    def skin_corrosion_hazard(self):
        skin_1 = self.subhazard_dict['skin_corrosion_hazard_1A'] + self.subhazard_dict['skin_corrosion_hazard_1B'] + self.subhazard_dict['skin_corrosion_hazard_1C']
        skin_2 = self.subhazard_dict['skin_corrosion_hazard_2']
        
        if skin_1/self.subhazard_dict['total_weight'] * 100 >= Decimal('5.0'):
            if self.subhazard_dict['skin_corrosion_hazard_1A'] >= 0:
                return '1A'
            elif self.subhazard_dict['skin_corrosion_hazard_1B'] >= 0:
                return '1B'
            else:
                return '1C'
        elif (10 * skin_1 + skin_2)/self.subhazard_dict['total_weight'] * 100 >= Decimal('10.0'):
            return '2'
        else:
            return 'No'

    @property    
    def eye_damage_hazard(self):
        skin_corrosion_1 = self.subhazard_dict['skin_corrosion_hazard_1A'] + self.subhazard_dict['skin_corrosion_hazard_1B'] + self.subhazard_dict['skin_corrosion_hazard_1C']
        eye_damage_1 = self.subhazard_dict['eye_damage_hazard_1']
        eye_damage_2 = self.subhazard_dict['eye_damage_hazard_2A'] + self.subhazard_dict['eye_damage_hazard_2B']
        
        if (skin_corrosion_1 + eye_damage_1)/self.subhazard_dict['total_weight'] * 100 >= Decimal('3.0'):
            #test = (skin_corrosion_1 + eye_damage_1)/self.subhazard_dict['total_weight'] * 100
            return '1'# % test
        
        elif (10*(skin_corrosion_1 + eye_damage_1) + eye_damage_2)/self.subhazard_dict['total_weight'] * 100 >= Decimal('10.0'):
            #if all the ingredients are in eye_damage_2, it is in category 2B
            if skin_corrosion_1 + eye_damage_1 + self.subhazard_dict['eye_damage_hazard_2A'] == 0:
                return '2B'
            else:
                return '2A' #if any ingredients are in 2A, it is  in category 2A
        
        else:
            return 'No'
        
    @property
    def germ_cell_mutagenicity_hazard(self):
        if (self.subhazard_dict['germ_cell_mutagenicity_hazard_1A'])/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            return '1A'
        elif (self.subhazard_dict['germ_cell_mutagenicity_hazard_1B'])/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            return '1B'
        elif (self.subhazard_dict['germ_cell_mutagenicity_hazard_2'])/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
            return '2'
        else:
            return 'No'
        
    @property
    def carcinogenicty_hazard(self):
        if (self.subhazard_dict['carcinogenicty_hazard_1A'] + self.subhazard_dict['carcinogenicty_hazard_1B'])/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            if self.subhazard_dict['carcinogenicty_hazard_1A'] >= 0:
                return '1A'
            else:
                return '1B'
        elif (self.subhazard_dict['carcinogenicty_hazard_2'])/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
            return '2'
        else:
            return 'No'
            
    @property
    def reproductive_hazard(self):
        reproductive_1 = self.subhazard_dict['reproductive_hazard_1A'] + self.subhazard_dict['reproductive_hazard_1B']
        
        if reproductive_1/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            if self.subhazard_dict['reproductive_hazard_1A'] >= 0:
                return '1A'
            else:
                return '1B'
            
        elif self.subhazard_dict['reproductive_hazard_2']/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            return '2'
        
        elif self.subhazard_dict['reproductive_hazard_3']/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            return '3'
        
        else:
            return 'No'
        
    @property
    def tost_single_hazard(self):
        
        tost3_ne = self.subhazard_dict['tost_single_hazard_3-NE, 3-RI'] + self.subhazard_dict['tost_single_hazard_3-NE']
        tost3_ri = self.subhazard_dict['tost_single_hazard_3-NE, 3-RI'] + self.subhazard_dict['tost_single_hazard_3-RI']
        
        if self.subhazard_dict['tost_single_hazard_1']/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
            return '1'
        elif self.subhazard_dict['tost_single_hazard_2']/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
            return '2'
        #had to change the statement below to account for categories '3-NI' and '3-RE'
        elif tost3_ne/self.subhazard_dict['total_weight'] * 100 >= Decimal('20.0') or tost3_ri/self.subhazard_dict['total_weight'] * 100 >= Decimal('20.0'):
            if tost3_ne/self.subhazard_dict['total_weight'] * 100 >= Decimal('20.0') and tost3_ri/self.subhazard_dict['total_weight'] * 100 >= Decimal('20.0'):
                return '3-NE, 3-RI'
            elif tost3_ne/self.subhazard_dict['total_weight'] * 100 >= Decimal('20.0'):
                return '3-NE'
            elif tost3_ri/self.subhazard_dict['total_weight'] * 100 >= Decimal('20.0'):
                return '3-RI'
        else:
            return 'No'
        
    @property
    def tost_repeat_hazard(self):
        if self.subhazard_dict['tost_repeat_hazard_1']/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
            return '1'
        elif self.subhazard_dict['tost_repeat_hazard_2']/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
            return '2'

        else:
            return 'No'

    @property
    def respiratory_hazard(self):
        respiratory_1 = self.subhazard_dict['respiratory_hazard_1A'] + self.subhazard_dict['respiratory_hazard_1B']
                
        if respiratory_1/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            if self.subhazard_dict['respiratory_hazard_1A']/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
                return '1A'
            elif self.subhazard_dict['respiratory_hazard_1B']/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
                return '1B'
            else:
                return '1'
        else:
            return 'No'
        
    @property
    def skin_sensitization_hazard(self):
        skin_1 = self.subhazard_dict['skin_sensitization_hazard_1A'] + self.subhazard_dict['skin_sensitization_hazard_1B']
                
        if skin_1/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
            if self.subhazard_dict['skin_sensitization_hazard_1A']/self.subhazard_dict['total_weight'] * 100 >= Decimal('0.1'):
                return '1A'
            elif self.subhazard_dict['skin_sensitization_hazard_1B']/self.subhazard_dict['total_weight'] * 100 >= Decimal('1.0'):
                return '1B'
            else:
                return '1'
        else:
            return 'No'
    
    @property
    def aspiration_hazard(self):
        if self.subhazard_dict['aspiration_hazard_1']/self.total_weight * 100 >= Decimal('10.0'):
            return '1'
    
    #the function 'calculate_ld50s' should be run before these
    #calculate_ld50s is now in 'init' so they're calculated when the instance is made
    @property
    def acute_hazard_oral(self):

        #oral_ld50 = self.flavor.oral_ld50
        oral_ld50 = self.subhazard_dict['oral_ld50']
        
        if 0 < oral_ld50 <= 5:
            return '1'
        elif 5 < oral_ld50 <= 50:
            return '2'
        elif 50 < oral_ld50 <= 300:
            return '3'
        elif 300 < oral_ld50 <= 2000:
            return '4'
        else:
            return 'No'
        
    @property
    def acute_hazard_dermal(self):
        
        #dermal_ld50 = self.flavor.dermal_ld50
        dermal_ld50 = self.subhazard_dict['dermal_ld50']
        
        #save_ld50(self.flavor, 'dermal_ld50', dermal_ld50)
        
        if 0 < dermal_ld50 <= 50:
            return '1'
        elif 50 < dermal_ld50 <= 200:
            return '2'
        elif 200 < dermal_ld50 <= 1000:
            return '3'
        elif 1000 < dermal_ld50 <= 2000:
            return '4'
        else:
            return 'No'
        
    @property
    def acute_hazard_gases(self):
                
        #gases_ld50 = self.flavor.gases_ld50
        gases_ld50 = self.subhazard_dict['gases_ld50']
        
        if 0 < gases_ld50 <= 100:
            return '1'
        elif 100 < gases_ld50 <= 500:
            return '2'
        elif 500 < gases_ld50 <= 2500:
            return '3'
        elif 2500 < gases_ld50 <= 20000:
            return '4'
        else:
            return 'No'
        
    @property
    def acute_hazard_vapors(self):
        
        #vapors_ld50 = self.flavor.vapors_ld50
        vapors_ld50 = self.subhazard_dict['vapors_ld50']
        
        if 0 < vapors_ld50 <= 0.5:
            return '1'
        elif 0.5 < vapors_ld50 <= 2.0:
            return '2'
        elif 2.0 < vapors_ld50 <= 10.0:
            return '3'
        elif 10.0 < vapors_ld50 <= 20.0:
            return '4'
        else:
            return 'No'
        
    @property
    def acute_hazard_dusts_mists(self):
        
        #dusts_mists_ld50 = self.flavor.dusts_mists_ld50
        dusts_mists_ld50 = self.subhazard_dict['dusts_mists_ld50']
        
        if 0 < dusts_mists_ld50 <= 0.05:
            return '1'
        elif 0.05 < dusts_mists_ld50 <= 0.5:
            return '2'
        elif 0.5 < dusts_mists_ld50 <= 1.0:
            return '3'
        elif 1.0 < dusts_mists_ld50 <= 5.0:
            return '4'
        else:
            return 'No'

    
    
    '''
    TODO?
    
    Regarding the 'except' statement below.  This currently handles two different exceptions.
    
    When none of the ingredients are hazardous, the final flavor_ld50 will equal total_weight / 0.
    I get a ZeroDivisionError and store the flavor_ld50 as None.
    
    When all of the ingredients have unknown ld50s, the final flavor_ld50 will equal 0 / 0.
    I get an InvalidOperation and store the flavor_ld50 as None.
    
    So currently, if flavor_ld50 is None, it could mean different things;
        1. None of the ingredients are hazardous (they are all above the threshold)
            -The flavor is definitely not hazardous, but ld50 cannot be calculated
            -Should I store it as a value just above the threshold?
        2. None of the ingredients are known (they all have NULL/None ld50s)
            -The ld50 of the flavor is UNKNOWN; this should probably stay None
            
    '''
    

    def calculate_ld50s(self):
        for acute_hazard, max_ld50 in acute_toxicity_list:
            
            unknown_weight_key = acute_hazard.split('acute_hazard_')[1] + '_unknown'
            
            try:
                ld50 = (self.total_weight - self.subhazard_dict[unknown_weight_key])/(self.subhazard_dict[acute_hazard])
            except: #ZeroDivisionError or InvalidOperation
                ld50 = None
            
            self.subhazard_dict[acute_hazard.split('acute_hazard_')[1] + '_ld50'] = ld50
    
#     def save_ld50s(self):
#         for acute_hazard, max_ld50 in acute_toxicity_list:
#             
#             ld50_property = acute_hazard.split('acute_hazard_')[1] + '_ld50'
#             
#             save_ld50(self.flavor, ld50_property, Decimal(str(self.subhazard_dict[ld50_property])))
    
#     def calculate_and_save_ld50s(self):
#         for acute_hazard, max_ld50 in acute_toxicity_list:
#         
#             try:
#                 ld50 = 1/(self.subhazard_dict[acute_hazard]/self.total_weight)
#             except ZeroDivisionError:
#                 ld50 = max_ld50 + 1
#             
#             save_ld50(self.flavor, acute_hazard.split('acute_hazard_')[1] + '_ld50', Decimal(str(ld50)))
        
    
    def get_hazard_dict(self):
        
        hazard_dict = {}
        
        for hazard_property in hazard_list:
            
            hazard_dict[hazard_property] = getattr(self, hazard_property)
            
        return hazard_dict
    '''
    Old functions that depended on knowing the flavor    
    
    def save_hazards(self):
        hazard_dict = self.get_hazard_dict()
        
        for hazard_name, category in hazard_dict.iteritems():
            setattr(self.flavor, hazard_name, category)
            
        self.flavor.save()
        
        self.save_ld50s()
        
    def recalculate_hazards(self):
        self.subhazard_dict = self.flavor.accumulate_hazards()
        self.calculate_ld50s()
    '''    
        
    def recalculate_hazards(self, formula_list):
        self.subhazard_dict = create_subhazard_dict(formula_list)
        self.calculate_ld50s()
        
        

def save_ld50(flavor, ld50_attr, ld50):
    setattr(flavor, ld50_attr, ld50)
    
    flavor.save()


    
    
