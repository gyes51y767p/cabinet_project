var mqtt = require('mqtt')

var globalMessage="";

var options = {
    host: '61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud',
    port: 8883,
    protocol: 'mqtts',
    username: 'gyes51y767p',
    password: '@Mm5648970'
}

// initialize the MQTT client
var client = mqtt.connect(options);

// setup the callbacks
client.on('connect', function () {
    console.log('Connected');
});

client.on('error', function (error) {
    console.log(error);
});

client.on('message', function (topic, message) {
    // called each time a message is received
    console.log('Received message:', topic, message.toString());
    document.querySelector('.first-line').innerHTML = message.toString();
    console.log('Received message:', topic, message.toString());
});var mqtt = require('mqtt')

var options = {
    host: '61850993d7e340d7b170bcd12078ef88.s2.eu.hivemq.cloud',
    port: 8883,
    protocol: 'mqtts',
    username: 'gyes51y767p',
    password: '@Mm5648970'
}

// initialize the MQTT client
var client = mqtt.connect(options);

// setup the callbacks
client.on('connect', function () {
    console.log('Connected');
});

client.on('error', function (error) {
    console.log(error);
});

client.on('message', function (topic, message) {
    // called each time a message is received
    console.log('Received message:', topic, message.toString());
    globalMessage= globalMessage+message.toString()+"\n";
});

// subscribe to topic 'my/test/topic'
client.subscribe('/door1');

// publish message 'Hello' to topic 'my/test/topic'
//client.publish('my/test/topic', 'Hello');

// subscribe to topic 'my/test/topic'
client.subscribe('/door1');

// publish message 'Hello' to topic 'my/test/topic'
//client.publish('my/test/topic', 'Hello');