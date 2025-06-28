# management/commands/create_sacco_admins.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from sacco.models import Sacco
from sacco_admin_app.models import SaccoAdmin

class Command(BaseCommand):
    help = 'Create SaccoAdmin instances for existing admin users'

    def handle(self, *args, **options):
        # Define your existing admin mappings
        admin_mappings = [
            {'user_id': 12, 'sacco_id': 1},
            # Add more mappings as needed
            # {'user_id': 15, 'sacco_id': 2},
        ]
        
        for mapping in admin_mappings:
            try:
                user = User.objects.get(id=mapping['user_id'])
                sacco = Sacco.objects.get(id=mapping['sacco_id'])
                
                _, created = SaccoAdmin.objects.get_or_create(
                    user=user,
                    sacco=sacco
                )
                
                if created:
                    self.stdout.write(
                        print(
                            f'Created SaccoAdmin for {user.username} -> {sacco.name}'
                        )
                    )
                else:
                    self.stdout.write(
                        print(
                            f'SaccoAdmin already exists for {user.username} -> {sacco.name}'
                        )
                    )
                    
            except (User.DoesNotExist, Sacco.DoesNotExist) as e:
                self.stdout.write(
                    print(f'Error with mapping {mapping}: {e}')
                )