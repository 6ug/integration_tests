import time

from navmazing import NavigateToAttribute, NavigateToSibling
from types import NoneType
from widgetastic.widget import Text, Checkbox, View
from widgetastic_patternfly import Button, Input, BootstrapSelect, CandidateNotFound, Tab

from cfme.common import WidgetasticTaggable, TagPageView
from cfme.common.vm_views import BasicProvisionFormView
from cfme.utils.appliance import Navigatable
from cfme.utils.appliance.implementations.ui import navigator, CFMENavigateStep, navigate_to
from cfme.utils.pretty import Pretty
from cfme.utils.update import Updateable
from cfme.utils.wait import wait_for
from widgetastic.utils import VersionPick
from widgetastic_manageiq import ManageIQTree, FonticonPicker, PotentiallyInvisibleTab
from . import ServicesCatalogView


class BasicInfoForm(ServicesCatalogView):
    title = Text('#explorer_title_text')

    name = Input(name='name')
    description = Input(name='description')
    display = Checkbox(name='display')
    select_catalog = BootstrapSelect('catalog_id')
    select_dialog = BootstrapSelect('dialog_id')
    select_orch_template = BootstrapSelect('template_id')
    select_provider = BootstrapSelect('manager_id')
    select_config_template = BootstrapSelect('template_id')
    field_entry_point = Input(name='fqname')
    retirement_entry_point = Input(name='retire_fqname')
    select_resource = BootstrapSelect('resource_id')
    tree = ManageIQTree('automate_treebox')
    cancel_button = Button('Cancel')


class BasicInfoTab(Tab, BasicInfoForm):
    TAB_NAME = 'Basic Info'


class RequestInfoTab(Tab, BasicProvisionFormView):
    TAB_NAME = 'Request Info'


class ButtonGroupForm(ServicesCatalogView):
    title = Text('#explorer_title_text')

    btn_group_text = Input(name='name')
    btn_group_hvr_text = Input(name='description')
    btn_image = VersionPick({
        '5.8': BootstrapSelect('button_image'),
        '5.9': FonticonPicker('button_icon')})


class ButtonFormCommon(ServicesCatalogView):
    title = Text('#explorer_title_text')

    class options(PotentiallyInvisibleTab):  # noqa

        btn_text = Input(name='name')
        btn_hvr_text = Input(name='description')
        btn_image = VersionPick({
            '5.8': BootstrapSelect('button_image'),
            '5.9': FonticonPicker('button_icon')})
        select_dialog = BootstrapSelect('dialog_id')

    class advanced(PotentiallyInvisibleTab):  # noqa

        system_process = BootstrapSelect('instance_name')
        message = Input(name='object_message')
        request = Input(name='object_request')


class AllCatalogItemView(ServicesCatalogView):
    title = Text("#explorer_title_text")

    @property
    def is_displayed(self):
        return self.in_explorer and self.title.text == 'All Service Catalog Items' and \
            self.catalog_items.is_opened and \
            self.catalog_items.tree.currently_selected == ["All Catalog Items"]


class DetailsCatalogItemView(ServicesCatalogView):
    title = Text("#explorer_title_text")

    @property
    def is_displayed(self):
        return self.in_explorer and self.catalog_items.is_opened and \
            self.title.text == 'Service Catalog Item "{}"'.format(self.context['object'].name)


class CatalogForm(BasicInfoForm):
    select_item_type = BootstrapSelect('st_prov_type', can_hide_on_select=True)

    @property
    def is_displayed(self):
        return self.in_explorer and self.catalog_items.is_opened and \
            self.title.text == "Adding a new Service Catalog Item"

    def before_filling(self):
        item_type = self.context['object'].provider_type or \
            self.context['object'].item_type or 'Generic'
        self.select_item_type.select_by_visible_text(item_type)
        self.flush_widget_cache()


class AddCatalogItemView(CatalogForm):
    apply_button = Button('Apply')
    add_button = Button("Add")
    request_info = View.nested(RequestInfoTab)

    @property
    def is_displayed(self):
        return self.in_explorer and self.catalog_items.is_opened and \
            self.title.text == "Adding a new Service Catalog Item"


