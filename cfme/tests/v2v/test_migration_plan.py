import fauxfactory
import pytest

from cfme.utils.appliance.implementations.ui import navigate_to

pytest.mark.ignore_stream('5.8', '5.9')

def infa_map():
    # Todo: `infra_map` should be replaced by infra_map object
    return "infra_map_obj"

#Todo: As upload widget issue reolved, need to parameterize this with `csv` and `discovery`
def test_plan_via_discovery(appliance, infra_map):
    coll = appliance.collections.migration_plan
    view = navigate_to(coll, 'Add')

    #Todo: This need to be replaced by dynamic vm_name handling
    migrate_list = ('ytale_win7_nvc60_v2v', 'ytale_nfs79_v2v_nvc60')
    appliance.collections.migration_plan.create(name="plan_".format(fauxfactory.gen_alphanumeric()),
                                                description="desc_".format(fauxfactory.gen_alphanumeric()),
                                                infra_map=infra_map.name,
                                                vm_names=migrate_list)

@pytest.mark.manual
def test_plan_via_csv():
    """
    same steps as discovery only uploading is via csv file
    Todo: upload widget work in progress
    """
    pass