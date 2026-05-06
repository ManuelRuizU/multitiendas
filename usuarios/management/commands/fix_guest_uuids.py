    # usuarios/management/commands/fix_guest_uuids.py
import uuid
from django.core.management.base import BaseCommand
from usuarios.models import Cliente
from django.db import transaction

class Command(BaseCommand):
        help = 'Ensures all Cliente records have unique non-null guest_uuids.'

        def handle(self, *args, **kwargs):
            self.stdout.write("Starting guest_uuid consistency check for Cliente records...")
            
            with transaction.atomic():
                clients_to_update = []
                # Obtener todos los UUIDs existentes para verificar unicidad
                existing_uuids = set(Cliente.objects.exclude(guest_uuid__isnull=True).values_list('guest_uuid', flat=True))

                for cliente in Cliente.objects.all():
                    # Si guest_uuid es NULL o si ya existe en el conjunto de UUIDs existentes (duplicado)
                    if cliente.guest_uuid is None or cliente.guest_uuid in existing_uuids:
                        new_uuid = uuid.uuid4()
                        # Generar un nuevo UUID hasta que sea realmente único
                        while new_uuid in existing_uuids:
                            new_uuid = uuid.uuid4()
                        
                        cliente.guest_uuid = new_uuid
                        existing_uuids.add(new_uuid) # Añadir el nuevo UUID al conjunto para futuras verificaciones
                        clients_to_update.append(cliente)
                        self.stdout.write(f"  Updated Cliente ID {cliente.id} with new guest_uuid: {cliente.guest_uuid}")
                
                if clients_to_update:
                    # Usar bulk_update para mayor eficiencia al guardar
                    Cliente.objects.bulk_update(clients_to_update, ['guest_uuid'])
                    self.stdout.write(self.style.SUCCESS(f"Successfully updated {len(clients_to_update)} Cliente records with unique guest_uuids."))
                else:
                    self.stdout.write(self.style.SUCCESS("All Cliente records already have unique non-null guest_uuids. No updates needed."))

            self.stdout.write("Guest_uuid consistency check completed.")