class EditCatalogItemView(BasicInfoForm):
    save_button = Button('Save')
    reset_button = Button('Reset')

    @property
    def is_displayed(self):
        return (
            self.in_explorer and
            self.catalog_items.is_opened and
            self.title.text == 'Editing Service Catalog Item "{}"'
                .format(self.context['object'].name)
        )

    def after_fill(self, was_change):
        # TODO: This is a workaround (Jira RHCFQE-5429)
        if was_change:
            wait_for(lambda: not self.save_button.disabled, timeout='10s', delay=0.2)


class AddButtonGroupView(ButtonGroupForm):

    add_button = Button("Add")

    @property
    def is_displayed(self):
        return self.in_explorer and self.catalog_items.is_opened and \
            self.title.text == "Adding a new Button Group"


class AddButtonView(ButtonFormCommon):

    add_button = Button("Add")
    cancel = Button('Cancel')

    @property
    def is_displayed(self):
        return self.in_explorer and self.catalog_items.is_opened and \
            self.title.text == "Adding a new Button"


class CatalogBundleFormView(ServicesCatalogView):
    title = Text('#explorer_title_text')
    basic_info = View.nested(BasicInfoTab)

    @View.nested
    class resources(Tab):  # noqa
        select_resource = BootstrapSelect('resource_id')


class AddCatalogBundleView(CatalogBundleFormView):
    cancel_button = Button('Cancel')
    apply_button = Button('Apply')
    add_button = Button("Add")

    @property
    def is_displayed(self):
        return self.in_explorer and self.catalog_items.is_opened and \
            self.title.text == "Adding a new Catalog Bundle"


class EditCatalogBundleView(CatalogBundleFormView):
    save_button = Button('Save')
    reset_button = Button('Reset')

    @property
    def is_displayed(self):
        return self.in_explorer and self.catalog_items.is_opened and \
            self.title.text == 'Editing Catalog Bundle "{}"'.format(self.obj.name)


