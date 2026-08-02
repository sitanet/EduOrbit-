"""
Phase 12.4.1 - HR Onboarding Wizard Navigation Framework Tests
Tests the navigation JavaScript implementation without browser
"""
import re
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from backend.apps.tenants.models import Tenant

User = get_user_model()


class OnboardingWizardNavigationTests(TestCase):
    """Test the onboarding wizard navigation framework"""
    
    def setUp(self):
        """Set up test user and tenant"""
        self.client = Client()
        self.tenant = Tenant.objects.create(
            name="Test School",
            is_active=True
        )
        self.user = User.objects.create_user(
            username='hradmin',
            email='hradmin@test.com',
            password='testpass123'
        )
        
    def test_wizard_page_loads(self):
        """Test that wizard page loads successfully"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'hr/admin/onboarding_wizard.html')
        
    def test_wizard_requires_authentication(self):
        """Test that unauthenticated users are redirected"""
        response = self.client.get('/hr/admin/onboarding/wizard/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.url)
        
    def test_javascript_variables_defined(self):
        """Test that all JavaScript variables are defined in template"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        # Check state variables
        self.assertIn('let currentStep = 1', content)
        self.assertIn('let draftId = null', content)
        self.assertIn('let totalSteps = 8', content)
        self.assertIn('let stepValidationState = {}', content)
        
    def test_javascript_functions_defined(self):
        """Test that all navigation functions are defined"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        # Check core navigation functions
        self.assertIn('function showStep(stepNumber)', content)
        self.assertIn('function goToStep(stepNumber)', content)
        self.assertIn('function nextStep()', content)
        self.assertIn('function prevStep()', content)
        
        # Check progress functions
        self.assertIn('function updateProgress()', content)
        self.assertIn('function updateNavigationButtons()', content)
        
        # Check validation
        self.assertIn('function validateStep(stepNumber)', content)
        
        # Check draft management
        self.assertIn('function saveDraftAuto()', content)
        self.assertIn('function saveDraftManual()', content)
        self.assertIn('function loadDraft()', content)
        self.assertIn('function clearDraft()', content)
        
        # Check Dojah functions (preserved)
        self.assertIn('function triggerNINVerify()', content)
        self.assertIn('function triggerBVNVerify()', content)
        
    def test_step1_form_fields_present(self):
        """Test that Step 1 form fields are present"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        # Required fields
        self.assertIn('id="firstNameInput"', content)
        self.assertIn('id="lastNameInput"', content)
        self.assertIn('id="dobInput"', content)
        self.assertIn('id="genderInput"', content)
        
        # Optional fields
        self.assertIn('id="middleNameInput"', content)
        self.assertIn('id="maritalStatusInput"', content)
        
        # KYC fields
        self.assertIn('id="ninInput"', content)
        self.assertIn('id="bvnInput"', content)
        
    def test_navigation_buttons_present(self):
        """Test that navigation buttons are present with correct IDs"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        self.assertIn('id="prevStepBtn"', content)
        self.assertIn('id="nextStepBtn"', content)
        self.assertIn('onclick="prevStep()"', content)
        self.assertIn('onclick="nextStep()"', content)
        
    def test_progress_bar_steps_present(self):
        """Test that progress bar has all 8 steps"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        # Check for onclick handlers for all steps
        for step_num in range(1, 9):
            self.assertIn(f'onclick="goToStep({step_num})"', content)
            
    def test_auto_save_initialization(self):
        """Test that auto-save is initialized on DOMContentLoaded"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        self.assertIn("document.addEventListener('DOMContentLoaded'", content)
        self.assertIn('setInterval(saveDraftAuto, 5000)', content)
        
    def test_keyboard_navigation_listeners(self):
        """Test that keyboard event listeners are registered"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        self.assertIn("document.addEventListener('keydown'", content)
        self.assertIn("e.key === 'Escape'", content)
        self.assertIn("e.key === 's'", content)
        self.assertIn("e.key === 'ArrowRight'", content)
        self.assertIn("e.key === 'ArrowLeft'", content)
        
    def test_beforeunload_handler(self):
        """Test that beforeunload handler is registered for draft save"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        self.assertIn("window.addEventListener('beforeunload'", content)
        self.assertIn('saveDraftAuto()', content)
        
    def test_console_log_initialization(self):
        """Test that initialization console log is present"""
        self.client.login(username='hradmin', password='testpass123')
        response = self.client.get('/hr/admin/onboarding/wizard/')
        content = response.content.decode('utf-8')
        
        self.assertIn("console.log('✓ EduOrbit HR Onboarding Wizard initialized (Phase 12.4.1)')", content)
