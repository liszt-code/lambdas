import boto3
import os
import time
from boto3.dynamodb.conditions import Attr, Key
from chalice import BadRequestError, Chalice, NotFoundError, Response
from uuid import uuid4 as uuid

app = Chalice(app_name='liszt')
dynamodb = boto3.client('dynamodb')

_LISZT_BUILDINGS_TABLE_NAME = os.getenv(
    'LISZT_BUILDINGS_TABLE', 'liszt-buildings-production')
_LISZT_UNITS_TABLE_NAME = os.getenv(
    'LISZT_UNITS_TABLE', 'liszt-units-production')
_LISZT_UNITS_GSI_NAME = os.getenv('LISZT_UNITS_GSI', 'building_unit_gsi')
_LISZT_RESIDENTS_TABLE_NAME = os.getenv(
    'LISZT_RESIDENTS_TABLE', 'liszt-residents-production')


def building_attribute_to_object(attribute):
    obj = {}
    obj['building_id'] = attribute.get('building_id', {}).get('S', '')
    obj['name'] = attribute.get('name', {}).get('S', '')
    return obj


def unit_attribute_to_object(attribute):
    obj = {}
    obj['unit_id'] = attribute.get('unit_id', {}).get('S', '')
    obj['name'] = attribute.get('name', {}).get('S', '')
    return obj


def resident_attribute_to_object(attribute):
    obj = {}
    obj['resident_id'] = attribute.get('resident_id', {}).get('S', '')
    obj['firstname'] = attribute.get('firstname', {}).get('S', '')
    obj['middlename'] = attribute.get('middlename', {}).get('S', '')
    obj['lastname'] = attribute.get('lastname', {}).get('S', '')
    return obj


@app.route('/buildings', methods=['GET'])
def list_buildings():
    response = dynamodb.scan(TableName=_LISZT_BUILDINGS_TABLE_NAME)
    items = response.get('Items', [])
    return [building_attribute_to_object(attribute) for attribute in items]


@app.route('/buildings/by_id', methods=['GET'])
def get_building_by_id():
    building_id = app.current_request.query_params.get('building_id')
    if not building_id:
        raise BadRequestError('building_id parameter is required')
    response = dynamodb.get_item(
        TableName=_LISZT_BUILDINGS_TABLE_NAME,
        Key={'building_id': {'S': building_id}}
    )
    item = response.get('Item')
    if not item:
        raise NotFoundError('building not found')
    return building_attribute_to_object(item)


@app.route('/buildings/register', methods=['POST'])
def register_building():
    payload = app.current_request.json_body
    name = payload.get('name')
    if not name:
        raise BadRequestError('name parameter is required')
    item = {
        'building_id': {'S': str(uuid())},
        'name': {'S': name},
    }
    dynamodb.put_item(TableName=_LISZT_BUILDINGS_TABLE_NAME, Item=item)
    return building_attribute_to_object(item)


@app.route('/buildings/deregister', methods=['DELETE'])
def deregister_building():
    building_id = app.current_request.query_params.get('building_id')
    if not building_id:
        raise BadRequestError('building_id parameter is required')
    dynamodb.delete_item(
        TableName=_LISZT_BUILDINGS_TABLE_NAME,
        Key={'building_id': {'S': building_id}}
    )
    return Response(body='', status_code=200)


@app.route('/buildings/units', methods=['GET'])
def list_building_units():
    building_id = app.current_request.query_params.get('building_id')
    if not building_id:
        raise BadRequestError('building_id parameter is required')
    response = dynamodb.query(
        TableName=_LISZT_UNITS_TABLE_NAME,
        IndexName=_LISZT_UNITS_GSI_NAME,
        KeyConditionExpression=Key('mykey').eq('myvalue')
    )
    return [unit_attribute_to_object(item) for item in response.get('Items', [])]  # noqa


@app.route('/units/register', methods=['POST'])
def register_unit():
    payload = app.current_request.json_body
    name = payload.get('name')
    if not name:
        raise BadRequestError('name parameter is required')
    building_id = payload.get('building_id')
    if not building_id:
        raise BadRequestError('building_id parameter is required')
    item = {
        'unit_id': str(uuid()),
        'name': name,
        'building_id': building_id,
    }
    dynamodb.put_item(TableName=_LISZT_UNITS_TABLE_NAME, Item=item)
    return item