class CatalogItem(Updateable, Pretty, Navigatable, WidgetasticTaggable):

    def __init__(self, name=None, description=None, item_type=None,
                 vm_name=None, display_in=False, catalog=None, dialog=None,
                 catalog_name=None, orch_template=None, provider_type=None,
                 provider=None, config_template=None, prov_data=None,
                 domain="ManageIQ (Locked)", appliance=None):
        Navigatable.__init__(self, appliance=appliance)
        self.name = name
        self.description = description
        self.item_type = item_type
        self.vm_name = vm_name
        self.display_in = display_in
        self.catalog = catalog
        self.dialog = dialog
        self.catalog_name = catalog_name
        self.orch_template = orch_template
        self.provider = provider
        self.config_template = config_template
        self.provider_type = provider_type
        self.provisioning_data = prov_data
        self.domain = domain

    TAB_MAPPING = {
        # Options
        'btn_text': 'options',
        'btn_hvr_text': 'options',
        'select_dialog': 'options',
        'btn_image': 'options',
        # Advanced
        'system_process': 'advanced',
        'request': 'advanced',
    }

    @classmethod
    def _categorize_fill_dict(cls, d):
        """This method uses ``TAB_MAPPING`` to categorize fields to appropriate tabs.
        For DRY purposes.
        """
        result = {}
        for key, value in d.items():
            try:
                placement = cls.TAB_MAPPING[key]
            except KeyError:
                raise KeyError('Unknown key name {} for Button'.format(key))
            if placement not in result:
                result[placement] = {}
            result[placement][key] = value
        return result

    def create(self):
        view = navigate_to(self, 'Add')
        # Need to provide the (optional) provider name to the form, not the object
        provider_formvalue = None
        if self.item_type == 'Orchestration':
            provider_formvalue = self.provider.name
        elif self.item_type == 'AnsibleTower':
            provider_formvalue = self.provider
        # For tests where orchestration template is None
        view.before_filling()
        view.fill({'name': self.name,
                   'description': self.description,
                   'display': self.display_in,
                   'select_catalog': self.catalog.name,
                   'select_dialog': self.dialog,
                   'select_orch_template': self.orch_template.template_name
                   if self.orch_template else None,
                   'select_provider': provider_formvalue,
                   'select_config_template': self.config_template})

        if view.field_entry_point.value == "":
            view.fill({'field_entry_point': 'a'})
            view.tree.click_path(
                "Datastore", self.domain, "Service", "Provisioning",
                "StateMachines", "ServiceProvision_Template", "CatalogItemInitialization")
            view.apply_button.click()
        if self.appliance.version >= "5.7" and self.item_type == "AnsibleTower":
            view.fill({'retirement_entry_point': 'b'})
            view.tree.click_path(
                "Datastore", self.domain, "Service", "Retirement",
                "StateMachines", "ServiceRetirement", "Generic")
            view.apply_button.click()
        if (self.catalog_name is not None and
                self.provisioning_data is not None and
                not isinstance(self.provider, NoneType)):
            view.request_info.catalog.catalog_name.row(
                name=self.catalog_name, provider=self.provider.name).click()
            view.request_info.fill(self.provisioning_data)
        view.add_button.click()
        view = self.create_view(AllCatalogItemView)
        view.flash.assert_success_message('Service Catalog Item "{}" was added'.format(self.name))
        assert view.is_displayed

    def update(self, updates):
        view = navigate_to(self, 'Edit')
        changed = view.fill(updates)
        if changed:
            view.save_button.click()
        else:
            view.cancel_button.click()
        view = self.create_view(DetailsCatalogItemView, override=updates)
        assert view.is_displayed
        if changed:
            view.flash.assert_message(
                'Service Catalog Item "{}" was saved'.format(updates.get('name', self.name)))
        else:
            view.flash.assert_message(
                'Edit of Catalog Item"{}" was cancelled by the user'.format(self.name))

    def delete(self):
        view = navigate_to(self, "Details")
        view.configuration.item_select('Remove Catalog Item', handle_alert=True)
        view = self.create_view(AllCatalogItemView)
        assert view.is_displayed
        view.flash.assert_success_message('The selected Catalog Item was deleted')

    def add_button_group(self):
        view = navigate_to(self, 'AddButtonGroup')
        if self.appliance.version >= '5.9':
            image = 'fa-user'
            flash_msg = 'Button Group "descr" was added'
        else:
            image = 'Button Image 1'
            flash_msg = 'Buttons Group "descr" was added'
        view.fill({'btn_group_text': "group_text",
                   'btn_group_hvr_text': "descr",
                   'btn_image': image})
        view.add_button.click()
        view = self.create_view(DetailsCatalogItemView)
        assert view.is_displayed
        view.flash.assert_success_message(flash_msg)

    def add_button(self):
        view = navigate_to(self, 'AddButton')
        if self.appliance.version >= '5.9':
            image = 'fa-user'
            flash_msg = 'Custom Button "btn_descr" was added'
        else:
            image = 'Button Image 1'
            flash_msg = 'Button "btn_descr" was added'
        view.fill(self._categorize_fill_dict({
            'btn_text': "btn_text",
            'btn_hvr_text': "btn_descr",
            'btn_image': image,
            'select_dialog': self.dialog,
            'system_process': "Request",
            'request': "InspectMe"}))
        view.add_button.click()
        view = self.create_view(DetailsCatalogItemView)
        time.sleep(5)
        assert view.is_displayed
        view.flash.assert_success_message(flash_msg)

    @property
    def exists(self):
        try:
            navigate_to(self, 'Details')
            return True
        except CandidateNotFound:
            return False


