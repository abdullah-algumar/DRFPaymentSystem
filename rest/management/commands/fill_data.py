from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest.models import CustomUser, Card, Transaction

class Command(BaseCommand):
    help = 'Verileri doldurmak için özel komut'

    def handle(self, *args, **options):
        for i in range(1, 6):
            # kullanicilar
            user = CustomUser.objects.create(email=f'user{i}@example.com')
            user.set_password(f'password{i}')
            user.save()

            # kartlar
            for j in range(1, 4):
                card = Card.objects.create(user=user, card_no=f'1234 5678 9012 345{i}{j}', status='ACTIVE')
                card.save()

                # İşlemler 
                for k in range(1, 6):
                    transaction = Transaction.objects.create(card=card, amount=100, description=f'Transaction {k}')
                    transaction.save()

        self.stdout.write(self.style.SUCCESS('Veriler başarıyla oluşturuldu.'))
