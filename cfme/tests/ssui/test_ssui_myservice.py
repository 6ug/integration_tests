# -*- coding: utf-8 -*-
import pytest

from cfme.infrastructure.provider import InfraProvider
from cfme.services.myservice import MyService
from cfme import test_requirements
from cfme.utils import testgen
from cfme.utils.version import current_version
from cfme.utils.appliance import get_or_create_current_appliance, ViaSSUI


pytestmark = [
    pytest.mark.meta(server_roles="+automate"),
    test_requirements.ssui,
    pytest.mark.long_running
]


pytest_generate_tests = testgen.generate([InfraProvider], required_fields=[
    ['provisioning', 'template'],
    ['provisioning', 'host'],
    ['provisioning', 'datastore']
], scope="module")


@pytest.mark.uncollectif(lambda: current_version() < '5.8')
@pytest.mark.parametrize('context', [ViaSSUI])
def test_myservice_crud(setup_provider, context, order_catalog_item_in_ops_ui):
    """Tests Myservice crud in SSUI."""
    appliance = get_or_create_current_appliance()
    service_name = order_catalog_item_in_ops_ui
    with appliance.context.use(context):
        appliance.server.login()
        myservice = MyService(appliance, service_name)
        myservice.update({'name': '{}_edited'.format(service_name)})
        # TODO - add rest of myservice crud like delete in next phase.
