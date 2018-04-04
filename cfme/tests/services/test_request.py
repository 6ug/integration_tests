# -*- coding: utf-8 -*-
import fauxfactory
import pytest

from cfme.automate.explorer.domain import DomainCollection
from cfme.common.vm import VM
from cfme.infrastructure.provider import InfraProvider
from cfme.infrastructure.provider.virtualcenter import VMwareProvider
from cfme.services.service_catalogs import ServiceCatalogs
from cfme.services.requests import RequestsView
from cfme import test_requirements
from cfme.utils.update import update
from cfme.utils.appliance.implementations.ui import navigate_to



pytestmark = [
    pytest.mark.meta(server_roles="+automate"),
    pytest.mark.usefixtures('vm_name', 'uses_infra_providers', 'catalog_item'),
    pytest.mark.long_running,
    test_requirements.service,
    pytest.mark.tier(3),
    pytest.mark.provider([VMwareProvider], scope="module"),
]


def test_copy_request(appliance, setup_provider, provider, catalog_item, request):
    """Automate BZ 1194479"""
    vm_name = catalog_item.prov_data["catalog"]["vm_name"]
    request.addfinalizer(lambda: VM.factory(vm_name + "_0001", provider).cleanup_on_provider())
    catalog_item.create()
    service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
    service_catalogs.order()
    request_description = catalog_item.name
    service_request = appliance.collections.requests.instantiate(request_description,
                                                                 partial_check=True)
    service_request.wait_for_request()
    assert navigate_to(service_request, 'Details')


STATES = ['Approved', 'Denied', 'Pending Approval']


@pytest.mark.paramerize('states', STATES)
def test_request_filter(appliance, catalog_item, request, provider, states):
    """
    1. Approve: Auto-approved
    2. Denied: Canceled-apporval
    3. Pending approval: Manual-approval
    """
    if states == STATES[0]:
        service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
        service_catalogs.order()
        service_request = appliance.collections.requests.instantiate(catalog_item.name,
                                                                     partial_check=True)
        service_request.wait_for_request()
        new_view = appliance.browser.create_view(RequestsView)
        if not new_view.approved_state.selected:
            new_view.approved_state.click()
        if new_view.denied_state.selected:
            new_view.denied_state.click()
        if new_view.pending_state.selected:
            new_view.pending_state.click()
        new_view.apply_btn.click()
        for i in new_view.table.read():
            if i.get('Description') == service_request.description:
                assert i.get('Approval State') == states

    elif states == STATES[1]:
        service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
        service_catalogs.order()
        service_request = appliance.collections.requests.instantiate(catalog_item.name,
                                                                     partial_check=True)
        service_request.wait_for_request()

        dc = DomainCollection(appliance)
        new_domain = dc.create(name=fauxfactory.gen_alphanumeric(), enabled=True)
        request.addfinalizer(new_domain.delete_if_exists)
        first_instance = dc.instantiate(name='ManageIQ') \
            .namespaces.instantiate(name='Service') \
            .namespaces.instantiate(name='Provisioning') \
            .namespaces.instantiate(name='StateMachines') \
            .classes.instantiate(name='ServiceProvisionRequestApproval') \
            .instances.instantiate(name='Default')
        first_instance.copy_to(new_domain)

        mofified_instance = new_domain.namespaces.instantiate(name='Service') \
            .namespaces.instantiate(name='Provisioning') \
            .namespaces.instantiate(name='StateMachines') \
            .classes.instantiate(name='ServiceProvisionRequestApproval') \
            .instances.instantiate(name='Default')
        with update(mofified_instance):
            mofified_instance.fields = {"approval_type": {"value": "manual"}}

        request_description = catalog_item.name
        service_request = appliance.collections.requests.instantiate(
            description=request_description,
            partial_check=True)
        service_request.deny_request_ui(reason="denied request")

        new_view = appliance.browser.create_view(RequestsView)
        if new_view.approved_state.selected:
            new_view.approved_state.click()
        if not new_view.denied_state.selected:
            new_view.denied_state.click()
        if new_view.pending_state.selected:
            new_view.pending_state.click()

        new_view.apply_btn.click()
        for i in new_view.table.read():
            if i.get('Description') == service_request.description:
                assert i.get('Approval State') == states

    elif states == STATES[2]:
        service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
        service_catalogs.order()
        service_request = appliance.collections.requests.instantiate(catalog_item.name,
                                                                 partial_check=True)
        service_request.wait_for_request()

        dc = DomainCollection(appliance)
        new_domain = dc.create(name=fauxfactory.gen_alphanumeric(), enabled=True)
        request.addfinalizer(new_domain.delete_if_exists)
        first_instance = dc.instantiate(name='ManageIQ') \
            .namespaces.instantiate(name='Service') \
            .namespaces.instantiate(name='Provisioning') \
            .namespaces.instantiate(name='StateMachines') \
            .classes.instantiate(name='ServiceProvisionRequestApproval') \
            .instances.instantiate(name='Default')
        first_instance.copy_to(new_domain)

        mofified_instance = new_domain.namespaces.instantiate(name='Service') \
            .namespaces.instantiate(name='Provisioning') \
            .namespaces.instantiate(name='StateMachines') \
            .classes.instantiate(name='ServiceProvisionRequestApproval') \
            .instances.instantiate(name='Default')
        with update(mofified_instance):
            mofified_instance.fields = {"approval_type": {"value": "manual"}}

        new_view = appliance.browser.create_view(RequestsView)
        if new_view.approved_state.selected:
            new_view.approved_state.click()
        if new_view.denied_state.selected:
            new_view.denied_state.click()
        if not new_view.pending_state.selected:
            new_view.pending_state.click()

        new_view.apply_btn.click()
        for i in new_view.table.read():
            if i.get('Description') == service_request.description:
                assert i.get('Approval State') == states
