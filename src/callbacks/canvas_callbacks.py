"""
Module: canvas_callbacks
Defines clientside callbacks for canvas (slide) management
"""
from dash import Input, Output, State

def canvas_callbacks(app):
    """
    Registers all clientside callbacks for canvas management:
      - creating new canvases from selected nodes
      - rendering tabs and canvas list
      - switching, renaming, deleting, duplicating canvases
      - clearing and splitting by clusters
    """
    # Create a new canvas from selected nodes
    app.clientside_callback(
        """
        function(nClicks, selectedNodes, store) {
            if (nClicks < 1) {
                return [window.dash_clientside.no_update, {'display': 'none'}, ''];
            }

            // Unpack store
            const full = (store && store.full) || [];
            const canvases = (store && store.canvases) || [];

            // Error: already 50 canvas 
            if (canvases.length >= 50) {
                return [
                    window.dash_clientside.no_update,
                    {'display': 'flex'},
                    'Вы достигли максимального количества холстов (50).'
                ];
            }

            // Error: no one selected nodes
            if (!selectedNodes || selectedNodes.length === 0) {
                return [
                    window.dash_clientside.no_update,
                    {'display': 'flex'},
                    'Чтобы создать холст, выберите в графе хотя бы одну вершину.'
                ];
            }

            // Error: >300 nodes
            if (selectedNodes.length > 300) {
                return [
                    window.dash_clientside.no_update,
                    {'display': 'flex'},
                    `Вы выбрали ${selectedNodes.length} вершин.\n` +
                    'Максимально допустимо — 300. Пожалуйста, сократите выбор.'
                ];
            }

            // Get ID selected nodes
            const selected = selectedNodes.slice(0, 300);
            const nodesIDs = selected.map(n => n.id);

            // Filter nodes & edges
            const nodes = full.filter(e => e.data && nodesIDs.includes(e.data.id)).map(e => ({ ...e }));
            const edges = full.filter(e => e.data && e.data.source
                            && nodesIDs.includes(e.data.source)
                            && nodesIDs.includes(e.data.target))
                            .map(e => ({ ...e }));

            // Save positions only for selected nodes
            const positions = {};
            nodes.forEach(n => {
                positions[n.id] = n.position;
            });

            // Create new object canvas
            const indx = store.nextCanvasIndex + 1;
            const newCanvas = {
                id: `canvas-${indx}`,
                name: `Холст ${indx}`,
                elements: nodes.concat(edges),
                positions: positions
            };

            return [
                {
                    full: full,
                    canvases: canvases.concat(newCanvas).slice(-50),
                    nextCanvasIndex: indx,
                }, 
                {
                    'display': 'none'
                },
                ''
            ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('canvas-error', 'style', allow_duplicate=True),
            Output('canvas-error', 'children', allow_duplicate=True)
        ],
        Input('create-new-canvas', 'n_clicks'),
        [
            State('network-graph', 'selectedNodeData'),
            State('canvas-store', 'data'),
        ],
        prevent_initial_call=True
    )

    # Build tabs and canvas list options
    app.clientside_callback(
        """
        function(store) {
            // create Tab object
            function makeTab(label, value) {
                return {
                    type: 'Tab',
                    namespace: 'dash_core_components',
                    props: { label: label, value: value }
                };
            }

            const slides = (store && store.canvases) || [];

            const tabs = [ makeTab('Полный граф', 'full') ];
            slides.forEach(c => {
                tabs.push(makeTab(c.name, c.id));
            });

            const options = [];
            const optionsOverlay = [];
            const allCanvases = [{ id: 'full', name: 'Полный граф' }].concat(slides);

            allCanvases.forEach(c => {
                // label
                options.push({
                    label: window.React.createElement(
                        'span', 
                        { className: 'canvas-list__label' }, 
                        c.name
                    ),
                    value: c.id + '-label',
                });

                // rename
                optionsOverlay.push({
                    label: window.React.createElement('img', {
                        src: '/assets/icons/rename.svg',
                        alt: 'rename',
                    }),
                    value: c.id + '-rename',
                });

                // delete
                optionsOverlay.push({
                    label: window.React.createElement('img', {
                        src: '/assets/icons/delete.svg',
                        alt: 'delete',
                    }),
                    value: c.id + '-delete',
                });

                // duplicate
                optionsOverlay.push({
                    label: window.React.createElement('img', {
                        src: '/assets/icons/duplicate.svg',
                        alt: 'duplicate',
                    }),
                    value: c.id + '-duplicate',
                });

            });

            return [tabs, options, optionsOverlay];
        }
        """,
        [
            Output('graph-tabs', 'children'),
            Output('canvas-list', 'options'),
            Output('canvas-list-action', 'options'),
        ],
        Input('canvas-store', 'data')
    )

    # Switching tabs
    app.clientside_callback(
        """
        function(newTab, store, currentElements, prevTab) {
            if (!store) {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update, window.dash_clientside.no_update];
            }

            if (prevTab) {
                if (prevTab === 'full') {
                    const newFullPos = {};
                    currentElements.forEach(el => {
                        if (el.data && el.data.id && el.position) {
                            newFullPos[el.data.id] = el.position;
                        }
                    });
                    store.fullPositions = newFullPos;
                } else {
                    const indx = store.canvases.findIndex(c => c.id === prevTab);
                    if (indx > -1) {
                        const pos = store.canvases[indx].positions || {};
                        currentElements.forEach(el => {
                            if (el.data && el.data.id && el.position) {
                                pos[el.data.id] = el.position;
                            }
                        });
                        store.canvases[indx].positions = pos;
                    }
                }
            }

            const listValue = `${newTab}-label`;

            return [store, newTab, listValue];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('active-canvas', 'data', allow_duplicate=True),
            Output('canvas-list', 'value'),
        ],
        Input('graph-tabs', 'value'),
        [
            State('canvas-store', 'data'),
            State('network-graph', 'elements'),
            State('active-canvas', 'data'),
        ],
        prevent_initial_call=True
    )

    # Render selected canvas elements
    app.clientside_callback(
        """
        function(activeID, store) {
            if (!store) {
                return window.dash_clientside.no_update;
            }

            // Return full graph
            if (activeID === 'full') {
                const fullCanvas = store.full || [];
                const fullPos = store.fullPositions || {};
                return fullCanvas.map(e => {
                    if (e.data && e.data.id && fullPos[e.data.id]) {
                        return {...e, position: fullPos[e.data.id]};
                    }
                    return e;
                });
            }

            // Search canvas
            const canvas = (store.canvases || []).find(s => s.id === activeID);
            if (!canvas) {
                return window.dash_clientside.no_update;
            }

            // For Cytoscape: return elements with positions
            return canvas.elements.map(e => {
                if (e.data && e.data.id && canvas.positions[e.data.id]) {
                    return { ...e, position: canvas.positions[e.data.id] };
                }
                return e;
            });
        }
        """,
        Output('network-graph', 'elements', allow_duplicate=True),
        Input('active-canvas', 'data'),
        State('canvas-store', 'data'),
        prevent_initial_call=True
    )

    # Switch to selected canvas by click on canvas-list item
    app.clientside_callback(
        """
        function(selectedValue) {
            if (!selectedValue) {
                return window.dash_clientside.no_update;
            }

            const indx = selectedValue.lastIndexOf('-');
            if (indx < 0) {
                return window.dash_clientside.no_update;
            }

            const canvasId = selectedValue.substring(0, indx);
            const action = selectedValue.substring(indx + 1);
            if (action !== 'label') {
                return window.dash_clientside.no_update;
            }
            return canvasId;
        }
        """,
        Output('graph-tabs', 'value', allow_duplicate=True),
        Input('canvas-list', 'value'),
        prevent_initial_call=True
    )

    # Handle rename/delete/duplicate actions
    app.clientside_callback(
        """
        function(selectedAction, store, activeId) {
            if (!selectedAction || !store || !store.canvases) {
                return [ window.dash_clientside.no_update, null, {'display': 'none'}, window.dash_clientside.no_update, window.dash_clientside.no_update ];
            }

            const indx = selectedAction.lastIndexOf('-');
            const canvasId = selectedAction.substring(0, indx);
            const action   = selectedAction.substring(indx + 1);

            const newStore = {
                full: store.full,
                fullPositions: store.fullPositions || {},
                canvases: store.canvases.map(c => ({ ...c })),
                nextCanvasIndex: store.nextCanvasIndex + 1,
            };

            let inputStyle = { display: 'none' };
            let inputValue = null;
            let newActive = window.dash_clientside.no_update;

            if (action === 'rename') {
                newStore.editingName = canvasId;

                const idx = store.canvases.findIndex(c=>c.id===canvasId) + 1;
                const topPx = (idx * 36) + 'px';

                inputValue = store.canvases.find(c=>c.id===canvasId)?.name || '';
                inputStyle = {
                    display: 'flex',
                    top: topPx,
                };

                window.setTimeout(() => {
                    const el = document.getElementById('rename-overlay-input');
                    if (el) { el.focus(); el.select(); }
                }, 0);
            } else if (action === 'delete') {
                newStore.canvases = newStore.canvases.filter(c => c.id !== canvasId);
                if (activeId === canvasId) {
                    newActive = 'full';
                }
            } else if (action === 'duplicate') {
                const orig = store.canvases.find(c => c.id === canvasId);
                if (orig && store.canvases.length < 50) {
                    const newIndx = newStore.nextCanvasIndex;
                    newStore.canvases.push({
                        id: `canvas-${newIndx}`,
                        name: `${orig.name} (копия)`,
                        elements: orig.elements,
                        positions: { ...orig.positions }
                    });
                    newStore.nextCanvasIndex = newIndx + 1;
                } else {
                    return [ window.dash_clientside.no_update, null, inputStyle, window.dash_clientside.no_update, newActive ];
                }
            } else {
                return [ window.dash_clientside.no_update, null, inputStyle, window.dash_clientside.no_update, newActive ];
            }

            return [ newStore, null, inputStyle, inputValue, newActive ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('canvas-list-action','value'),
            Output('rename-overlay', 'style'),
            Output('rename-overlay-input', 'value'),
            Output('graph-tabs', 'value', allow_duplicate=True),
        ],
        Input('canvas-list-action', 'value'),
        [
            State('canvas-store', 'data'),
            State('active-canvas', 'data'),
        ],
        prevent_initial_call=True
    )

    # Commit rename on submit
    app.clientside_callback(
        """
        function(nSubmit, nBlur, newName, store) {
            if (!store || !store.editingName) {
                return [ window.dash_clientside.no_update, window.dash_clientside.no_update ];
            }
            if (!(nSubmit > 0 || nBlur > 0)) {
                return [ window.dash_clientside.no_update, window.dash_clientside.no_update ];
            }

            if (!newName) {
                return [ window.dash_clientside.no_update, {'display': 'none'} ];
            }

            const id = store.editingName;
            const newStore = { ...store };
            newStore.canvases = newStore.canvases.map(c => {
                if (c.id === id) {
                    return { ...c, name: newName };
                }
                return c;
            });

            delete newStore.editingName;

            return [ newStore, {'display': 'none'} ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('rename-overlay', 'style', allow_duplicate=True),
        ],
        [
            Input('rename-overlay-input', 'n_submit'),
            Input('rename-overlay-input', 'n_blur'),
        ],
        [
            State('rename-overlay-input', 'value'),
            State('canvas-store', 'data'),
        ],
        prevent_initial_call=True
    )

    # Delete all canvases
    app.clientside_callback(
        """
        function(nClicks, store) {
            if (nClicks < 1 || !store) {
                return window.dash_clientside.no_update;
            }

            const newStore = {
                full: store.full,
                fullPositions: store.fullPositions || {},
                canvases: [],
                nextCanvasIndex: 0
            };

            return [ newStore, 'full' ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('graph-tabs', 'value', allow_duplicate=True)
        ],
        Input('delete-all-canvases', 'n_clicks'),
        State('canvas-store', 'data'),
        prevent_initial_call=True
    )

    # Split full graph into cluster canvases
    app.clientside_callback(
        """
        function(nClicks, store) {
            if (nClicks < 1 || !store || !store.full) {
                return window.dash_clientside.no_update;
            }

            const full = store.full;

            const clusters = Array.from(
                new Set(
                    full
                    .filter(el => el.data && el.data.cluster != null)
                    .map(el => el.data.cluster)
                )
            ).sort((a, b) => a - b);

            const newStore = {
                full: full,
                fullPositions: store.fullPositions || {},
                canvases: [],
                nextCanvasIndex: 0
            };

            const maxCanvases = 50;
            for (let i = 0; i < clusters.length && newStore.canvases.length < maxCanvases; i++) {
                const cl = clusters[i];

                const nodes = full.filter(e => e.data && e.data.cluster === cl).map(e => ({ ...e }));

                const edges = full.filter(e => e.data && e.data.source != null)
                            .filter(e =>
                                nodes.some(n => n.data.id === e.data.source) &&
                                nodes.some(n => n.data.id === e.data.target)
                            )
                            .map(e => ({ ...e }));

                newStore.canvases.push({
                    id: `canvas-${newStore.nextCanvasIndex}`,
                    name: `Кластер ${cl}`,
                    elements: nodes.concat(edges),
                    positions: {},
                });
                newStore.nextCanvasIndex++;
            }

            return [ newStore, 'full' ];
        }
        """,
        [
            Output('canvas-store', 'data', allow_duplicate=True),
            Output('graph-tabs', 'value', allow_duplicate=True)
        ],
        Input('split-by-clusters', 'n_clicks'),
        State('canvas-store', 'data'),
        prevent_initial_call=True
    )
