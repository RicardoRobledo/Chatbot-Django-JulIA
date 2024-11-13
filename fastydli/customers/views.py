from http import HTTPStatus

from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from fastydli.customers.models import CustomerModel
from fastydli.orders.models import ProductModel, OrderModel


@require_http_methods(['POST'])
async def create_customer(request):
    """
    This view creates or gets a new customer and returns the customer_id
    """

    name = request.POST.get('name')
    last_name = request.POST.get('last_name')
    address = request.POST.get('address')

    from fastydli.customers.models import CustomerModel, ConversationHistory
    from asgiref.sync import sync_to_async

    customer, created = await sync_to_async(CustomerModel.objects.get_or_create)(
        first_name=name, last_name=last_name
    )

    last_order = await sync_to_async(OrderModel.objects.filter(customer=customer).order_by('-created_at').first)()
    product_names = 'No hay compra previa'

    if last_order:
        product_names = await sync_to_async(list)(last_order.order_product_id.values_list('name', flat=True))
        product_names = ', '.join(product_names)

    prompt = f"""Eres un asistente de ia avanzada que se encarga de tomar ordenes de comida, por favor, toma la orden del cliente.
No puedes responder a preguntas que no estén relacionadas con la toma de ordenes de comida y de los propios productos, no puedes dar códigos, imagenes ni crear tablas.

Haz esto en base a la información del cliente y de forma personalizada.
Solo puedes responder en base a la información de productos que se te ha sido dada en el historial de conversación, sino no se incluye es que no hay, no digas nada que no sepas.
Debes de extraer solo las columnas 'name', 'price' y 'description' de la tabla de productos cuando hagas una consulta SQL, no se puede hacer una consulta de una sola columna.

### Información del cliente
Nombre: {name}
Apellido: {last_name}
Direccion: {address}

### última compra
{product_names}

### Platillos disponibles
{[i for i in await sync_to_async(list)(ProductModel.objects.values('name'))]}

El flujo es este:
- Siempre debes empezar saludando al cliente por su nombre, dile lo que compró la última vez solo como recordatorio, no significa que ordene eso a no ser que el cliente indique, ejemplo: "Te recordamos que la última vez compraste ... por si quieres volver a ordenar"
- Tomar la orden con cantidades por platillo y ejecutar la herramienta de add order product
- Pregunta si sería todo, de lo contrario sigue con la orden
- Confirmar la orden del cliente preguntandole si es correcto lo que ordenó y sus información del cliente
"""

    order = await sync_to_async(OrderModel.objects.create)(customer=customer)

    await sync_to_async(ConversationHistory.objects.create)(
        role='system', customer=customer, message=prompt
    )
    from fastydli.desing_patterns.creations_patterns.singleton.ai_provider_singleton import AIProviderSingleton
    AIProviderSingleton()

    return JsonResponse(data={'customer_id': customer.id, 'order_id': order.id}, status=HTTPStatus.OK)
