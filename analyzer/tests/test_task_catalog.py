from unittest.mock import patch

from django.test import SimpleTestCase

from analyzer.services import task_catalog


class TaskCatalogTests(SimpleTestCase):
    def test_get_role_entry_reloads_config_map_when_file_changes(self):
        original_module = task_catalog.config_map
        original_mtime = task_catalog._config_map_mtime
        original_roles = original_module.MAP_CAR_ROLE

        try:
            old_roles = ({'jql': 'project = OLD'},)
            new_roles = ({'jql': 'project = OLD'}, {'jql': 'project = NEW'})
            task_catalog.config_map.MAP_CAR_ROLE = old_roles
            task_catalog._config_map_mtime = 1

            def fake_reload(module):
                module.MAP_CAR_ROLE = new_roles
                return module

            with patch.object(
                task_catalog, '_module_mtime', return_value=2
            ), patch.object(
                task_catalog.importlib, 'reload', side_effect=fake_reload
            ):
                role_entry = task_catalog.get_role_entry(1)

            self.assertEqual(role_entry['jql'], 'project = NEW')
            self.assertEqual(task_catalog._config_map_mtime, 2)
        finally:
            original_module.MAP_CAR_ROLE = original_roles
            task_catalog.config_map = original_module
            task_catalog._config_map_mtime = original_mtime
