import re


"""
Path to hazard document
"""
#path_to_labels = '/home/matta/label.xls'

path_to_labels = '/home/matta/label_changed.xls'



"""
Hazard information
"""


acute_toxicity_list = [('acute_hazard_oral', 'oral_ld50', 'oral_unknown', 2000),
                       ('acute_hazard_dermal', 'dermal_ld50', 'dermal_unknown', 2000),
                       ('acute_hazard_gases', 'gases_ld50', 'gases_unknown', 20000),
                       ('acute_hazard_vapors', 'vapors_ld50', 'vapors_unknown', 20.0),
                       ('acute_hazard_dusts_mists', 'dusts_mists_ld50', 'dusts_mists_unknown', 5.0)]


#non-acute hazards
hazard_list = ['skin_corrosion_hazard', 
               'eye_damage_hazard', 
               'germ_cell_mutagenicity_hazard', 
               'carcinogenicity_hazard', 
               'reproductive_hazard',
               'tost_single_hazard',
               'tost_repeat_hazard',
               'respiratory_hazard',
               'skin_sensitization_hazard']





"""
Regular expressions
"""

"""
CAS RE: this is used to only pick out rows that have information we want;
    excludes table headers, footnotes, document title, etc.
"""

cas_re = re.compile('\d*-\d*-\d*')

"""
These regular expressions are used to check if an ingredient in the document has multiple phases,
    where each phase has its own set of hazards. 
"""

gas_re = re.compile('gas')
solution_re = re.compile('solution')



