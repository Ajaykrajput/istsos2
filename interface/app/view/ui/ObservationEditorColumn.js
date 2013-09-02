/*
 * File: app/view/ui/ObservationEditorColumn.js
 * Date: Mon Sep 02 2013 10:49:22 GMT+0200 (CEST)
 *
 * This file was generated by Ext Designer version 1.2.3.
 * http://www.sencha.com/products/designer/
 *
 * This file will be auto-generated each and everytime you export.
 *
 * Do NOT hand edit this file.
 */

Ext.define('istsos.view.ui.ObservationEditorColumn', {
    extend: 'Ext.panel.Panel',

    border: 0,
    layout: {
        align: 'stretch',
        type: 'hbox'
    },
    title: '',

    initComponent: function() {
        var me = this;

        Ext.applyIf(me, {
            items: [
                {
                    xtype: 'panel',
                    id: 'chartContainer',
                    padding: '16px',
                    maintainFlex: true,
                    layout: {
                        type: 'fit'
                    },
                    title: '',
                    flex: 0.9
                },
                {
                    xtype: 'panel',
                    border: 0,
                    id: 'gridContainer',
                    width: 300,
                    maintainFlex: true,
                    layout: {
                        type: 'fit'
                    },
                    bodyPadding: '16px',
                    title: ''
                }
            ]
        });

        me.callParent(arguments);
    }
});