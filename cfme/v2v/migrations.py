import attr
import csv

from navmazing import NavigateToAttribute, NavigateToSibling
from widgetastic.widget import Checkbox, View
from widgetastic_manageiq import RadioGroup, Table, HiddenFileInput
from widgetastic_patternfly import Text, TextInput, Button, BootstrapSelect

from cfme.base.login import BaseLoggedInPage
from cfme.modeling.base import BaseCollection, BaseEntity
from cfme.utils.appliance.implementations.ui import (navigator, CFMENavigateStep, navigate_to)
from cfme.utils.wait import wait_for


class MigrationDashboardView(BaseLoggedInPage):
    create_infrastructure_mapping = Text(locator='(//a|//button)'
                                                 '[text()="Create Infrastructure Mapping"]')
    create_migration_plan = Text(locator='(//a|//button)[text()="Create Migration Plan"]')



    @property
    def is_displayed(self):
        return self.navigation.currently_selected == ['Compute', 'Migration']


class AddInfrastructureMappingView(View):
    title = Text(locator='.//h4[contains(@class,"modal-title")]')
    name = TextInput(name='name')
    description = TextInput(name='description')
    back_btn = Button('Back')
    next_btn = Button('Next')
    cancel_btn = Button('Cancel')

    @property
    def is_displayed(self):
        return (self.title.text == 'Infrastructure Mapping Wizard')


class AddMigrationPlanView(View):
    title = Text(locator='.//h4[contains(@class,"modal-title")]')
    back_btn = Button('Back')
    next_btn = Button('Next')
    cancel_btn = Button('Cancel')

    @View.nested
    class general(View):
        infra_map = BootstrapSelect('infrastructure_mapping')
        name = TextInput(name='name')
        description = TextInput(name='description')
        select_vm = RadioGroup('.//*[contains(@id,"vm_choice_radio")]')

    @View.nested
    class vms(View):
        import_btn = Button('Import')
        importcsv = Button('Import CSV')
        hidden_field = HiddenFileInput(locator='.//*[contains(@accept,".csv")]')
        table = Table('.//*[contains(@class, "container-fluid")]/table',
                      column_widgets={"Select": Checkbox(locator=".//input")})

    @View.nested
    class options(View):
        create_btn = Button('Create')
        run_migration = RadioGroup('.//*[contains(@id,"migration_plan_choice_radio")]')

    @View.nested
    class results(View):
        close_btn = Button('Close')
        msg = Text('.//*[contains(@id,"migration-plan-results-message")]')

    @property
    def is_displayed(self):
        return (self.title.text == 'Migration Plan Wizard')


@attr.s
class InfrastructureMapping(BaseEntity):
    """Class representing v2v infrastructure mappings"""
    category = 'migrationplan'
    string_name = 'Migration Plan'


@attr.s
class InfrastructureMappingCollection(BaseCollection):
    """Collection object for Migration mapping object"""
    ENTITY = InfrastructureMapping


@attr.s
class MigrationPlan(BaseEntity):
    """Class representing v2v infrastructure mappings"""
    name = attr.ib()


@attr.s
class MigrationPlanCollection(BaseCollection):
    """Collection object for Migration mapping object"""
    ENTITY = MigrationPlan

    def create(self, name, infra_map, vm_names, description=None, csv_import=False,
               start_migration=False):
        """Create new migration plan

        Args:
            name: (string) plan name
            description: (string) plan description
            infra_map: (object) infra map object name
            vm_names: (list) vm names
            csv_import: (bool) flag for importing vms
            start_migration: (bool) flag for start migration
        """
        view = navigate_to(self, 'Add')
        view.general.fill({
            'infra_map': infra_map,
            'name': name,
            'description': description
        })

        if csv_import:
            view.general.select_vm.select("Import a CSV file with a list of VMs to be migrated")
            view.next_btn.click()
            with open('v2v_vms.csv', 'w') as file:
                headers = ['Name', 'Provider']
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                for vm_name in vm_names:
                    #Todo: remove `Provider` hardcoding
                    writer.writerow({'Name': vm_name, 'Provider': 'vSphere 6 (nested)'})
            file.close()
            view.vms.hidden_field.fill('v2v_vms.csv')
        else:
            view.next_btn.click()
        wait_for(lambda: view.vms.table.is_displayed, timeout=60, message='Wait for VMs view',
                 delay=2)

        for row in view.vms.table.rows():
            if row['VM Name1'].read() in vm_names:
                row['Select'].fill(True)
        view.next_btn.click()

        if start_migration:
            view.options.run_migration.select("Start migration immediately")
        view.options.create_btn.click()
        wait_for(lambda: view.results.msg.is_displayed, timeout=60, message='Wait for Results view')

        if start_migration:
            base_flash = "Migration Plan: '{}' is in progress".format(name)
        else:
            base_flash = "Migration Plan: '{}' has been saved".format(name)
        assert view.results.msg.read() == base_flash

        view.results.close_btn.click()
        return self.instantiate(name)


@navigator.register(InfrastructureMappingCollection, 'All')
@navigator.register(MigrationPlanCollection, 'All')
class All(CFMENavigateStep):
    VIEW = MigrationDashboardView
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Compute', 'Migration')


@navigator.register(InfrastructureMappingCollection, 'Add')
class AddInfrastructureMapping(CFMENavigateStep):
    VIEW = AddInfrastructureMappingView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.create_infrastructure_mapping.click()


@navigator.register(MigrationPlanCollection, 'Add')
class AddMigrationPlan(CFMENavigateStep):
    VIEW = AddMigrationPlanView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.create_migration_plan.click()
