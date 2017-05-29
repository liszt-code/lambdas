'use strict';

module.exports.buildings = (event, context, callback) => {
    const response = {
        statusCode: 200,
        headers: {
        },
        body: JSON.stringify({
            message: '',
            input: event,
        }),
    };

    callback(null, response);
};
