from pathlib import Path
import tomlkit
from frappe_manager.migration_manager.migration_base import MigrationBase
from frappe_manager.migration_manager.migration_helpers import MigrationBenches, MigrationServicesManager
from frappe_manager.migration_manager.version import Version
from frappe_manager.migration_manager.backup_manager import BackupManager


class MigrationV0140(MigrationBase):
    version = Version("0.14.0")

    def init(self):
        self.cli_dir: Path = Path.home() / 'frappe'
        self.benches_dir = self.cli_dir / "sites"
        self.backup_manager = BackupManager(str(self.version), self.benches_dir)
        self.benches_manager = MigrationBenches(self.benches_dir)
        self.services_manager: MigrationServicesManager = MigrationServicesManager(
            services_path=self.cli_dir / 'services'
        )

    def migrate_services(self):
        config_path = self.cli_dir / 'fm_config.toml'

        if config_path.exists():
            data = tomlkit.parse(config_path.read_text())
            email = data.get('le_email', None)
            data['letsencrypt'] = {'email': email}

            if email:
                del data['le_email']

            with open(config_path, 'w') as f:
                f.write(tomlkit.dumps(data))
