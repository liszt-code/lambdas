'use strict';

const AWS = require('aws-sdk');
const dynamoDb = new AWS.DynamoDB.DocumentClient();
const uuid = require('uuid/v4');

module.exports = (event, callback) => {
    const params = {
        TableName: process.env.LISZT_BUILDINGS_TABLE,
        ConsistentRead: false,
    };

    return dynamoDb.scan(params, (error, data) => {
        if (error) {
            callback(error);
        }
        callback(error, data.Items);
    });
};
