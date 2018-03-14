# -*- coding: utf-8 -*-
import fauxfactory
import pytest

from cfme.configure.access_control import Role, User
from cfme.base.credential import Credential
from cfme.utils.blockers import BZ
from cfme.infrastructure.provider.virtualcenter import VMwareProvider
from cfme.services.catalogs.orchestration_template import OrchestrationTemplate
from cfme.services.myservice.ui import MyService
from cfme.services.service_catalogs import ServiceCatalogs
from cfme.utils import error
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.utils import version

pytestmark = [
    pytest.mark.meta(server_roles="+automate"),
    pytest.mark.usefixtures('uses_infra_providers'),
    pytest.mark.usefixtures('setup_provider_modscope'),
    pytest.mark.provider([VMwareProvider], scope="module")
]


def new_credential():
    if BZ(1487199, forced_streams=['5.8']).blocks:
        return Credential(principal='uid{}'.format(fauxfactory.gen_alphanumeric().lower()),
                          secret='redhat')
    else:
        return Credential(principal='uid{}'.format(fauxfactory.gen_alphanumeric()),
                          secret='redhat')


def new_role(appliance, product_features):
    collection = appliance.collections.roles
    return collection.create(name='role_{}'.format(fauxfactory.gen_alphanumeric()),
                             vm_restriction=None, product_features=product_features)


def new_group(appliance, role):
    collection = appliance.collections.groups
    return collection.create(description='group_{}'.format(fauxfactory.gen_alphanumeric()),
                             role=role, tenant="My Company")


def new_user(appliance, group):
    collection = appliance.collections.users
    return collection.create(name='user_{}'.format(fauxfactory.gen_alphanumeric()),
                             credential=new_credential(),
                             email='xyz@redhat.com',
                             group=group,
                             cost_center='Workload',
                             value_assign='Database')


@pytest.yield_fixture(scope="module")
def role_user_group(appliance):
    role = new_role(appliance=appliance, product_features=[(['Everything'], False)] + [(['Everything', k], True)
                    for k in ['Access Rules for all Virtual Machines']])
    group = new_group(appliance=appliance, role=role.name)
    user = new_user(appliance=appliance, group=group)
    yield (role, user)


@pytest.yield_fixture(scope='function')
def _myservice(appliance, catalog_item):
    vm_name = catalog_item.provisioning_data["catalog"]["vm_name"] + '_0001'
    catalog_item.create()
    service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
    service_catalogs.order()
    yield catalog_item.name, vm_name


def test_service_rbac_no_permission(appliance, role_user_group):
    """ Test service rbac without user permission """
    role, user = role_user_group
    import ipdb;ipdb.set_trace()
    error_message = "The user's role is not authorized for any access, " \
                    "please contact the administrator!"
    with error.expected(error_message):
        appliance.server.login(user)


CATALOG_MODULES = ['Catalogs', 'Orchestration Templates', 'Catalog Items', 'Service Catalogs']


@pytest.mark.parametrize('permission', CATALOG_MODULES)
def test_service_rbac_catalog_explorer(appliance, role_user_group, catalog,
                                       catalog_item, permission):
    """ Test service rbac with only catalog explorer module permissions"""
    uncheck = [(['Everything'], True)] + [(['Everything'], False)]
    role, user = role_user_group
    appliance.server.login_admin()

    if permission == CATALOG_MODULES[3]:
        role.update({'product_features': uncheck +
                                         [(['Everything', 'Services', 'Catalogs Explorer', k], True)
                                          for k in ['Catalog Items', 'Service Catalogs', 'Catalogs']] +
                                         [(['Everything', 'Services', 'Requests', ], True)] +
                                         [(['Everything', 'Automation', 'Automate', 'Customization'], True)]})
    else:
        role.update({'product_features': uncheck +
                                         [(['Everything', 'Services', 'Catalogs Explorer', k], True)
                                          for k in [permission]]})

    with user:
        appliance.server.login(user)
        if permission == CATALOG_MODULES[0]:
            assert catalog.exists
            catalog.delete()
        elif permission == CATALOG_MODULES[1]:
            template = OrchestrationTemplate(template_type="CloudFormation Templates",
                                             template_name=fauxfactory.gen_alphanumeric(),
                                             description="my_template")
            template.create(fauxfactory.gen_numeric_string())
            assert template.exists
            template.delete()
        elif permission == CATALOG_MODULES[2]:
            catalog_item.create()
            assert catalog_item.exists
            catalog_item.delete()
        elif permission == CATALOG_MODULES[3]:
            catalog_item.create()
            service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
            service_catalogs.order()
            service_request = appliance.collections.requests.instantiate(catalog_item.name,
                                                                         partial_check=True)
            service_request.wait_for_request()
            assert service_request.is_succeeded()
            catalog_item.delete()


def test_service_rbac_request(appliance, role_user_group, catalog_item):
    """ Test service rbac with only request module permissions"""
    role, user = role_user_group
    role.update({'product_features': [(['Everything'], True)] + [(['Everything'], False)] +
                                     [(['Everything', 'Services', 'Catalogs Explorer', k], True)
                                     for k in ['Catalog Items', 'Service Catalogs', 'Catalogs']] +
                                     [(['Everything', 'Services', 'Requests', ], True)]+
                                     [(['Everything', 'Automation', 'Automate', 'Customization'],
                                       True)]})
    with user:
        catalog_item.create()
        service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
        service_catalogs.order()
        cells = {'Description': catalog_item.name}
        order_request = appliance.collections.requests.instantiate(cells=cells, partial_check=True)
        order_request.wait_for_request(method='ui')
        assert order_request.is_succeeded(method='ui')

