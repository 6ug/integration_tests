import fauxfactory
import pytest

from cfme.automate.import_export import AutomateGitRepository
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme import test_requirements
from cfme.automate.import_export import AutomateGitRepository
from cfme.utils.appliance.implementations.ui import navigate_to
from cfme.utils.update import update

pytest.mark.ignore_stream('5.8', '5.9')


@pytest.fixture
def infra_map():
    # Todo: add infra object from kk's code
    return "map1"


@pytest.fixture
def migrate_list():
    #Todo: remove hardcoding with auto-vm provisioning
    return ['ytale-v2v-ubuntu7']


@pytest.mark.parametrize('migration_flag', [True, False], ids=['start_migration', 'save_migration'])
@pytest.mark.parametrize('method', ['via_csv', 'via_discovery'])
def test_migration_plan(appliance, infra_map, migrate_list, method, migration_flag):
    if method == 'csv':
        csv_import = True
    else:
        csv_import = False

    coll = appliance.collections.migration_plan
    coll.create(name="plan_{}".format(fauxfactory.gen_alphanumeric()),
                description="desc_{}".format(fauxfactory.gen_alphanumeric()),
                infra_map=infra_map,
                vm_names=migrate_list,
                csv_import=csv_import,
                start_migration=migration_flag)

    if migration_flag:
        base_flash = "Migration Plan: '{}' is in progress".format(coll.name)
    else:
        base_flash = "Migration Plan: '{}' has been saved".format(coll.name)

    assert view.results.msg.read() == base_flash

