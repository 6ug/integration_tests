import attr

from navmazing import NavigateToAttribute, NavigateToSibling
from cfme.base.login import BaseLoggedInPage
from widgetastic.widget import View, ConditionalSwitchableView, Checkbox
from widgetastic_manageiq import RadioGroup, PaginationPane, Table
from widgetastic_patternfly import Text, TextInput, Button, BootstrapSelect
from cfme.modeling.base import BaseCollection, BaseEntity
from cfme.utils.appliance.implementations.ui import (navigator, CFMENavigateStep,
    can_skip_badness_test, navigate_to)
from cfme.utils.wait import wait_for


# Views


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
    title = Text(locator='.//h4[contains(@class,"modal-title")]')  # tested
    back_btn = Button('Back') # tested
    next_btn = Button('Next') # tested
    cancel_btn = Button('Cancel') # tested

    @View.nested
    class general(View):
        infra_map = BootstrapSelect('infrastructure_mapping') # tested
        name = TextInput(name='name') # tested
        description = TextInput(name='description') # tested

        # Todo: remove below
        select_vm = RadioGroup('.//div[6]/div[2]/div/div/div/div[2]/section/div/div/form/div[4]/div')

    @View.nested
    class vms(View):
        # This is table declaration, I am using it like
        # view = navigate_to(appliance.collections.migration.plan, 'Add')
        # view.vms.table.check_all()
        import_btn = Button('Import')
        importcsv = Button('Import CSV')

        table = Table('.//*[contains(@class, "container-fluid")]/table',
              column_widgets={"Select": Checkbox(locator=".//input")})

        # table = Table('.//*[contains(@class, "container-fluid")]/table', column_widgets={"Actions": })
        # paginator = PaginationPane()

    @View.nested
    class options(View):
        create_btn = Button('Create')  # tested
        run_migration = RadioGroup(
            './/div[6]/div[2]/div/div/div/div[2]/section/div/div/form/div/div')


    @View.nested
    class results(View):
        close_btn = Button('Close')  # tested
        msg = Text('.//div[6]/div[2]/div/div/div/div[2]/section/div/div/div/h3/text()')

    @property
    def is_displayed(self):
        return (self.title.text == 'Migration Plan Wizard')


# Collections Entities

@attr.s
class InfrastructureMapping(BaseEntity):
    """Class representing v2v infrastructure mappings"""
    name =att.

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
        view = navigate_to(self, 'Add')
        view.general.fill({
            'infra_map': infra_map,
            'name': name,
            'description': description
        })

        if csv_import:
            view.general.select_vm.select("Import a CSV file with a list of VMs to be migrated")
        view.next_btn.click()

        wait_for(lambda: view.vms.table.is_displayed,
                 timeout=60,
                 message='Wait for VMs view',
                 delay=2)

        for row in view.vms.table.rows():
            if row['VM Name1'].read() in vm_names:
                row['Select'].fill(True)

        # view.browser.element(".//div[6]/div[2]/div/div/div/div[2]/section/div/div/div/table/tbody/tr[1]/td[1]/td/input").click()
        view.next_btn.click()
        view.options.create_btn.click()
        view.results.close_btn.click()
        return self.instantiate(name)

        if start_migration:
            base_message = "Migration Plan: '{}' has been saved"


        else:
            view.options.run_migration.select("Start migration immediately")
            base_message = "Migration Plan: '{}' is in progress"


            # view.flash.assert_success_message(base_message.format(name))
            #
            # view.results.msg.(base_message.format(name))


# Navigations

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