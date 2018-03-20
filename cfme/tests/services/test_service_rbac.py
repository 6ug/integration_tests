import fauxfactory
import pytest

from cfme.infrastructure.provider.virtualcenter import VMwareProvider
from cfme.services.service_catalogs import ServiceCatalogs

pytestmark = [
    pytest.mark.usefixtures('uses_infra_providers', 'setup_provider'),
    pytest.mark.provider([VMwareProvider], scope="module")
]

CATALOG_MODULES = ['Catalogs', 'Orchestration Templates', 'Catalog Items', 'Service Catalogs']


def new_role(appliance, product_features):
    collection = appliance.collections.roles
    return collection.create(name='role_{}'.format(fauxfactory.gen_alphanumeric()),
                             vm_restriction=None, product_features=product_features)


def new_group(appliance, role):
    collection = appliance.collections.groups
    return collection.create(description='group_{}'.format(fauxfactory.gen_alphanumeric()),
                             role=role, tenant="My Company")


def new_user(appliance, group, credential):
    collection = appliance.collections.users
    return collection.create(name='user_{}'.format(fauxfactory.gen_alphanumeric()),
                             credential=credential,
                             email='xyz@redhat.com',
                             groups=group,
                             cost_center='Workload',
                             value_assign='Database')


@pytest.yield_fixture(scope='module')
def role_user_group(appliance, new_credential):
    role = new_role(appliance=appliance, product_features=[(['Everything'], False),
                            (['Everything', 'Access Rules for all Virtual Machines'], True)])
    group = new_group(appliance=appliance, role=role.name)
    user = new_user(appliance=appliance, group=group, credential=new_credential)
    yield role, user


def test_service_rbac_no_permission(appliance, role_user_group):
    """ Test service rbac without user permission """
    role, user = role_user_group
    error_message = ("The user's role is not authorized for any access, "
                     "please contact the administrator!")
    with pytest.raises(Exception, match=error_message):
        appliance.server.login(user)


@pytest.mark.parametrize('permission', CATALOG_MODULES)
def test_service_rbac_catalog_explorer(appliance, role_user_group, catalog,
                                       catalog_item, permission):
    """ Test service rbac with only catalog explorer module permissions"""
    role, user = role_user_group
    if permission == CATALOG_MODULES[3]:
        role.update({
            'product_features': [(['Everything'], True)] + [(['Everything'], False)] +
                                [(['Everything', 'Services', 'Requests', ], True)] +
                                [(['Everything', 'Services', 'Catalogs Explorer', k], True)
                                 for k in ['Catalog Items', 'Service Catalogs', 'Catalogs']] +
                                [(['Everything', 'Automation', 'Automate', 'Customization'], True)]
        })
    else:
        role.update({
            'product_features': [(['Everything'], True)] + [(['Everything'], False)] +
                                [(['Everything', 'Services', 'Catalogs Explorer', k], True)
                                 for k in [permission]]
        })

    with user:
        if permission == CATALOG_MODULES[0]:
            assert catalog.exists
        elif permission == CATALOG_MODULES[1]:
            collection = appliance.collections.orchestration_templates
            template = collection.create(template_name=fauxfactory.gen_alphanumeric(),
                                         template_type='Amazon CloudFormation',
                                         template_group='CloudFormation Templates',
                                         description='template description',
                                         content=fauxfactory.gen_numeric_string())
            assert template.exists
            template.delete()
        elif permission == CATALOG_MODULES[2]:
            assert catalog_item.exists
        elif permission == CATALOG_MODULES[3]:
            # Without below line, service_order only works here via admin, not via user
            # TODO: Remove below line when this behavior gets fixed
            appliance.server.login(user)
            service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
            service_catalogs.order()
            service_request = appliance.collections.requests.instantiate(catalog_item.name,
                                                                         partial_check=True)
            service_request.wait_for_request()
            assert service_request.is_succeeded()


def test_service_rbac_request(appliance, role_user_group, catalog_item):
    """ Test service rbac with only request module permissions"""
    role, user = role_user_group
    role.update({
        'product_features': [(['Everything'], True)] + [(['Everything'], False)] +
                            [(['Everything', 'Services', 'Catalogs Explorer', k], True)
                             for k in ['Catalog Items', 'Service Catalogs', 'Catalogs']] +
                            [(['Everything', 'Services', 'Requests', ], True)] +
                            [(['Everything', 'Automation', 'Automate', 'Customization'], True)]
    })
    with user:
        # Without below line, service_order only works here via admin, not via user
        # TODO: Remove below line when this behavior gets fixed
        appliance.server.login(user)
        service_catalogs = ServiceCatalogs(appliance, catalog_item.catalog, catalog_item.name)
        service_catalogs.order()
        cells = {'Description': catalog_item.name}
        order_request = appliance.collections.requests.instantiate(cells=cells, partial_check=True)
        order_request.wait_for_request(method='ui')
        assert order_request.is_succeeded(method='ui')
