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

    # Verificar si existen órdenes para el cliente
    orders_exist = await sync_to_async(OrderModel.objects.filter(customer=customer).exists)()

    # Inicializar la variable para los nombres de productos
    product_names = 'No hay compra previa'

    # Si existen órdenes, obtener la primera
    if orders_exist:
        last_order = await sync_to_async(OrderModel.objects.filter(customer=customer).order_by('-created_at').first)()

        # Obtener los nombres de los productos asociados a la orden
        if last_order:
            product_names = await sync_to_async(list)(last_order.order_product_id.values_list('name', flat=True))
            product_names = ', '.join(product_names)

    prompt = f"""Eres un asistente de ia avanzada que se encarga de tomar ordenes de comida por medio de herramientas, por favor, toma la orden del cliente.
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

### El flujo de conversación
1 - Siempre debes empezar saludando al cliente por su nombre, dile lo que compró la última vez solo como recordatorio solo si compró algo, no significa que ordene eso a no ser que el cliente indique, ejemplo: "Te recordamos que la última vez compraste ..."
2 - Tomar orden.
  2.1 - Cuando el usuario mencione que quiere determinado platillo y no está incluido en el historial de conversación como encontrado, debes de usar la herramienta de extract vector db query para buscar si hay productos y posteriormente preguntar si lo platillos encontrados quiere agregarlos.
  2.2 - Tomar la orden con cantidades por platillo, solo puedes recordar los platillos encontrados y que ya estén en el historial de conversación por la tool de extract vector db query, esto para la toma de orden
3 - Siempre que se agregue un platillo, pregunta si sería todo.
3 - Confirmar la orden del cliente preguntandole si es correcto y listar lo que ordenó y sus información del cliente. Con todos los pasos completados anteriores, cuando se pida que confirme la orden el cliente en este ultimo pase despues de decir que es todo y diga que su orden es errónea, debes de proporcionarle el número de teléfono: 4974562444 para que pueda consultar de forma directa con una persona, dile que para tratar esto puede hablar con esta persona y lamenta el inconveniente. Solo proprciona el numero al final

En este momento le preguntaste al cliente: ¡Gracias por proporcionar tu información! ¿En qué puedo ayudarte?
"""

    order = await sync_to_async(OrderModel.objects.create)(customer=customer)

    await sync_to_async(ConversationHistory.objects.create)(
        role='system', customer=customer, message=prompt
    )
    from fastydli.desing_patterns.creations_patterns.singleton.ai_provider_singleton import AIProviderSingleton
    AIProviderSingleton()

    return JsonResponse(data={'customer_id': customer.id, 'order_id': order.id}, status=HTTPStatus.OK)
