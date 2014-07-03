import re



"""
Path to hazard document
"""
path_to_labels = '/home/matta/label.xls'



"""
Hazard information
"""


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






"""
Regular expressions
"""

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

tost_re = re.compile('STO[^-]*-[^SR]*([SR])E[^\d]*(\d(?:(?:-RI)?(?:-NE)?)?)')

"""
These are the re's for SCI, EDI, and CAR
These are simpler to parse since each re covers one hazard, only need to find the category
"""

sci_re = re.compile('SCI[^\d]*(\d[ABC]?)')
edi_re = re.compile('EDI[^\d]*(\d[ABC]?)')
car_re = re.compile('CAR[^\d]*(\d[ABC]?)')

