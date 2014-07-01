"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client, RequestFactory

from hazard_calculator.utils import *


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


#MIXTURE EXAMPLE 1 - from GHS packet   
class HazardTest1(TestCase):
    fixtures = ['testdata.json']
    
    def setUp(self):
        self.count = Flavor.objects.count()
        self.flavor = Flavor.objects.get(number=1000)
        self.accumulator = HazardAccumulator(self.flavor)
        self.subhazard_dict = self.accumulator.subhazard_dict
        self.hazard_dict = self.accumulator.get_hazard_dict()
    
    #ensure that there is only one flavor in the testdata fixture    
    def test_count(self): 
        self.assertEqual(self.count, 1)
        

    #testing various properties to ensure the hazardaccumulator is working correctly  
    def test_ld50s(self): 
        self.assertEqual(round(self.subhazard_dict['dermal_ld50']), 24286)
        
    def test_eye_category(self):
        self.assertEqual(self.hazard_dict['eye_damage_hazard'], '2A')
        
class GHSRegularExpressionTest(TestCase):
    
    """
    In this test I will be using various test cases found in the hazard document
    and ensure that the regular expressions I wrote can capture the correct information.
    """
    
    fixtures = ['GHSIngredients.json']
    
    def setUp(self):
        pass
    
    def test_ld50_re(self):
        #ld50_re = re.compile('AT([IOD])[^\d]*(\d)[^(\d]*\([^\d]*([\d]+)[^)]*')
        
        teststring1 = 'ATD 4(1100),ATI 2(1,v),ATO 3(100),CAR 2,EDI 2A,FL 4,SCI 2,STO-SE 3-RI'
        
        
        self.assertEqual(ld50_re.findall(teststring1), [('D', '4', '1100'), ('I', '2', '1'), ('O', '3', '100')])
        