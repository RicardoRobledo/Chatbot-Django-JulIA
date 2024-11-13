from http import HTTPStatus

from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from fastydli.customers.models import CustomerModel, ConversationHistory
from fastydli.orders.models import OrderModel

from fastydli.desing_patterns.creations_patterns.singleton.ai_provider_singleton import AIProviderSingleton
from fastydli.desing_patterns.creations_patterns.singleton.vector_db_singleton import VectorDBSingleton


@require_http_methods(['GET'])
def home(request):

    return render(request, 'chatbot/home.html')


@require_http_methods(['POST'])
async def send_message(request):

    VectorDBSingleton()
    AIProviderSingleton()

    message = request.POST.get('message')
    customer_id = request.POST.get('customer_id')
    order_id = request.POST.get('order_id')

    from asgiref.sync import sync_to_async

    customer = await sync_to_async(CustomerModel.objects.filter)(id=customer_id)
    # Obtener el primer resultado
    customer_instance = await sync_to_async(lambda: customer.first())()

    order = await sync_to_async(OrderModel.objects.filter)(id=order_id)
    order_instance = await sync_to_async(lambda: order.first())()

    # Crear el registro en ConversationHistory de forma asíncrona
    await sync_to_async(ConversationHistory.objects.create)(
        role='user', customer=customer_instance, message=message
    )

    # Llamar a la función async del proveedor de IA
    data = await AIProviderSingleton.create_completion_message(customer_instance, order_instance, message)

    return JsonResponse(data=data, status=HTTPStatus.OK)
