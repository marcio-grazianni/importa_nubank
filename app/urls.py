from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.TransacaoListView.as_view(), name='transacao_list'),
    path('sintetico/', views.TransacaoSinteticoView.as_view(), name='transacao_sintetico'),
    path('upload/', views.upload_csv, name='transacao_upload'),
    path('nova/', views.TransacaoCreateView.as_view(), name='transacao_create'),
    path('<int:pk>/', views.TransacaoDetailView.as_view(), name='transacao_detail'),
    path('<int:pk>/editar/', views.TransacaoUpdateView.as_view(), name='transacao_update'),
    path('<int:pk>/excluir/', views.TransacaoDeleteView.as_view(), name='transacao_delete'),
]