class CatalogBundle(CatalogItem, Navigatable):

    def __init__(self, name=None, description=None, display_in=None,
                 catalog=None, dialog=None, catalog_items=None, appliance=None):
        self.catalog_items = catalog_items
        super(CatalogBundle, self).__init__(
            name=name,
            description=description,
            display_in=display_in,
            catalog=catalog,
            dialog=dialog
        )
        Navigatable.__init__(self, appliance=appliance)

    def create(self):
        view = navigate_to(self, 'BundleAdd')
        domain = "ManageIQ (Locked)"
        view.basic_info.fill({
            'name': self.name,
            'description': self.description,
            'display': self.display_in,
            'select_catalog': self.catalog.name,
            'select_dialog': self.dialog
        })
        if view.basic_info.field_entry_point.value == "":
            view.basic_info.fill({'field_entry_point': ''})
            view.basic_info.tree.click_path(
                "Datastore", domain, "Service", "Provisioning",
                "StateMachines", "ServiceProvision_Template", "CatalogItemInitialization")
            view.apply_button.click()
        for cat_item in self.catalog_items:
            view.resources.fill({'select_resource': cat_item})
        view.add_button.click()
        view.flash.assert_success_message('Catalog Bundle "{}" was added'.format(self.name))
        view = self.create_view(AllCatalogItemView)
        assert view.is_displayed
        view.flash.assert_no_error()

    def update(self, updates):
        view = navigate_to(self, 'BundleEdit')
        changed = view.resources.fill({'select_resource': updates.get('catalog_items')})
        if changed:
            view.save_button.click()
        else:
            view.cancel_button.click()
        if changed:
            view.flash.assert_success_message(
                'Catalog Bundle "{}" was saved'.format(updates.get('name', self.name)))
        else:
            view.flash.assert_success_message(
                'Edit of Catalog Bundle"{}" was cancelled by the user'.format(self.name))
        view = self.create_view(DetailsCatalogItemView, override=updates)
        assert view.is_displayed
        view.flash.assert_no_error()


@navigator.register(CatalogItem, 'All')
class All(CFMENavigateStep):
    VIEW = AllCatalogItemView

    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Services', 'Catalogs')
        self.view.catalog_items.tree.click_path('All Catalog Items')


@navigator.register(CatalogItem, 'Details')
class Details(CFMENavigateStep):
    VIEW = DetailsCatalogItemView
    prerequisite = NavigateToSibling('All')

    def step(self):
        self.prerequisite_view.catalog_items.tree.click_path("All Catalog Items",
                                                             self.obj.catalog.name, self.obj.name)


@navigator.register(CatalogItem, 'Add')
class Add(CFMENavigateStep):
    VIEW = AddCatalogItemView
    prerequisite = NavigateToSibling('All')

    def am_i_here(self):
        # Going to an Add page should always be done from first principles incase a previous Add
        # failed
        return False

    def step(self):
        self.prerequisite_view.configuration.item_select('Add a New Catalog Item')


@navigator.register(CatalogItem, 'Edit')
class Edit(CFMENavigateStep):
    VIEW = EditCatalogItemView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.configuration.item_select('Edit this Item')


@navigator.register(CatalogItem, 'AddButtonGroup')
class AddButtonGroup(CFMENavigateStep):
    VIEW = AddButtonGroupView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.configuration.item_select('Add a new Button Group')


@navigator.register(CatalogItem, 'AddButton')
class AddButton(CFMENavigateStep):
    VIEW = AddButtonView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.configuration.item_select('Add a new Button')


@navigator.register(CatalogItem, 'EditTagsFromDetails')
class EditTags(CFMENavigateStep):
    VIEW = TagPageView
    prerequisite = NavigateToSibling('Details')

    def step(self):
        self.prerequisite_view.policy.item_select('Edit Tags')


@navigator.register(CatalogBundle, 'BundleAll')
class BundleAll(CFMENavigateStep):
    VIEW = AllCatalogItemView
    prerequisite = NavigateToAttribute('appliance.server', 'LoggedIn')

    def step(self):
        self.prerequisite_view.navigation.select('Services', 'Catalogs')
        self.view.catalog_items.tree.click_path('All Catalog Items')


@navigator.register(CatalogBundle, 'BundleDetails')
class BundleDetails(CFMENavigateStep):
    VIEW = DetailsCatalogItemView
    prerequisite = NavigateToSibling('BundleAll')

    def step(self):
        self.prerequisite_view.catalog_items.tree.click_path("All Catalog Items",
                                                             self.obj.catalog.name, self.obj.name)


@navigator.register(CatalogBundle, 'BundleAdd')
class BundleAdd(CFMENavigateStep):
    VIEW = AddCatalogBundleView
    prerequisite = NavigateToSibling('BundleAll')

    def step(self):
        self.prerequisite_view.configuration.item_select('Add a New Catalog Bundle')


@navigator.register(CatalogBundle, 'BundleEdit')
class BundleEdit(CFMENavigateStep):
    VIEW = EditCatalogBundleView
    prerequisite = NavigateToSibling('BundleDetails')

    def step(self):
        self.prerequisite_view.configuration.item_select('Edit this Item')
