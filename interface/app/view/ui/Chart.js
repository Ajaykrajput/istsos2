/*
 * File: app/view/ui/Chart.js
 * Date: Mon Sep 02 2013 10:49:22 GMT+0200 (CEST)
 *
 * This file was generated by Ext Designer version 1.2.3.
 * http://www.sencha.com/products/designer/
 *
 * This file will be auto-generated each and everytime you export.
 *
 * Do NOT hand edit this file.
 */

Ext.define('istsos.view.ui.Chart', {
    extend: 'Ext.panel.Panel',
    requires: [
        'istsos.view.ProcedurePlotter',
        'istsos.view.ProcedureChooser'
    ],

    border: 0,
    height: 600,
    id: 'chartpanel',
    minHeight: 400,
    minWidth: 1130,
    autoScroll: true,
    layout: {
        type: 'border'
    },
    bodyStyle: 'background-color: white;',
    title: '',

    initComponent: function() {
        var me = this;

        Ext.applyIf(me, {
            items: [
                {
                    xtype: 'panel',
                    border: 0,
                    id: 'charttwo',
                    minWidth: 500,
                    layout: {
                        align: 'stretch',
                        type: 'vbox'
                    },
                    title: '',
                    region: 'center',
                    items: [
                        {
                            xtype: 'panel',
                            border: 0,
                            height: 150,
                            id: 'plotcalc',
                            activeItem: 0,
                            layout: {
                                type: 'card'
                            },
                            title: '',
                            items: [
                                {
                                    xtype: 'panel',
                                    border: 0,
                                    padding: '0px 5px 5px 5px ',
                                    title: '',
                                    items: [
                                        {
                                            xtype: 'fieldset',
                                            title: '2. Plot data',
                                            items: [
                                                {
                                                    xtype: 'procedureplotter',
                                                    id: 'plotdatafrm'
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    xtype: 'panel',
                                    border: 0,
                                    id: 'calccnt',
                                    padding: '9 10 0 10',
                                    layout: {
                                        type: 'fit'
                                    },
                                    title: ''
                                }
                            ]
                        },
                        {
                            xtype: 'panel',
                            border: 0,
                            html: '<div style=\'border-radius: 3px 3px 3px 3px !important; background-color: white; border: thin solid green; width: 100%; height: 100%;\' id=\'chartCnt\'></div>',
                            title: '',
                            flex: 0.7,
                            margins: '0 10 5 10'
                        },
                        {
                            xtype: 'panel',
                            border: 0,
                            height: 30,
                            padding: '0 10 5 10',
                            layout: {
                                align: 'middle',
                                padding: '0 10 5 10',
                                type: 'hbox'
                            },
                            title: '',
                            items: [
                                {
                                    xtype: 'button',
                                    id: 'btnRangeDay',
                                    enableToggle: true,
                                    text: 'Day',
                                    toggleGroup: 'timeline',
                                    flex: 1
                                },
                                {
                                    xtype: 'button',
                                    id: 'btnRangeWeek',
                                    enableToggle: true,
                                    text: 'Week',
                                    toggleGroup: 'timeline',
                                    flex: 1
                                },
                                {
                                    xtype: 'button',
                                    id: 'btnRangeAll',
                                    enableToggle: true,
                                    pressed: true,
                                    text: 'All',
                                    toggleGroup: 'timeline',
                                    flex: 1
                                }
                            ]
                        }
                    ]
                },
                {
                    xtype: 'panel',
                    border: 0,
                    id: 'chartthree',
                    minWidth: 350,
                    width: 350,
                    layout: {
                        align: 'stretch',
                        type: 'vbox'
                    },
                    collapsed: false,
                    region: 'east',
                    items: [
                        {
                            xtype: 'panel',
                            border: 0,
                            height: 105,
                            layout: {
                                type: 'fit'
                            },
                            title: '',
                            items: [
                                {
                                    xtype: 'form',
                                    border: 0,
                                    id: 'chartfilterFrm',
                                    bodyPadding: '0 10 5 0',
                                    collapseFirst: false,
                                    collapsed: false,
                                    title: '',
                                    items: [
                                        {
                                            xtype: 'fieldset',
                                            padding: 5,
                                            title: '3. Start editing',
                                            items: [
                                                {
                                                    xtype: 'combobox',
                                                    id: 'oeCbEditableProcedures',
                                                    name: 'procedure',
                                                    fieldLabel: 'Procedure',
                                                    labelWidth: 70,
                                                    displayField: 'name',
                                                    queryMode: 'local',
                                                    store: 'editableProcedure',
                                                    valueField: 'name',
                                                    anchor: '100%'
                                                },
                                                {
                                                    xtype: 'container',
                                                    height: 25,
                                                    layout: {
                                                        align: 'stretch',
                                                        type: 'hbox'
                                                    },
                                                    items: [
                                                        {
                                                            xtype: 'button',
                                                            hidden: true,
                                                            id: 'btnCancelEditor',
                                                            text: 'Cancel',
                                                            flex: 1
                                                        },
                                                        {
                                                            xtype: 'button',
                                                            id: 'btnStartEditor',
                                                            text: 'Start editing',
                                                            flex: 1
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            xtype: 'panel',
                            border: 0,
                            id: 'chartgridcnt',
                            layout: {
                                type: 'fit'
                            },
                            title: '',
                            flex: 1,
                            margins: '0 10 5 0'
                        }
                    ]
                },
                {
                    xtype: 'panel',
                    border: 0,
                    width: 300,
                    layout: {
                        type: 'fit'
                    },
                    title: '',
                    region: 'west',
                    items: [
                        {
                            xtype: 'fieldset',
                            padding: 5,
                            layout: {
                                type: 'fit'
                            },
                            title: '1. Choose procedure',
                            items: [
                                {
                                    xtype: 'procedurechooser',
                                    id: 'pchoose'
                                }
                            ]
                        }
                    ]
                }
            ]
        });

        me.callParent(arguments);
    }
});