/*
 * File: app.js
 *
 * This file was generated by Sencha Architect version 3.0.4.
 * http://www.sencha.com/products/architect/
 *
 * This file requires use of the Ext JS 4.2.x library, under independent license.
 * License of Sencha Architect does not include license for Ext JS 4.2.x. For more
 * details see http://www.sencha.com/license or contact license@sencha.com.
 *
 * This file will be auto-generated each and everytime you save your project.
 *
 * Do NOT hand edit this file.
 */

// @require @packageOverrides
Ext.Loader.setConfig({
    enabled: true
});


Ext.application({
    models: [
        'ServiceModel'
    ],
    stores: [
        'Requests',
        'Services',
        'Methods'
    ],
    views: [
        'HomePanel'
    ],
    controllers: [
        'HomeController',
        'sosController'
    ],
    name: 'requests',

    launch: function() {
        Ext.create('requests.view.HomePanel');
        prettyPrint();
    }

});
