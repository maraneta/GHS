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


"""
HAZARD RE: this is used to find, split, and capture all hazard tokens in the input document
"""

hazard_re = re.compile('([^(,\n]*(?:(?:\([^)]*\))*[^,(\n]*)*)[,\n]?')


"""
LD50 RE: covers ATI, ATO, and ATD; returns category and ld50
examples: ATI 5(300), ATO 3(300), ATI 4(3350 ppm), 

will match '#anything ATI #anything (digit) #anything ( #anything digits #anything )
"""

ld50_re = re.compile('AT([IOD])[^\d]*(\d)[^(\d]*\([^\d]*([\d]+)[^)]*')

inhalation_ld50_re = re.compile('ATI[^\d]*(\d)[^(\d]*\([^\d]*([\d]+)[^)]*')
        
"""        
EH RE: covers EH A and EH C; returns chronic/acute and category

there must be ONE SPACE between 'EH' and either 'A' or 'C' and no space between A/C and the category
"""

eh_re = re.compile('EH ([AC])(\d)')

ca_re = re.compile('EH C(\d)')


"""
flammable_re: covers FL, FS, and FG

will find the first digit after either fl, fg, or fs
will not match if it does not contain fl fg or fs, or if there are no digits afterward
"""
flammable_re = re.compile('F([LGS])[^\d]*(\d)')

fs_re = re.compile('FS[^\d]*(\d)')

"""
tost_re: covers STO - SE and STO - RE

will find the first digit after SE or SR
will match '#ANYTHING STO #ANYTHING - #ANYTHING (S or R) E #ANYTHING digit

"""

tost_re = re.compile('STO[^-]*-[^SR]*([SR])E[^\d]*(\d(?:(?:-RI)?(?:-NE)?)?)')

tost_single_re = re.compile('STO[^-]*-[^S]*([S])E[^\d]*(\d(?:(?:-RI)?(?:-NE)?)?)')
tost_repeat_re = re.compile('STO[^-]*-[^R]*([R])E[^\d]*(\d)')

"""
These are the re's for SCI, EDI, CAR, and SS
These are simpler to parse since each re covers one hazard, only need to find the category
"""

sci_re = re.compile('SCI[^\d]*(\d[ABC]?)')
edi_re = re.compile('EDI[^\d]*(\d[ABC]?)')
car_re = re.compile('CAR[^\d]*(\d[ABC]?)')
ss_re = re.compile('SS[^\d]*(\d[ABC]?)')



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
                car_re: 'carcinogenicity_hazard',
                ss_re: 'skin_sensitization_hazard',
                
                
          }

