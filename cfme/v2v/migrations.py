import attr

from navmazing import NavigateToAttribute, NavigateToSibling
from cfme.base.login import BaseLoggedInPage

from cfme.utils.pretty import Pretty
from widgetastic.widget import View
from widgetastic_patternfly import Text, BootstrapSelect, Input
from widgetastic_manageiq import RadioGroup, CheckboxSelect, Button
from cfme.modeling.base import BaseCollection, BaseEntity
from cfme.utils.appliance.implementations.ui import navigator, CFMENavigateStep


# I have to add four classes with working widgets

# class MigrationPlanWizardView(View):
#     infra_mapping = BootstrapSelect('infrastructure_mapping')
#     name = Input(name='name')
#     description = Input(name='description')
#     vms_imports = RadioGroup('//input[@name="vm_choice_radio"]') # not tested
#
#     next_btn = Button(title='Next')
#     cancel_btn = Button(title='Cancel')
#     back_btn = Button(title='Back')
#


# views

class MigrationDashboardView(BaseLoggedInPage):
    create_infrastructure_mapping = Text(locator='(//a|//button)'
        '[text()="Create Infrastructure Mapping"]')
    create_migration_plan = Text(locator='(//a|//button)[text()="Create Migration Plan"]')

    # we have to remove below, I just added for testing

    infra_mapping = BootstrapSelect('infrastructure_mapping')
    name = Input(name='name')
    description = Input(name='description')
    vms_imports = RadioGroup('//input[@name="vm_choice_radio"]') # not working

    next_btn = Button(title='Next')
    cancel_btn = Button(title='Cancel')
    back_btn = Button(title='Back')


    @property
    def is_displayed(self):
        return self.navigation.currently_selected == ['Compute', 'Migration']


# Collections Entities


@attr.s
class InfrastructureMapping(BaseEntity):
    """Class representing v2v infrastructure mappings"""
    category = 'infrastructuremapping'
    string_name = 'Infrastructure Mapping'


@attr.s
class InfrastructureMappingCollection(BaseCollection):
    """Collection object for Migration mapping object"""
    ENTITY = InfrastructureMapping


@attr.s
class MigrationPlan(BaseEntity):
    """Class representing v2v infrastructure mappings"""
    category = 'migrationplan'
    string_name = 'Migration Plan'


@attr.s
class MigrationPlanCollection(BaseCollection):
    """Collection object for Migration mapping object"""
    ENTITY = MigrationPlan


@navigator.register(InfrastructureMappingCollection, 'All')
@navigator.register(MigrationPlanCollection, 'All')
class All(CFMENavigateStep):
    VIEW = MigrationDashboardView
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Migration')

    def resetter(self):
        """Reset the view"""
        self.view.browser.refresh()


@navigator.register(InfrastructureMappingCollection, 'Add')
class InfrastructureMappingAdd(CFMENavigateStep):
    VIEW = MigrationDashboardView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.create_infrastructure_mapping.click()

# working, just use like, view = navigate_to(appliance.collection.migration_plan, 'Add')
@navigator.register(MigrationPlanCollection, 'Add')
class MigrationPlanAdd(CFMENavigateStep):
    VIEW = MigrationDashboardView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.create_migration_plan.click()
