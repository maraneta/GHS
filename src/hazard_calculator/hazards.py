import re

from hazard_calculator.models import GHSIngredient

 




'''
BASE HAZARD FUNCTIONS
'''

def basehazard_process_re(cell_contents, hazard_field, re):
    
    hazards_found = []
    
    if re.search(cell_contents):
        re_results = re.findall(cell_contents)
        
        for category in re_results: #if there's more than one, then there's a duplicate
            hazards_found.append((hazard_field, category))
            
    return hazards_found



def basehazard_add_weight_to_subhazard_dict(ingredient, weight, hazard):
    """
    Here I attempt to correct any instances where a parsed category is not a possible
    category defined in our database.  If we parse category '2' and our database only
    contains '2A' and '2B', we just add an 'A' to the key (assume it is the most 
    hazardous option).  This would not work if the most hazardous alternative is not
    just suffixed with 'A'; in that case you would get another KeyError.
    """
    weights_to_add = {}
    
    ingredient_hazard_category = getattr(ingredient, hazard)
    
    if ingredient_hazard_category != '':
        try:
            weights_to_add[hazard + '_' + ingredient_hazard_category] = weight
        except KeyError: 
            weights_to_add[hazard + '_' + ingredient_hazard_category + 'A'] = weight        

    return weights_to_add



def basehazard_get_subhazard_dict_keys(hazard_field):
    keys_to_add = []
    
    for category in GHSIngredient._meta.get_field(hazard_field).choices:
        if category[0] != 'No':     #category[0] and category[1] are always the same
            keys_to_add.append(hazard_field + '_' + category[0])
    
    return keys_to_add


'''
BASE ACUTE TOXICITY HAZARD FUNCTIONS
'''


def acutehazard_process_re(cell_contents, hazard_field, ld50_field, re):
    hazards_found = []
    
    if re.search(cell_contents):
        re_results = re.findall(cell_contents)
        
        for category, ld50 in re_results: #if there's more than one, then there's a duplicate
            hazards_found.append((hazard_field, category))
            hazards_found.append((ld50_field, ld50))
            
    return hazards_found    


def acutehazard_add_weight_to_subhazard_dict(ingredient, weight, total_weight, acute_hazard, ld50_property, 
                                 unknown_weight_key, max_ld50):
    
    weights_to_add = {}
    
    ingredient_ld50 = getattr(ingredient, ld50_property)
    
    if ingredient_ld50 == None:
        #for each ingredient, only add its weight to the unknown key for each acute hazard 
        # if that ingredients concentration is >10%    
        if (weight/total_weight) * 100 > 10: 
            weights_to_add[unknown_weight_key] = weight #don't modify dict just return values
    elif ingredient_ld50 < max_ld50:
        weights_to_add[acute_hazard] = weight/getattr(ingredient, ld50_property)

    return weights_to_add


'''
ACUTE HAZARDS
'''


class AcuteToxicityOral():
    #put hazard specific parameters in these classes and pass them into the base functions
    human_readable_field = 'Acute Toxicity Hazard: Oral'
    human_readable_ld50 = 'Acute Toxicity Oral LD50'

    hazard_field = 'acute_hazard_oral'
    ld50_field = 'oral_ld50'
    unknown_weight_key = 'oral_unknown'
    max_ld50 = 2000
    
    acute_oral_re = re.compile('ATO[^\d]*(\d)[^(\d]*\([^\d]*([\d]+)[^)]*')

    @staticmethod
    def process_re(cell_contents):
        return acutehazard_process_re(cell_contents, AcuteToxicityOral.hazard_field, 
                                                AcuteToxicityOral.ld50_field, AcuteToxicityOral.acute_oral_re)
                    
    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return acutehazard_add_weight_to_subhazard_dict(ingredient, weight, total_weight,
                                                                         AcuteToxicityOral.hazard_field,
                                                                         AcuteToxicityOral.ld50_field,
                                                                         AcuteToxicityOral.unknown_weight_key,
                                                                         AcuteToxicityOral.max_ld50)
 
    @staticmethod
    def get_subhazard_dict_keys():
        return AcuteToxicityOral.hazard_field, AcuteToxicityOral.unknown_weight_key
 
