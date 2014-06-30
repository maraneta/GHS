from django.db import models

# Create your models here.

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
        ('3','3'),)
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
        ('3','3'))          
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
    
    
# #Since both Flavor and Ingredient models will have the same hazard fields, they can inherit them from this class
# class GHSIngredient(HazardousChemical):
# 
#     #can't figure out a way to use this
#     #just save same data in two tables for now
# #     class Meta:
# #         managed = False
# #         db_table = 'Raw Materials'
# 
#     # This is the formula identifier. there may be multiple but only one active
# #     id = models.PositiveIntegerField("PIN", 
# #                                      db_column='ProductID',)
# #                                      #default=get_next_rawmaterialcode)
# 
# 
# 
#     rawmaterialcode = models.PositiveIntegerField(
#             primary_key=True,
#             db_column='RawMaterialCode',
#             blank=True,)    
#         

    
    
    
    
    
    
