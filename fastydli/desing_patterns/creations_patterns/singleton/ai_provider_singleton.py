from http import HTTPStatus
import json

from openai import AsyncOpenAI
from django.conf import settings

from fastydli.customers.models import ConversationHistory, CustomerModel
from fastydli.orders.models import ProductModel, OrderModel, OrderProductModel
from fastydli.base.parsers import OrderFormatter


__author__ = 'Ricardo'
__version__ = '1.0'


class AIProviderSingleton():

    __client = None

    @classmethod
    def __get_connection(self):
        """
        This method create our client
        """

        return AsyncOpenAI(api_key=settings.OPENAI_API_KEY,)

    def __new__(cls, *args, **kwargs):

        if cls.__client == None:

            # making connection
            cls.__client = cls.__get_connection()

        return cls.__client

    @classmethod
    async def create_completion_message(cls, customer, order, user_message):
        """
        This method creates a new completion message

        :param customer: the customer that we will use to order
        :param order: the order that we will use to create add products
        :param user_message: the message that we will use to create the completion message
        :return: a completion message
        """

        message = {'data': {}, 'status_code': HTTPStatus.OK}

        from asgiref.sync import sync_to_async

        history = []
        response = None

        # Convertimos el queryset en una lista de manera síncrona para evitar problemas al iterar
        conversation_messages = await sync_to_async(list)(ConversationHistory.objects.filter(customer=customer.id))

        for conversation_message in conversation_messages:
            if conversation_message.role == 'developer':
                history.append(
                    {'role': 'system', 'content': conversation_message.message})
            elif conversation_message.role == 'user':
                history.append(
                    {'role': 'user', 'content': conversation_message.message})
            elif conversation_message.role == 'assistant':

                if conversation_message.type == 'message':
                    history.append(
                        {'role': 'assistant', 'content': conversation_message.message})
                elif conversation_message.type == 'function_call':
                    history.append({
                        'type': conversation_message.type,
                        'id': conversation_message.tool_call_id,
                        'call_id': conversation_message.call_id,
                        'name': conversation_message.tool_name,
                        'arguments': conversation_message.arguments
                    })

            elif conversation_message.role == 'tool_call':
                history.append({
                    "type": "function_call_output",
                    "call_id": conversation_message.call_id,
                    "output": conversation_message.result,
                })

        response_message = await cls.__client.responses.create(
            model='gpt-4.1',
            input=history,
            tools=[{
                "type": "file_search",
                "vector_store_ids": ["vs_6840d53e459481918c516ea63d62215c"],
                "max_num_results": 3
            }, {
                "type": "function",
                "name": "finish_order",
                "description": "Finish the order process to confirm it",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "customer address where the order will be delivered"
                        },
                        "customer_profile": {
                            "type": "string",
                            "description": "customer summary about what likes, dislikes, allergies, etc."
                        }
                    }
                },
                "required": ["address", "customer_profile"]
            }],
            include=["file_search_call.results"])

        if response_message.output[0].type == 'file_search_call':

            doc = 'Resultados encontrados:'

            for result in response_message.output[0].results:
                doc += f'\n\n{result.text}'

            history.append({'role': 'assistant', 'content': doc})

            await sync_to_async(ConversationHistory.objects.create)(
                role='assistant', customer=customer, message=doc
            )

            response_message = await cls.__client.responses.create(
                model='gpt-4.1',
                input=history
            )

            await sync_to_async(ConversationHistory.objects.create)(
                role='assistant', customer=customer, message=response_message.output_text
            )

            history.append(
                {'role': 'assistant', 'content': response_message.output_text})

            response = response_message.output_text

        elif response_message.output[0].type == 'function_call':

            json_data = json.loads(response_message.output[0].arguments)

            if json_data['address'] == '' or json_data['customer_profile'] == '':

                print(
                    '\n\nError al procesar la orden, dirección o perfil del cliente no proporcionados\n\n')

                await sync_to_async(ConversationHistory.objects.create)(
                    role='assistant', customer=customer, message='Trataste de ejecutar la tool, pero hubo un error al procesar la orden, debo intentar de nuevo leyendo todo lo anterior paso a paso y asegurarme de que la dirección y orden del cliente han sido confirmados por el, sino le pediré confirmación al cliente y su dirección tal como lo indican los pasos del flujo.'
                )
                response = 'Parece ser que hubo un error, ¿Podrías repetirme de nuevo?'
                history.append(
                    {'role': 'assistant',
                        'content': 'Parece que hubo un error al procesar la orden, debo intentar de nuevo leyendo todo lo anterior paso a paso y asegurarme de que la dirección y orden del cliente han sido confirmados por el, sino le pediré confirmación al cliente y su dirección tal como lo indican los pasos del flujo.'}
                )

            else:

                history.append({
                    'type': response_message.output[0].type,
                    'id': response_message.output[0].id,
                    'call_id': response_message.output[0].call_id,
                    'name': response_message.output[0].name,
                    'arguments': response_message.output[0].arguments
                })

                await sync_to_async(ConversationHistory.objects.create)(
                    role='function_call',
                    customer=customer,
                    tool_name=response_message.output[0].name,
                    tool_call_id=response_message.output[0].id,
                    call_id=response_message.output[0].call_id,
                    type=response_message.output[0].type,
                    arguments=json_data
                )

                history.append({
                    "type": "function_call_output",
                    "call_id": response_message.output[0].call_id,
                    "output": 'tool ejecutada',
                })

                await sync_to_async(ConversationHistory.objects.create)(
                    role="function_call_output",
                    customer=customer,
                    call_id=response_message.output[0].call_id,
                    result='tool ejecutada'
                )

                response_parsed = await cls.__client.responses.parse(
                    model='gpt-4.1',
                    input=history +
                    [{'role': 'user', 'content': 'Lo anterior son datos de una orden, debes extraer los productos de la orden, pero el nombre debe ser tal cual el que está en tu conocimiento y herramienta de file_search, extrae el nombre tal cual y sin modificar'}],
                    text_format=OrderFormatter
                )

                products_parsed = response_parsed.output_parsed.products
                products_ordered = []
                total = 0

                for product_parsed in products_parsed:
                    product = await sync_to_async(lambda: ProductModel.objects.filter(name=product_parsed.product).first())()
                    total += product.price * product_parsed.quantity
                    products_ordered.append(OrderProductModel(
                        product=product, order=order, quantity=product_parsed.quantity))

                await sync_to_async(OrderProductModel.objects.bulk_create)(products_ordered)

                order.total = total
                order.address = json_data['address']
                await sync_to_async(order.save)()

                response_message = await cls.__client.responses.create(
                    model='gpt-4.1',
                    input=history
                )

                await sync_to_async(ConversationHistory.objects.create)(
                    role='assistant', customer=customer, message=response_message.output_text
                )

                history.append(
                    {'role': 'assistant', 'content': response_message.output_text})

                await sync_to_async(ConversationHistory.objects.filter(customer=customer).delete)()
                await sync_to_async(CustomerModel.objects.update)(customer_profile=json_data['customer_profile'])

                response = '''**Tu orden ha sido concretada con éxito.**

Sí deseas hablar directamente con alguien para aclarar cualquier duda o tratar este asunto, por favor contacta al siguiente número:

📞 **4974562444**

Estamos para ayudarte.'''

        else:

            await sync_to_async(ConversationHistory.objects.create)(
                role='assistant', customer=customer, message=response_message.output_text
            )

            history.append(
                {'role': 'assistant', 'content': response_message.output_text})

            response = response_message.output_text

        message['data'] = {'message': response}

        return message