@app.route('/units/deregister', methods=['DELETE'])
def deregister_unit():
    unit_id = app.current_request.query_params.get('unit_id')
    if not unit_id:
        raise BadRequestError('unit_id parameter is required')
    dynamodb.delete_item(
        TableName=_LISZT_UNITS_TABLE_NAME,
        Key={'unit_id': {'S': unit_id}}
    )
    return Response(body='', status_code=200)


@app.route('/units/residents', methods=['GET'])
def list_unit_residents():
    unit_id = app.current_request.query_params.get('unit_id')
    if not unit_id:
        raise BadRequestError('unit_id parameter is required')
    response = dynamodb.get_item(
        TableName=_LISZT_UNITS_TABLE_NAME,
        Key={'unit_id': {'S': unit_id}}
    )
    item = response.get('Item')
    if not item:
        raise NotFoundError('unit not found')
    resident_ids = item.get('Residents', [])

    keys = [{'resident_id': {'S': resident_id}} for resident_id in resident_ids]
    response = dynamodb.batch_get_item(
        RequestItems={_LISZT_RESIDENTS_TABLE_NAME: {'Keys': keys}}
    )
    items = response.get(_LISZT_UNITS_TABLE_NAME, [])
    return [resident_attribute_to_object(item) for item in items]


@app.route('/residents/by_id', methods=['GET'])
def get_resident_by_id():
    resident_id = app.current_request.query_params.get('resident_id')
    if not resident_id:
        raise BadRequestError('resident_id parameter is required')
    response = dynamodb.get_item(
        TableName=_LISZT_RESIDENTS_TABLE_NAME,
        Key={'resident_id': {'S': resident_id}}
    )
    item = response.get('Item')
    if not item:
        raise NotFoundError('resident not found')
    return resident_attribute_to_object(item)


@app.route('/residents/register', methods=['POST'])
def register_resident():
    payload = app.current_request.json_body
    resident = {
        'resident_id': str(uuid()),
        'name': payload.get('name'),
    }
    dynamodb.put_item(TableName=_LISZT_RESIDENTS_TABLE_NAME, Item=resident)
    return resident


@app.route('/residents/deregister', methods=['DELETE'])
def deregister_resident():
    resident_id = app.current_request.query_params.get('resident_id')
    if not resident_id:
        raise BadRequestError('resident_id parameter is required')
    dynamodb.delete_item(
        TableName=_LISZT_RESIDENTS_TABLE_NAME,
        Key={'resident_id': {'S': resident_id}}
    )
    return Response(body='', status_code=200)


@app.route('/residents/move_in', methods=['POST'])
def move_resident_in():
    payload = app.current_request.json_body
    resident_id = payload.get('resident_id')
    unit_id = payload.get('unit_id')
    if not resident_id:
        raise BadRequestError('resident_id parameter is required')
    if not unit_id:
        raise BadRequestError('unit_id parameter is required')
    dynamodb.update_item(
        TableName=_LISZT_UNITS_TABLE_NAME,
        Key={'unit_id': {'S': unit_id}},
        UpdateExpression='ADD Residents :residents SET UpdatedAt = :timestamp',
        ExpressionAttributeValues={
            ':residents': [resident_id],
            ':timestamp': int(time.time()),
        },
        ConditionExpression=Attr('unit_id').exists()
    )
    return Response(body='', status_code=200)


@app.route('/residents/move_out', methods=['POST'])
def move_resident_out():
    payload = app.current_request.json_body
    resident_id = payload.get('resident_id')
    unit_id = payload.get('unit_id')
    if not resident_id:
        raise BadRequestError('resident_id parameter is required')
    if not unit_id:
        raise BadRequestError('unit_id parameter is required')
    dynamodb.update_item(
        TableName=_LISZT_UNITS_TABLE_NAME,
        Key={'unit_id': {'S': unit_id}},
        UpdateExpression='SET UpdatedAt = :timestamp DELETE Residents :resident',  # noqa
        ExpressionAttributeValues={
            ':residents': [resident_id],
            ':timestamp': int(time.time()),
        },
        ConditionExpression=Attr('unit_id').exists()
    )
    return Response(body='', status_code=200)
