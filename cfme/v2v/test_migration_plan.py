import fauxfactory

from cfme.utils.appliance.implementations.ui import navigate_to

def infa_map():
    # Todo: `infra_map` should be replaced by infra_map object
    return "infra_map_obj"

#Todo: As table widget issue reolved, I will parameterize this with `csv` and `discovery`
def test_plan_via_discovery(appliance, infra_map):
    coll = appliance.collections.migration_plan
    view = navigate_to(coll, 'Add')

    #Todo: This need to be replaced by dynamic vm_name handling
    migrate_list = ('vmname1', 'vmname1', 'vmname1')
    appliance.collections.migration_plan.create(name="plan_".format(fauxfactory.gen_alphanumeric()),
                                                description="desc_".format(fauxfactory.gen_alphanumeric()),
                                                infra_map=infra_map.name,
                                                vm_names=migrate_list)