class AcuteToxicityDermal():
    human_readable_field = 'Acute Toxicity Hazard: Dermal'
    human_readable_ld50 = 'Acute Toxicity Dermal LD50'

    hazard_field = 'acute_hazard_dermal'
    ld50_field = 'dermal_ld50'
    unknown_weight_key = 'dermal_unknown'
    max_ld50 = 2000
    
    acute_dermal_re = re.compile('ATD[^\d]*(\d)[^(\d]*\([^\d]*([\d]+)[^)]*')

    @staticmethod
    def process_re(cell_contents):
        return acutehazard_process_re(cell_contents, AcuteToxicityDermal.hazard_field, 
                                                AcuteToxicityDermal.ld50_field, AcuteToxicityDermal.acute_dermal_re)
        
    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return acutehazard_add_weight_to_subhazard_dict(ingredient, weight, total_weight,
                                                                         AcuteToxicityDermal.hazard_field,
                                                                         AcuteToxicityDermal.ld50_field,
                                                                         AcuteToxicityDermal.unknown_weight_key,
                                                                         AcuteToxicityDermal.max_ld50)
 
    @staticmethod
    def get_subhazard_dict_keys():
        return AcuteToxicityDermal.hazard_field, AcuteToxicityDermal.unknown_weight_key
                       
class AcuteToxicityInhalation():
    human_readable_field = 'Acute Toxicity Hazard: Gases/Inhalation'
    human_readable_ld50 = 'Acute Toxicity Gas/Inhalation LD50'

    hazard_field = 'acute_hazard_gases'
    ld50_field = 'gases_ld50'
    unknown_weight_key = 'gases_unknown'
    max_ld50 = 20000
    
    acute_inhalation_re = re.compile('ATI[^\d]*(\d)[^(\d]*\([^\d]*([\d]+)[^)]*')

    @staticmethod
    def process_re(cell_contents):
        return acutehazard_process_re(cell_contents, AcuteToxicityInhalation.hazard_field, 
                                                AcuteToxicityInhalation.ld50_field, AcuteToxicityInhalation.acute_inhalation_re)
    
    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return acutehazard_add_weight_to_subhazard_dict(ingredient, weight, total_weight,
                                                                         AcuteToxicityInhalation.hazard_field,
                                                                         AcuteToxicityInhalation.ld50_field,
                                                                         AcuteToxicityInhalation.unknown_weight_key,
                                                                         AcuteToxicityInhalation.max_ld50)
 
    @staticmethod
    def get_subhazard_dict_keys():
        return AcuteToxicityInhalation.hazard_field, AcuteToxicityInhalation.unknown_weight_key
 
 
 
'''
NON ACUTE HAZARDS
''' 
 
