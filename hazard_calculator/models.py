from django.db import models
from decimal import Decimal

from hazard_calculator.utils import acute_toxicity_list, hazard_list

#Since both Flavor and Ingredient models will have the same hazard fields, they can inherit them from this class
class HazardFields(models.Model):

    class Meta:
        abstract = True
    
    ACUTE_TOXICITY_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),)
    SKIN_CORROSION_CHOICES = (
        ('No','No'),
        ('1A','1A'),
        ('1B','1B'),
        ('1C','1C'),
        ('2','2'),
        ('3','3'),)
    EYE_DAMAGE_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('2A','2A'),
        ('2B','2B'),)
    RESPIRATORY_SENSITIZATION_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('1A','1A'),
        ('1B','1B'),)
    SKIN_SENSITIZATION_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('1A','1A'),
        ('1B','1B'),)
    GERM_CELL_MUTAGENICITY_CHOICES = (
        ('No','No'),
        ('1A','1A'),
        ('1B','1B'),
        ('2','2'),)
    CARCINOGENICTY_CHOICES = (
        ('No','No'),
        ('1A','1A'),
        ('1B','1B'),
        ('2','2'),)
    REPRODUCTIVE_CHOICES = (
        ('No','No'),
        ('1A','1A'),
        ('1B','1B'),
        ('2','2'),
        ('3','3'))
    TOST_SINGLE_EXPOSURE_CHOICES = (
         ('No','No'),
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('3-NE','3-NE'),
        ('3-RI','3-RI'),
        ('3-NE, 3-RI','3-NE, 3-RI'))
    TOST_REPEAT_EXPOSURE_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('2','2'), )
    ASPIRATION_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('2','2'),)
    ASPHYXIANT_CHOICES = (
        ('No','No'),
        ('Single Category','Single Category'),)
    ACUTE_AQUATIC_TOXICITY_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('2','2'),
        ('3','3'),
        )          
    CHRONIC_AQUATIC_TOXICITY_CHOICES = (
        ('No','No'),
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'))       
            
    
    
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
                ('No','No'),
                ('1','1'),
                ('2','2'),
                ('3','3'),
                ('4','4'),)
    FLAMMABLE_SOLID_CHOICES = (
                ('No','No'),
                ('1','1'),
                ('2','2'),)
    SELF_REACTIVE_CHOICES = (
                ('No','No'),
                ('Type A','Type A'),
                ('Type B','Type B'),
                ('Type C','Type C'),
                ('Type D','Type D'),
                ('Type E','Type E'),
                ('Type F','Type F'),
                ('Type G','Type G'),)
    EMIT_FLAMMABLE_GAS_CHOICES = (
                ('No','No'),
                ('1','1'),
                ('2','2'),
                ('3','3'),)
    OXIDIZING_LIQUID_CHOICES = (
                ('No','No'),
                ('1','1'),
                ('2','2'),
                ('3','3'),)
    OXIDIZING_SOLID_CHOICES = (
                ('No','No'),
                ('1','1'),
                ('2','2'),
                ('3','3'),)
    ORGANIC_PEROXIDE_CHOICES = (
                ('No','No'),
                ('Type A','Type A'),
                ('Type B','Type B'),
                ('Type C','Type C'),
                ('Type D','Type D'),
                ('Type E','Type E'),
                ('Type F','Type F'),
                ('Type G','Type G'),)
    CORROSIVE_TO_METAL_CHOICES = (
                ('No','No'),
                ('1','1'),)
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


class GHSIngredient(HazardFields):

#     class Meta:
#         abstract=True
        
    cas = models.CharField(
        max_length=15,
        blank=True)
    
    

class FormulaLineItem(models.Model):
    """
    This model pretty much represents a consolidated leaf weight of a flavor.  
    Each instance of this model will contain a cas number and a weight.
    A list of a FormulaLineItem objects will be passed into the main function of this app.
    
    NOTE: Should I add a reference to flavor?  
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


    
    
