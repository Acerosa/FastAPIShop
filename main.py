import time
from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request
from fastapi.background import BackgroundTasks
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ['http://127.0.0.1:300/'],
    allow_methods = ['*'],
    allow_headers = ['*']
)


# must be a different database

redis = get_redis_connection(
    host='redis-17161.c269.eu-west-1-3.ec2.cloud.redislabs.com',
    port = 17161,
    password='FPwLzHDv79kYPFNbLOG5EbMkl5MQA1on',
    decode_responses=True
)

@app.get('/orders/{pk}')
def get(pk:str):
    return Order.get(pk)

class Order(HashModel):
    product_id: str
    price:float
    fee:float
    total:float
    quantity:int
    status:str #pending, competed, refound

    class Meta:
        database=redis

@app.post('/orders')
async def create(request:Request, backgroundTask: BackgroundTasks): #id, quantity
    body = await request.json()
    req = requests.get('http://127.0.0.1:8000/products/%s' % body['id'])
    product = req.json()
    order = Order(
          product_id = body['id'],
          price=product['price'],
          fee=0.2 * int(product['price']),
          total=1.2 * int(product['price']),
          quantity=body['quantity'],
          status='pending').save()
    backgroundTask.add_task(oder_completed, order)
    return order

def oder_completed(order:Order):
    time.sleep(5)
    order.status = 'completed'
    order.save()
    redis.xadd('oder_completed', order.dict(), '*')