class SkinCorrosionHazard():

    human_readable_field = 'Skin Corrosion Hazard'
    hazard_field = 'skin_corrosion_hazard'
    sci_re = re.compile('SCI[^\d]*(\d[ABC]?)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, SkinCorrosionHazard.hazard_field, SkinCorrosionHazard.sci_re)
                
    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return basehazard_add_weight_to_subhazard_dict(ingredient, weight, SkinCorrosionHazard.hazard_field)
 
    @staticmethod
    def get_subhazard_dict_keys():
        return basehazard_get_subhazard_dict_keys(SkinCorrosionHazard.hazard_field)
 
class EyeDamageHazard():

    human_readable_field = 'Eye Damage Hazard'
    hazard_field = 'eye_damage_hazard'
    edi_re = re.compile('EDI[^\d]*(\d[ABC]?)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, EyeDamageHazard.hazard_field, EyeDamageHazard.edi_re)

    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return basehazard_add_weight_to_subhazard_dict(ingredient, weight, EyeDamageHazard.hazard_field)
   
    @staticmethod
    def get_subhazard_dict_keys():
        return basehazard_get_subhazard_dict_keys(EyeDamageHazard.hazard_field)
    
class CarcinogenicityHazard():

    human_readable_field = 'Carcinogenicity Hazard'
    hazard_field = 'carcinogenicity_hazard'
    car_re = re.compile('CAR[^\d]*(\d[ABC]?)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, CarcinogenicityHazard.hazard_field, CarcinogenicityHazard.car_re)

    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return basehazard_add_weight_to_subhazard_dict(ingredient, weight, CarcinogenicityHazard.hazard_field)
    
    @staticmethod
    def get_subhazard_dict_keys():
        return basehazard_get_subhazard_dict_keys(CarcinogenicityHazard.hazard_field)
  
class TostSingleHazard():

    human_readable_field = 'Target Organ System Toxicity: Single Exposure Hazard'
    hazard_field = 'tost_single_hazard'
    tost_single_re = re.compile('STO[^-]*-[^S]*SE[^\d]*(\d(?:(?:-RI)?(?:-NE)?)?)')
    
    @staticmethod
    def process_re(cell_contents):
        
        re = TostSingleHazard.tost_single_re
        hazard_field = TostSingleHazard.hazard_field
        
        hazards_found = []
        
        if re.search(cell_contents):
            re_results = re.findall(cell_contents)
            
            #print re_results
            
            for category in re_results:
                if category in ['3', '3-NE', '3-RI'] and ('3-RI' and '3-NE') in re_results:
                    if ('tost_single_hazard', '3-NE, 3-RI') not in hazards_found:
                        hazards_found.append((hazard_field, '3-NE, 3-RI'))
                    
                else:
                    hazards_found.append((hazard_field, category))

        return hazards_found

    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return basehazard_add_weight_to_subhazard_dict(ingredient, weight, TostSingleHazard.hazard_field)
         
    @staticmethod
    def get_subhazard_dict_keys():
        return basehazard_get_subhazard_dict_keys(TostSingleHazard.hazard_field)
         

class TostRepeatHazard():

    human_readable_field = 'Target Organ System Toxicity: Repeated Exposure Hazard'
    hazard_field = 'tost_repeat_hazard'
    tost_repeat_re = re.compile('STO[^-]*-[^R]*RE[^\d]*(\d)')

    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, TostRepeatHazard.hazard_field, TostRepeatHazard.tost_repeat_re)

    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return basehazard_add_weight_to_subhazard_dict(ingredient, weight, TostRepeatHazard.hazard_field)
     
    @staticmethod
    def get_subhazard_dict_keys():
        return basehazard_get_subhazard_dict_keys(TostRepeatHazard.hazard_field)
 

class SkinSensitizationHazard():

    human_readable_field = 'Skin Sensitization Hazard'
    hazard_field = 'skin_sensitization_hazard'
    ss_re = re.compile('SS[^\d]*(\d[ABC]?)')
    
        
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, SkinSensitizationHazard.hazard_field, SkinSensitizationHazard.ss_re)

    @staticmethod
    def add_weight_to_subhazard_dict(ingredient, weight, total_weight):
        return basehazard_add_weight_to_subhazard_dict(ingredient, weight, SkinSensitizationHazard.hazard_field)
     
    @staticmethod
    def get_subhazard_dict_keys():
        return basehazard_get_subhazard_dict_keys(SkinSensitizationHazard.hazard_field)
 




'''
The hazards below can be found on some ingredients in the document.  They will be saved to the GHSIngredient objects
during import.  HOWEVER, they are NOT calculated for final products, and do not need any subhazard_dict related functions.
'''


class ChronicAquaticHazard():
    human_readable_field = 'Chronic Aquatic Toxicity Hazard'
    hazard_field = 'chronic_aquatic_toxicity_hazard'
    ca_re = re.compile('EH C(\d)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, ChronicAquaticHazard.hazard_field, ChronicAquaticHazard.ca_re)    


class AcuteAquaticHazard():
    human_readable_field = 'Acute Aquatic Toxicity Hazard'
    hazard_field = 'acute_aquatic_toxicity_hazard'
    aa_re = re.compile('EH A(\d)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, AcuteAquaticHazard.hazard_field, AcuteAquaticHazard.aa_re)    


class FlammableSolidHazard():
    human_readable_field = 'Flammable Solid Hazard'
    hazard_field = 'flammable_solid_hazard'
    fs_re = re.compile('FS[^\d]*(\d)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, FlammableSolidHazard.hazard_field, FlammableSolidHazard.fs_re)    

class FlammableLiquidHazard():
    human_readable_field = 'Flammable Liquid Hazard'
    hazard_field = 'flammable_liquid_hazard'
    fl_re = re.compile('FL[^\d]*(\d)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, FlammableLiquidHazard.hazard_field, FlammableLiquidHazard.fl_re)    

class FlammableGasHazard():
    human_readable_field = 'Flammable Gas Hazard'
    hazard_field = 'emit_flammable_hazard'
    fg_re = re.compile('FG[^\d]*(\d)')
    
    @staticmethod
    def process_re(cell_contents):
        return basehazard_process_re(cell_contents, FlammableGasHazard.hazard_field, FlammableGasHazard.fg_re)    


#  #these hazards do not appear in the hazard document
#  class AcuteToxicityVapors():
#      pass
#      
#  class AcuteToxicityDustsMists():
#      pass
#  
#  class AcuteToxicityGases():
#      pass
#  
#  class GermCellMutagenicityHazard():
#      pass
#  
#  class ReproductiveHazard():
#      pass
#  
#  class RespiratoryHazard():
#      pass

hazard_class_list = [AcuteToxicityOral, AcuteToxicityDermal, AcuteToxicityInhalation, SkinCorrosionHazard,
                     EyeDamageHazard, CarcinogenicityHazard, SkinSensitizationHazard, TostRepeatHazard, TostSingleHazard]


hazards_in_document_but_not_calculated = [ChronicAquaticHazard, AcuteAquaticHazard, FlammableSolidHazard,
                                          FlammableLiquidHazard, FlammableGasHazard]