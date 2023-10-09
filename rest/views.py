import random
import string
from rest_framework import generics
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest.models import Card, CustomUser, Transaction
from rest.serializers.CardSerializer import CardSerializer
from rest.serializers.CustomUserSerializer import CustomUserSerializer, UserRegisterSerializer
from rest.serializers.TransactionSerializer import TransactionSerializer
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination
from django_redis import get_redis_connection
from django.db.models import Sum
import random
import string



'''Kullanıcı sisteme kayıt olduktan sonra otomatik olarak bir adet kart oluşur ve atanır,'''

class RegisterView(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            card_no = ''.join(random.choice(string.digits) for _ in range(16))

            try:
                card = Card.objects.create(user=user, card_no=card_no)
            except Exception as e:
                return Response({"message": f"Hata oluştu: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            card_serializer = CardSerializer(card)

            return Response(
                {"message": "Kullanıcı kaydedildi ve otomatik olarak bir kart oluşturuldu."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


'''kullanıcı sisteme giriş yaptığında otomatik oluşan kart status=ACTIVE olarak
güncellenir.
Kullanıcı sisteme giriş yaptığında gerekli alanlar redis tarafında tutulur, kontrol için DB'ye
sorgu atılmaz.'''

class LoginView(APIView):
    def get(self, request):
        user = request.user
        try:
            if user is not None:
                card = Card.objects.get(user=user)

                if card.status != "ACTIVE":
                    card.status = "ACTIVE"
                    card.save()

                    redis_connection = get_redis_connection("default")
                    redis_connection.hmset(f"user:{user.id}", {"email": user.email})

                    return Response({"message": "Oturum başarıyla açıldı ve Kartın durumu başarıyla güncellendi."}, 
                                    status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Oturum başarıyla açıldı ve Kart zaten ACTIVE durumunda."}, status=status.HTTP_200_OK)
        except Card.DoesNotExist:
            return Response({"message": "Kullanıcıya ait bir kart bulunamadı."}, status=status.HTTP_404_NOT_FOUND)


'''1-Kullanıcı kart işlemleri(Oluşturma/Silme/Güncelleme/Listeleme(silinen kartlar
listelenmez))
-SYSTEM_CARD herhangi bir güncelleme işlemi yapılamaz.'''

class CardViewSet(viewsets.ModelViewSet):
    queryset = Card.objects.exclude(status='DELETED')
    pagination_class = LimitOffsetPagination
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.label == 'SYSTEM_CARD':
            return Response({"message": "SYSTEM_CARD güncellenemez."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status != 'DELETED':
            instance.status = 'DELETED'
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({"message": "Kart zaten silinmiş."}, status=status.HTTP_400_BAD_REQUEST)


'''2-Kullanıcı işlemlerini 2 şekilde listeleyebilir.
2.1-Detaylı(her işlemin detaylı görüldüğü, description ile filtreleme yapılabilen)'''

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['card__user', 'description']
    search_fields = ['description']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(card__user=user)


'''2-Kullanıcı işlemlerini 2 şekilde listeleyebilir.
2.2-Aktif kartların sayısı ile toplamda harcama yapılan tutar, pasif kartların toplamda
ne kadar harcama yapıldığı'''

class UserSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        active_cards = Card.objects.filter(user=user, status='ACTIVE')
        total_spent_on_active_cards = Transaction.objects.filter(card__in=active_cards).aggregate(Sum('amount'))['amount__sum'] or 0

        passive_cards = Card.objects.filter(user=user, status='PASSIVE')
        total_spent_on_passive_cards = Transaction.objects.filter(card__in=passive_cards).aggregate(Sum('amount'))['amount__sum'] or 0

        return Response({
            'active_cards_count': active_cards.count(),
            'total_spent_on_active_cards': total_spent_on_active_cards,
            'total_spent_on_passive_cards': total_spent_on_passive_cards,
        })


''' Kullanıcı herhangi bir kart numarası ile işlem gerçekleştirebilir.'''

class TransactionByCardView(generics.CreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, card_no):
        try:
            card = Card.objects.get(card_no=card_no)

            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                serializer.save(card=card)
                return Response({"message": "İşlem başarıyla oluşturuldu."}, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Card.DoesNotExist:
            return Response({"message": "Belirtilen kart numarasına sahip bir kart bulunamadı."}, status=status.HTTP_404_NOT_FOUND)