# -*- coding: utf-8 -*-
"""This module contains control REST API specific tests."""
import pytest
import fauxfactory

from cfme import test_requirements
from cfme.rest.gen_data import conditions as _conditions
from cfme.rest.gen_data import policies as _policies
from cfme.utils.rest import (
    assert_response,
    delete_resources_from_collection,
    delete_resources_from_detail,
    query_resource_attributes,
)
from cfme.utils.version import current_version
from cfme.utils.wait import wait_for

pytestmark = [
    test_requirements.rest
]


class TestConditionsRESTAPI(object):
    @pytest.fixture(scope='function')
    def conditions(self, request, appliance):
        num_conditions = 2
        response = _conditions(request, appliance.rest_api, num=num_conditions)
        assert_response(appliance)
        assert len(response) == num_conditions
        return response

    def test_query_condition_attributes(self, conditions, soft_assert):
        """Tests access to condition attributes.

        Metadata:
            test_flag: rest
        """
        query_resource_attributes(conditions[0], soft_assert=soft_assert)

    def test_create_conditions(self, appliance, conditions):
        """Tests create conditions.

        Metadata:
            test_flag: rest
        """
        for condition in conditions:
            record = appliance.rest_api.collections.conditions.get(id=condition.id)
            assert record.description == condition.description

    @pytest.mark.parametrize('method', ['post', 'delete'], ids=['POST', 'DELETE'])
    def test_delete_conditions_from_detail(self, conditions, method):
        """Tests delete conditions from detail.

        Metadata:
            test_flag: rest
        """
        delete_resources_from_detail(conditions, method=method, num_sec=100, delay=5)

    def test_delete_conditions_from_collection(self, conditions):
        """Tests delete conditions from collection.

        Metadata:
            test_flag: rest
        """
        delete_resources_from_collection(conditions, num_sec=100, delay=5)

    @pytest.mark.parametrize(
        'from_detail', [True, False],
        ids=['from_detail', 'from_collection'])
    def test_edit_conditions(self, conditions, appliance, from_detail):
        """Tests edit conditions.

        Metadata:
            test_flag: rest
        """
        num_conditions = len(conditions)
        uniq = [fauxfactory.gen_alphanumeric(5) for _ in range(num_conditions)]
        new = [{'description': 'Edited Test Condition {}'.format(u)} for u in uniq]
        if from_detail:
            edited = []
            for index in range(num_conditions):
                edited.append(conditions[index].action.edit(**new[index]))
                assert_response(appliance)
        else:
            for index in range(num_conditions):
                new[index].update(conditions[index]._ref_repr())
            edited = appliance.rest_api.collections.conditions.action.edit(*new)
            assert_response(appliance)
        assert len(edited) == num_conditions
        for index, condition in enumerate(conditions):
            record, __ = wait_for(
                lambda: appliance.rest_api.collections.conditions.find_by(
                    description=new[index]['description']) or False,
                num_sec=100,
                delay=5,
                message="Find a test condition"
            )
            condition.reload()
            assert condition.description == edited[index].description == record[0].description


class TestPoliciesRESTAPI(object):
    @pytest.fixture(scope='function')
    def policies(self, request, appliance):
        num_policies = 2
        response = _policies(request, appliance.rest_api, num=num_policies)
        assert_response(appliance)
        assert len(response) == num_policies
        return response

    def test_query_policy_attributes(self, policies, soft_assert):
        """Tests access to policy attributes.

        Metadata:
            test_flag: rest
        """
        query_resource_attributes(policies[0], soft_assert=soft_assert)

    def test_create_policies(self, appliance, policies):
        """Tests create policies.

        Metadata:
            test_flag: rest
        """
        for policy in policies:
            record = appliance.rest_api.collections.policies.get(id=policy.id)
            assert record.description == policy.description

    def test_delete_policies_from_detail_post(self, policies):
        """Tests delete policies from detail using POST method.

        Metadata:
            test_flag: rest
        """
        delete_resources_from_detail(policies, method='POST', num_sec=100, delay=5)

    @pytest.mark.uncollectif(lambda: current_version() < '5.9')
    def test_delete_policies_from_detail_delete(self, policies):
        """Tests delete policies from detail using DELETE method.

        Testing BZ 1435773

        Metadata:
            test_flag: rest
        """
        delete_resources_from_detail(policies, method='DELETE', num_sec=100, delay=5)

    def test_delete_policies_from_collection(self, policies):
        """Tests delete policies from collection.

        Metadata:
            test_flag: rest
        """
        delete_resources_from_collection(policies, num_sec=100, delay=5)

    @pytest.mark.parametrize(
        'from_detail', [True, False],
        ids=['from_detail', 'from_collection'])
    def test_edit_policies(self, policies, appliance, from_detail):
        """Tests edit policies.

        Testing BZ 1435777

        Metadata:
            test_flag: rest
        """
        num_policies = len(policies)
        uniq = [fauxfactory.gen_alphanumeric(5) for _ in range(num_policies)]
        new = [{'description': 'Edited Test Policy {}'.format(u)} for u in uniq]
        if from_detail:
            edited = []
            for index in range(num_policies):
                edited.append(policies[index].action.edit(**new[index]))
                assert_response(appliance)
        else:
            for index in range(num_policies):
                new[index].update(policies[index]._ref_repr())
            edited = appliance.rest_api.collections.policies.action.edit(*new)
            assert_response(appliance)
        assert len(edited) == num_policies
        for index, policy in enumerate(policies):
            record, __ = wait_for(
                lambda: appliance.rest_api.collections.policies.find_by(
                    description=new[index]['description']) or False,
                num_sec=100,
                delay=5,
                message="Find a policy"
            )
            policy.reload()
            assert policy.description == edited[index].description == record[0].description
