# Motile Tracker Repository Map

**Generated:** 2026-01-13

---

## Project Overview

**Motile Tracker** is an interactive tracking application built as a napari plugin that leverages the motile library for solving tracking problems using Integer Linear Programming (ILP). It enables users to track objects across 2D+time and 3D+time image sequences with global optimization.

### Key Information
- **Project Name:** motile-tracker
- **Version:** Dynamic (setuptools-scm)
- **License:** BSD 3-Clause
- **Python Requirements:** >=3.11
- **Status:** Production/Stable
- **Primary Author:** Caroline Malin-Mayor (malinmayorc@janelia.hhmi.org)
- **Repository:** https://github.com/funkelab/motile_tracker
- **Documentation:** https://funkelab.github.io/motile_tracker/

### What It Does
- Interactive cell/object tracking with global optimization
- Support for both segmentation-based and point-based tracking
- Support for 2D, 3D data with time dimension
- Interactive editing of tracking results
- Multiple solving modes (full dataset, chunked/windowed solving)
- Track visualization with lineage trees
- Import/export of tracking data (CSV, GEFF formats)
- Optional GPU acceleration via Gurobi solver

---

## Repository Structure

```
motile_tracker/
├── src/motile_tracker/           # Main application code (~9,000 lines)
│   ├── application_menus/        # Main UI widgets and menus
│   ├── data_views/              # Visualization and data coordination
│   ├── motile/                  # Tracking solver backend
│   ├── import_export/           # Data import/export functionality
│   ├── example_data.py          # Sample datasets loader
│   ├── launcher.py              # Entry point for napari integration
│   └── napari.yaml              # Napari plugin manifest
│
├── tests/                        # Test suite
│   ├── motile/                  # Solver and menu tests
│   └── import_export/           # Import/export tests
│
├── docs/                         # Sphinx documentation
│   └── source/
│       ├── getting_started.rst
│       ├── editing.rst
│       ├── tree_view.rst
│       └── motile.rst
│
├── scripts/                      # Example scripts
│   ├── run_hela.py
│   ├── load_external_points.py
│   └── view_external_tracks.py
│
├── pyproject.toml               # Project configuration
├── README.md                    # User documentation
├── DEVELOPER.md                 # Developer guide
├── justfile                     # Common tasks (test, start, docs)
└── uv.lock                      # Dependency lock file
```

---

## Architecture Overview

The application follows a **modular, layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│       UI Layer (Qt Widgets)             │
│  - MenuWidget, TreeWidget, EditingMenu  │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│   Data Coordination Layer               │
│  - TracksViewer (Singleton)             │
│  - Signal/Slot connections (psygnal)    │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│   Visualization Layer                   │
│  - Napari layers (Points, Labels, Graph)│
│  - Tree view, Ortho views               │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│   Backend/Solver Layer                  │
│  - Motile ILP solver                    │
│  - NetworkX graphs                      │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│   External Libraries                    │
│  - motile_toolbox, funtracks            │
└─────────────────────────────────────────┘
```

---

## Deep Dive: Core Source Folders

This section provides comprehensive file-by-file documentation of every module in the source code. Each entry includes:
- File path and line count
- Class/function names and purposes
- Key methods and attributes
- Signals emitted (for Qt components)
- Design patterns used
- Relationships with other components

Stars (⭐) indicate particularly important files that are central to the application's functionality.

### Quick Navigation

1. **[Application Menus](#1-application-menus-srcmotile_trackerapplication_menus)** - Top-level UI (5 files, 411 lines)
   - MainApp, MenuWidget, EditingMenu, VisualizationWidget

2. **[Data Views](#2-data-views-srcmotile_trackerdata_views)** - Visualization & coordination (33 files, 6,087 lines)
   - A. Views Coordinator: TracksViewer ⭐, TracksList, NodeSelectionList, Groups
   - B. Views: Layers (Points, Labels, Graph), Tree View, Ortho Views
   - C. Graph Attributes

3. **[Motile Backend](#3-motile-backend-srcmotile_trackermotile)** - Solver & parameters (11 files, 2,004 lines)
   - A. Backend: solve() ⭐, SolverParams ⭐, MotileRun
   - B. Menus: RunEditor ⭐, ParamsEditor, RunViewer

4. **[Import/Export](#4-importexport-srcmotile_trackerimport_export)** - Data I/O (11 files, 1,795 lines)
   - ImportDialog ⭐, ExportDialog, CSV/GEFF widgets, Scale configuration

5. **[Other Root Files](#5-other-root-files)** - Entry points & utilities
   - example_data.py, launcher.py, napari.yaml, \_\_init\_\_.py, \_\_main\_\_.py

### 1. Application Menus ([src/motile_tracker/application_menus/](src/motile_tracker/application_menus/))

**Purpose:** Main UI orchestration and menu management
**Size:** 5 files, ~411 lines of code

This folder contains the top-level UI components that users interact with directly.

#### Files:

##### [main_app.py](src/motile_tracker/application_menus/main_app.py) (28 lines)
**Class:** `MainApp(QWidget)`

The root application widget that combines all tracker widgets for faster dock arrangement.

**Key responsibilities:**
- Instantiates `MenuWidget` (main control panel)
- Instantiates `TreeWidget` (lineage tree view)
- Adds TreeWidget as a dock widget at the bottom of the napari viewer
- Initializes orthogonal views for 3D data visualization
- Sets up the main vertical layout

**Usage:** This is the main entry point widget registered as a napari plugin command.

##### [menu_widget.py](src/motile_tracker/application_menus/menu_widget.py) (~150 lines)
**Class:** `MenuWidget(QTabWidget)`

The primary tabbed interface containing all tracking functionality.

**Tabs provided:**
1. **Tracking Tab** - Contains `MotileWidget` for running tracking solver
2. **Tracks List Tab** - Contains `TracksList` for viewing all tracks
3. **Edit Tracks Tab** - Contains `EditingMenu` for interactive editing
4. **Groups Tab** - Contains `CollectionWidget` for organizing tracks
5. **Visualization Tab** - Contains `LabelVisualizationWidget` for display settings

**Key features:**
- Manages tab switching and layout
- Connects TracksViewer signals to update UI state
- Handles import/export dialogs
- Provides centralized access to all tracking operations

##### [editing_menu.py](src/motile_tracker/application_menus/editing_menu.py) (~150 lines)
**Class:** `EditingMenu(QWidget)`

Interactive track editing interface with buttons for all editing operations.

**Node Operations:**
- **Start New Track** - Creates new track from selected node
- **Delete Node** - Removes selected node(s) from tracking graph
- **Swap Node Label** - Changes segmentation label of selected node

**Edge Operations:**
- **Break Selected Edge** - Splits track by removing edge
- **Add Edge** - Creates new edge between two selected nodes

**Track Operations:**
- **View Track ID** - Displays current track ID for selected node
- **Set Track ID** - Manually assigns track ID to selected nodes

**Key features:**
- Force mode toggle for operations that would otherwise be invalid
- Connects to TracksViewer for state management
- Provides user confirmation dialogs for destructive operations
- Updates visualization immediately after edits

##### [visualization_widget.py](src/motile_tracker/application_menus/visualization_widget.py) (~80 lines)
**Class:** `LabelVisualizationWidget(QWidget)`

Controls for customizing how track labels are displayed.

**Key features:**
- Dropdown to select which label layer to visualize
- Options for contour display
- Color/opacity controls
- Connects to TrackLabels layer for live updates

**Public exports (\_\_init\_\_.py):**
- `MainApp` - Primary application widget
- `EditingMenu` - Track editing interface
- `MenuWidget` - Tabbed menu container

### 2. Data Views ([src/motile_tracker/data_views/](src/motile_tracker/data_views/))

**Purpose:** Data visualization, coordination, and state management
**Size:** 33 files, ~6,087 lines of code (largest module)

This is the core of the application, handling all data coordination, visualization, and user interactions. It's organized into three main subfolders: `views_coordinator/`, `views/`, and `_tests/`.

#### A. Views Coordinator ([src/motile_tracker/data_views/views_coordinator/](src/motile_tracker/data_views/views_coordinator/))

**Purpose:** Central state management and signal routing using psygnal

This subfolder implements the coordinator/controller pattern, with TracksViewer as the central singleton.

##### [tracks_viewer.py](src/motile_tracker/data_views/views_coordinator/tracks_viewer.py) (~600 lines) ⭐ **CORE CLASS**
**Class:** `TracksViewer` (Singleton)

The heart of the application - coordinates all state and communication between components.

**Signals emitted:**
- `tracks_updated(Optional[bool])` - Emitted when track data changes
- `update_track_id()` - Emitted when track ID needs updating
- `mode_updated()` - Emitted when display mode changes
- `center_node(int)` - Emitted to center view on a node

**Key attributes:**
- `viewer: napari.Viewer` - Reference to napari viewer
- `tracks: SolutionTracks | None` - Current tracking solution
- `colormap` - napari colormap for track visualization
- `symbolmap: dict[NodeType, str]` - Symbol mapping for different node types (END: "x", CONTINUE: "disc", SPLIT: "triangle_up")
- `mode: str` - Current display mode ("all", "selected", "track")
- `visible: list | str` - Currently visible tracks
- `tracking_layers: TracksLayerGroup` - Manages all napari layers
- `selected_nodes: NodeSelectionList` - Currently selected nodes
- `tracks_list: TracksList` - List of all tracks
- `collection_widget: CollectionWidget` - Track collections/groups

**Key methods:**
- `get_instance(viewer)` - Singleton accessor
- `request_new_track()` - Request new track ID
- `update_tracks(mode, visible)` - Update displayed tracks
- `update_selection()` - Update visualization based on selection
- `delete_node(node_id, force)` - Delete node from graph
- `add_edge(source, target)` - Add edge between nodes
- `swap_node_label(node_id, new_label)` - Change node segmentation label

**Design pattern:** Singleton ensuring single source of truth for application state

##### [tracks_list.py](src/motile_tracker/data_views/views_coordinator/tracks_list.py) (~150 lines)
**Class:** `TracksList(QWidget)`

Widget displaying a list of all tracks in the current solution.

**Signals:**
- `view_tracks(str, list)` - Emitted when user selects tracks to view

**Features:**
- List view of all track IDs
- Multi-selection support
- Buttons to view all/selected tracks
- Auto-updates when tracks change

##### [node_selection_list.py](src/motile_tracker/data_views/views_coordinator/node_selection_list.py) (~100 lines)
**Class:** `NodeSelectionList`

Manages the list of currently selected nodes.

**Signals:**
- `list_updated()` - Emitted when selection changes

**Key methods:**
- `add_node(node_id)` - Add node to selection
- `remove_node(node_id)` - Remove node from selection
- `clear()` - Clear selection
- `toggle_node(node_id)` - Toggle node selection

**Features:**
- Multi-node selection support
- Maintains selection order
- Prevents duplicates

##### [groups.py](src/motile_tracker/data_views/views_coordinator/groups.py) (~250 lines)
**Class:** `CollectionWidget(QWidget)`

Organize tracks into named collections/groups for analysis.

**Features:**
- Create/delete collections
- Add/remove tracks from collections
- View specific collections
- Save/load collections with track solution

**Use case:** Group tracks by cell type, experimental condition, or analysis category

##### [key_binds.py](src/motile_tracker/data_views/views_coordinator/key_binds.py) (~80 lines)

Defines all keyboard shortcuts for the application.

**Key bindings defined:**
- `Q` - Toggle display mode (all/selected/track)
- Click - Select node
- Shift+Click - Append to selection
- Ctrl/Cmd+Click - Center on node
- Custom keybinds for track editing operations

**Key function:**
- `bind_keymap(viewer, keymap, tracks_viewer)` - Registers keybinds with napari

##### [user_dialogs.py](src/motile_tracker/data_views/views_coordinator/user_dialogs.py) (~50 lines)

Modal confirmation dialogs for user actions.

**Functions:**
- `confirm_force_operation(operation_name)` - Confirm potentially destructive operations
- Custom dialog builders for various user confirmations

**Usage:** Prevents accidental data loss from destructive operations

#### B. Views ([src/motile_tracker/data_views/views/](src/motile_tracker/data_views/views/))

**Purpose:** UI components and napari layer management

This subfolder contains all visualization components: napari layer wrappers, tree view widgets, and orthogonal views for 3D data.

##### Layers ([src/motile_tracker/data_views/views/layers/](src/motile_tracker/data_views/views/layers/))

Custom napari layer classes that wrap and extend napari's built-in layers with tracking-specific functionality.

###### [tracks_layer_group.py](src/motile_tracker/data_views/views/layers/tracks_layer_group.py) (~200 lines) ⭐
**Class:** `TracksLayerGroup`

Factory and manager for all tracking-related napari layers.

**Managed layers:**
- `tracks_layer: TrackGraph | None` - Edges between nodes
- `points_layer: TrackPoints | None` - Node positions
- `seg_layer: TrackLabels | None` - Segmentation masks

**Key methods:**
- `set_tracks(tracks, name)` - Create/update all layers from track data
- `add_napari_layers()` - Add layers to napari viewer
- `remove_napari_layers()` - Clean up layers
- `center_view(node_id)` - Center camera on specific node
- `link_clipping_planes()` - Synchronize clipping planes between layers (for 3D)

**Purpose:** Centralized layer lifecycle management

###### [track_points.py](src/motile_tracker/data_views/views/layers/track_points.py) (~400 lines)
**Class:** `TrackPoints` (inherits napari.layers.Points)

Points layer displaying node positions with track-specific styling.

**Features:**
- Color nodes by track ID using TracksViewer colormap
- Symbol shapes based on node type (end/continue/split)
- Size based on node area/radius
- Face color for selection highlighting
- Click handlers for node selection
- Time-based visibility (shows nodes in current timeframe)

**Styling:**
- Selected nodes: highlighted with different color
- Node types: different symbols (x, disc, triangle)
- Track colors: from colormap for easy visual tracking

###### [track_labels.py](src/motile_tracker/data_views/views/layers/track_labels.py) (~500 lines)
**Class:** `TrackLabels` (inherits napari.layers.Labels)

Labels layer displaying segmentation masks with track coloring.

**Features:**
- Color segmentation by track ID
- Support for both 2D and 3D data
- Lazy loading for large datasets (uses dask)
- Dynamic relabeling on-the-fly
- Paint mode for manual corrections
- Click handlers for node selection from segmentation

**Key methods:**
- `get_value(coords)` - Get track ID at coordinates
- `on_paint(event)` - Handle manual segmentation edits
- `_relabel_segmentation()` - Color by track ID instead of segmentation ID

**Use case:** Visualize tracking results overlaid on original segmentation

###### [track_graph.py](src/motile_tracker/data_views/views/layers/track_graph.py) (~300 lines)
**Class:** `TrackGraph` (inherits napari.layers.Shapes)

Shapes layer displaying edges between tracked objects.

**Features:**
- Draws lines between parent and child nodes
- Color edges by track ID
- Time-based visibility (shows only edges relevant to current time)
- Click handlers for edge selection
- Support for 2D and 3D visualization

**Rendering:**
- Edges rendered as napari shapes (lines/paths)
- Color matches track color from colormap
- Thickness adjustable

**Purpose:** Visualize temporal connections and lineage relationships

###### [contour_labels.py](src/motile_tracker/data_views/views/layers/contour_labels.py) (~200 lines)
**Class:** `ContourLabels` (inherits napari.layers.Shapes)

Shapes layer for displaying label contours instead of filled masks.

**Features:**
- Extract contours from label masks
- Display as outlines/borders
- More efficient for overlapping objects
- Track-based coloring

**Use case:** Alternative visualization when filled masks are too cluttered

###### [click_utils.py](src/motile_tracker/data_views/views/layers/click_utils.py) (~100 lines)

Utility functions for handling mouse clicks on layers.

**Key functions:**
- `get_node_id_from_click(coords, tracks, layer_type)` - Determine which node was clicked
- `handle_selection_click(node_id, modifiers)` - Apply selection based on keyboard modifiers
- `handle_center_click(node_id)` - Center view on clicked node

**Click behavior:**
- Click: Select single node
- Shift+Click: Append to selection
- Ctrl/Cmd+Click: Center view on node

##### Tree View ([src/motile_tracker/data_views/views/tree_view/](src/motile_tracker/data_views/views/tree_view/))

Lineage tree visualization using pyqtgraph for displaying track hierarchies over time.

###### [tree_widget.py](src/motile_tracker/data_views/views/tree_view/tree_widget.py) (~800 lines) ⭐
**Class:** `TreeWidget(QWidget)`, `CustomViewBox(pg.ViewBox)`

The main lineage tree visualization widget using pyqtgraph.

**Features:**
- Hierarchical tree layout showing parent-child relationships
- Time on X-axis, tracks on Y-axis
- Color-coded by track ID
- Interactive node selection (click, shift-drag rectangle selection)
- Zoom/pan controls
- Feature-based coloring (color nodes by custom features)
- Navigation controls for centering and zooming

**Key components:**
- `CustomViewBox` - Extended pyqtgraph ViewBox with rectangle selection
- `PlotWidget` - pyqtgraph plot with custom interaction
- Connected to TracksViewer for state synchronization

**Purpose:** Provide overview of entire lineage structure

###### [tree_widget_utils.py](src/motile_tracker/data_views/views/tree_view/tree_widget_utils.py) (~300 lines)

Utility functions for tree view operations.

**Key functions:**
- `extract_lineage_tree(tracks)` - Extract tree structure from tracking graph
- `extract_sorted_tracks(tracks)` - Sort tracks for display
- `get_features_from_tracks(tracks)` - Extract feature data for coloring
- `compute_tree_layout(tree)` - Calculate node positions for tree display

###### [tree_view_mode_widget.py](src/motile_tracker/data_views/views/tree_view/tree_view_mode_widget.py) (~100 lines)
**Class:** `TreeViewModeWidget(QWidget)`

Controls for selecting tree view display mode.

**Modes:**
- View all tracks
- View selected tracks only
- View specific track

###### [tree_view_feature_widget.py](src/motile_tracker/data_views/views/tree_view/tree_view_feature_widget.py) (~150 lines)
**Class:** `TreeViewFeatureWidget(QWidget)`

Controls for coloring tree nodes by feature values.

**Features:**
- Dropdown to select feature (area, speed, custom attributes)
- Colormap selection
- Value range adjustment

**Purpose:** Visualize quantitative features across lineages

###### [flip_axes_widget.py](src/motile_tracker/data_views/views/tree_view/flip_axes_widget.py) (~50 lines)
**Class:** `FlipTreeWidget(QWidget)`

Simple controls for flipping tree display axes.

**Options:**
- Swap time and track axes
- Invert axis directions

###### [navigation_widget.py](src/motile_tracker/data_views/views/tree_view/navigation_widget.py) (~100 lines)
**Class:** `NavigationWidget(QWidget)`

Navigation controls for tree view.

**Features:**
- Center on selected node
- Zoom to fit all
- Zoom to fit selection
- Manual zoom controls

##### Orthogonal Views ([src/motile_tracker/data_views/views/ortho_views.py](src/motile_tracker/data_views/views/ortho_views.py)) (~200 lines)

**Function:** `initialize_ortho_views(viewer)`

Sets up orthogonal view sliders for 3D data visualization using napari-orthogonal-views plugin.

**Features:**
- XY, XZ, YZ slice views
- Synchronized navigation
- Clipping plane controls
- 3D volume rendering support

**Purpose:** Navigate 3D tracking data more easily

#### C. Other Files

##### [graph_attributes.py](src/motile_tracker/data_views/graph_attributes.py) (25 lines)

Defines enums for node and edge attributes in the tracking graph.

**Enums:**
- `NodeAttr`: POS, TIME, SEG_ID, SEG_HYPO, TRACK_ID, AREA
- `EdgeAttr`: IOU

**Purpose:** Standardize attribute names across the application

### 3. Motile Backend ([src/motile_tracker/motile/](src/motile_tracker/motile/))

**Purpose:** Solver configuration, execution, and result management
**Size:** 11 files, ~2,004 lines of code

This module handles the core tracking algorithm using the motile library (ILP-based optimization).

#### A. Backend ([src/motile_tracker/motile/backend/](src/motile_tracker/motile/backend/))

**Purpose:** Core solving logic and parameter management

##### [solve.py](src/motile_tracker/motile/backend/solve.py) (~600 lines) ⭐ **CORE ALGORITHM**

The main solving pipeline that coordinates graph construction, solver setup, and optimization.

**Main function:** `solve(segmentation, solver_params) -> nx.DiGraph`

**Solving pipeline:**

1. **Build Candidate Graph**
   - Uses `motile_toolbox` to extract nodes from segmentation
   - Each segmentation label becomes a candidate node
   - Edges created between nodes within `max_edge_distance`
   - Attributes computed: position, area, time, IOU

2. **Choose Solving Strategy**
   - `_solve_full()` - Solve entire dataset at once (smaller datasets)
   - `_solve_chunked()` - Solve in windows (large datasets)

3. **Construct ILP Solver**
   - Function: `construct_solver(graph, params)`
   - Add constraints:
     - Max children per node (division constraint)
     - Flow conservation (one track per object)
   - Add costs:
     - Edge selection cost (negative to encourage connections)
     - Appear cost (penalize new tracks)
     - Division cost (penalize splits)
     - Distance cost (prefer closer objects)
     - IOU cost (prefer overlapping objects)

4. **Solve ILP**
   - Uses motile library with Gurobi or open-source solver
   - Returns selected nodes and edges
   - Assigns track IDs to connected components

5. **Return Solution**
   - Solution as networkx DiGraph with selected edges
   - Node attributes: pos, time, seg_id, track_id, area
   - Edge attributes: iou

**Key functions:**
- `build_candidate_graph(segmentation, params)` - Extract nodes and edges
- `_solve_full(graph, params)` - Global optimization
- `_solve_chunked(graph, params, window_size, overlap)` - Windowed solving
- `construct_solver(graph, params)` - Build ILP with costs/constraints

**Chunked solving:** For large datasets, solve in overlapping windows. Previous window solutions are "pinned" in overlap regions to maintain consistency.

##### [solver_params.py](src/motile_tracker/motile/backend/solver_params.py) (~91 lines) ⭐
**Class:** `SolverParams(BaseModel)` - Pydantic model

Defines all solver parameters with validation, defaults, and descriptions.

**Parameters:**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_edge_distance` | 50.0 | Max distance objects can move between frames |
| `max_children` | 2 | Max divisions per object (1=no division, 2=binary division) |
| `edge_selection_cost` | -20.0 | Cost for selecting an edge (negative encourages edges) |
| `appear_cost` | 30.0 | Cost for starting new track (higher = fewer, longer tracks) |
| `division_cost` | 20.0 | Cost for division (higher = fewer divisions) |
| `distance_cost` | 1.0 | Multiplier for distance-based edge cost |
| `iou_cost` | -5.0 | Multiplier for IOU-based edge cost (negative = prefer overlap) |
| `window_size` | None | Frames per window for chunked solving |
| `overlap_size` | None | Overlap between windows |
| `single_window_start` | None | Test on single window starting at frame N |

**Validation:**
- `window_size` must be >= 2 if set
- `overlap_size` must be >= 1 if set
- `overlap_size` must be < `window_size`

**Purpose:** Type-safe, validated configuration with automatic UI generation

##### [motile_run.py](src/motile_tracker/motile/backend/motile_run.py) (~400 lines)
**Class:** `MotileRun` (inherits `funtracks.SolutionTracks`)

Container for a complete tracking run with parameters, results, and metadata.

**Attributes:**
- `graph: nx.DiGraph` - Solution graph with selected tracks
- `segmentation: np.ndarray` - Input segmentation
- `solver_params: SolverParams` - Parameters used for this run
- `scale: tuple` - Spatial scale (for physical units)
- `time: list` - Timestamp per frame
- `run_name: str` - User-assigned name
- `run_time: datetime` - When the run was created

**Key methods:**
- `save(filepath)` - Serialize run to disk (graph + params + metadata)
- `load(filepath)` - Deserialize from disk
- `to_csv(filepath)` - Export tracks to CSV format
- `compute_features()` - Calculate track statistics (length, speed, etc.)

**Inheritance:** Extends `funtracks.SolutionTracks` which provides:
- `TracksController` for graph editing operations
- Track ID assignment and management
- Node type detection (end, continue, split)

**Purpose:** Persistent storage of complete tracking runs for reproducibility

#### B. Menus ([src/motile_tracker/motile/menus/](src/motile_tracker/motile/menus/))

**Purpose:** UI components for solver interaction

##### [motile_widget.py](src/motile_tracker/motile/menus/motile_widget.py) (~200 lines)
**Class:** `MotileWidget(QWidget)`

Main tracking control widget that contains `RunEditor` and `RunViewer`.

**Structure:**
- **Top section:** `RunEditor` for creating new runs
- **Bottom section:** `RunViewer` for viewing/loading existing runs

**Features:**
- Tab interface switching between editor and viewer
- Connects `start_run` signal to initiate solving
- Progress indication during solving
- Error handling and user feedback

##### [run_editor.py](src/motile_tracker/motile/menus/run_editor.py) (~350 lines) ⭐
**Class:** `RunEditor(QGroupBox)`

Widget for configuring parameters and starting tracking runs.

**Components:**
1. **Run Name Field** - User-assigned name for the run
2. **Layer Selection** - Dropdown to select input segmentation/points layer
3. **Solver Parameters Editor** - `SolverParamsEditor` widget
4. **Run Tracking Button** - Initiates solving

**Signal:** `start_run(MotileRun)` - Emitted when solving completes

**Process:**
1. User selects input layer from napari
2. User configures parameters via `SolverParamsEditor`
3. User clicks "Run Tracking"
4. Widget calls `solve()` with segmentation and parameters
5. Progress bar shown during solving
6. On completion, emits `start_run` signal with `MotileRun` object
7. TracksViewer receives run and displays results

**Validation:**
- Ensures segmentation layer is selected
- Validates all parameters via Pydantic
- Shows warnings for large datasets

##### [params_editor.py](src/motile_tracker/motile/menus/params_editor.py) (~300 lines)
**Class:** `SolverParamsEditor(QWidget)`

Auto-generates UI from `SolverParams` Pydantic model.

**Features:**
- Introspects Pydantic model fields
- Creates appropriate widget for each parameter type:
  - `QSpinBox` for integers
  - `QDoubleSpinBox` for floats
  - `QCheckBox` for booleans
  - `QComboBox` for enums
- Shows field descriptions as tooltips
- Live validation as user types
- Reset to defaults button

**Key method:**
- `get_params() -> SolverParams` - Extract current parameter values

**Purpose:** Automatic UI generation reduces code duplication and keeps UI in sync with parameters

##### [run_viewer.py](src/motile_tracker/motile/menus/run_viewer.py) (~250 lines)
**Class:** `RunViewer(QGroupBox)`

Widget for viewing and loading existing tracking runs.

**Features:**
- List of available runs (from saved files or current session)
- View parameters for each run
- Load run to display in napari
- Delete saved runs
- Export runs to CSV

**Signals:**
- `load_run(MotileRun)` - Emitted when user loads a run

##### [params_viewer.py](src/motile_tracker/motile/menus/params_viewer.py) (~150 lines)
**Class:** `ParamsViewer(QWidget)`

Read-only display of solver parameters.

**Features:**
- Shows parameter names, values, and descriptions
- Formatted display with units
- Comparison view (compare parameters between runs)

**Purpose:** Inspect parameters of completed runs for reproducibility

##### [param_values.py](src/motile_tracker/motile/menus/param_values.py) (~100 lines)

Utility functions for parameter value conversion and formatting.

**Functions:**
- `format_param_value(value, param_name)` - Format for display (add units, round)
- `parse_param_value(string, param_type)` - Parse user input
- `validate_param_value(value, param_model)` - Check validity

**Purpose:** Centralized parameter handling logic

**Public exports (\_\_init\_\_.py):**
- `MotileRun` - Tracking run container
- `SolverParams` - Parameter model
- `solve` - Main solving function

### 4. Import/Export ([src/motile_tracker/import_export/](src/motile_tracker/import_export/))

**Purpose:** Data ingestion and output
**Size:** 11 files, ~1,795 lines of code

This module handles importing external tracking data and exporting tracking results.

#### Menus ([src/motile_tracker/import_export/menus/](src/motile_tracker/import_export/menus/))

All UI components for import/export workflows.

##### [import_dialog.py](src/motile_tracker/import_export/menus/import_dialog.py) (~300 lines) ⭐
**Class:** `ImportDialog(QDialog)`

Main import orchestrator dialog with tabbed interface.

**Tabs:**
1. **CSV Import** - Import tracking data from CSV files
2. **GEFF Import** - Import from GEFF (Graph Exchange File Format)
3. **Segmentation** - Import from napari Labels layer

**Workflow:**
1. User selects import format
2. User maps columns/fields to track attributes
3. User configures spatial scale
4. Dialog validates and imports data
5. Creates `MotileRun` or `SolutionTracks` object
6. Displays in TracksViewer

**Features:**
- Format auto-detection
- Preview before import
- Error validation
- Progress indication

##### [export_dialog.py](src/motile_tracker/import_export/menus/export_dialog.py) (~200 lines)
**Class:** `ExportDialog(QDialog)`

Main export orchestrator dialog.

**Export formats:**
1. **CSV** - Export tracks to CSV with configurable columns
2. **Napari Layers** - Export as Labels layer
3. **GEFF** - Export to Graph Exchange File Format

**Features:**
- Column selection for CSV export
- Format configuration
- File path selection
- Export validation

##### [csv_import_widget.py](src/motile_tracker/import_export/menus/csv_import_widget.py) (~300 lines)
**Class:** `CSVImportWidget(QWidget)`

Widget for importing tracking data from CSV files.

**CSV Format Expected:**
```
track_id,t,z,y,x,area,parent_id,...
0,0,10,50,100,250,,
0,1,12,52,103,255,,
1,0,20,150,200,300,,
```

**Features:**
- Column mapping (map CSV columns to track attributes)
- Delimiter detection (comma, tab, semicolon)
- Header detection
- Preview table
- Validation (check required columns, data types)

**Required columns:**
- Track ID
- Time
- Position (y, x for 2D; z, y, x for 3D)

**Optional columns:**
- Area, parent_id, custom features

##### [csv_dimension_widget.py](src/motile_tracker/import_export/menus/csv_dimension_widget.py) (~150 lines)
**Class:** `CSVDimensionWidget(QWidget)`

Widget for mapping CSV columns to spatial dimensions.

**Features:**
- Dropdown for each dimension (t, z, y, x)
- Auto-detection based on column names
- Validation of dimension completeness

**Purpose:** Handle CSV files with different column orderings

##### [geff_import_widget.py](src/motile_tracker/import_export/menus/geff_import_widget.py) (~250 lines)
**Class:** `GEFFImportWidget(QWidget)`

Widget for importing from GEFF format.

**GEFF Format:** XML-based graph exchange format from Cell Tracking Challenge
- Contains nodes (detections) and edges (links)
- Supports divisions and merges
- Includes segmentation references

**Features:**
- Parse XML structure
- Extract node positions and features
- Extract edge connections
- Load associated segmentation images
- Convert to MotileRun format

##### [geff_import_utils.py](src/motile_tracker/import_export/menus/geff_import_utils.py) (~200 lines)

Utility functions for parsing GEFF XML format.

**Key functions:**
- `parse_geff_xml(filepath)` - Parse GEFF XML file
- `extract_nodes(xml_tree)` - Extract node information
- `extract_edges(xml_tree)` - Extract edge connections
- `build_graph(nodes, edges)` - Construct networkx graph
- `load_geff_segmentation(folder)` - Load associated TIFF segmentation

**Purpose:** Separate parsing logic from UI code

##### [segmentation_widgets.py](src/motile_tracker/import_export/menus/segmentation_widgets.py) (~250 lines)
**Classes:** Multiple widgets for segmentation input

Widgets for importing tracking data from napari segmentation layers.

**Widgets:**
- `SegmentationLayerSelector(QWidget)` - Select Labels layer
- `SegmentationImporter(QWidget)` - Import and validate segmentation
- `SegmentationConverter(QWidget)` - Convert segmentation to tracks

**Features:**
- Layer validation (check dimensions, data type)
- Time series detection
- Auto-extract nodes from segmentation
- Create initial track IDs

**Use case:** Start tracking from existing segmentation without running solver

##### [prop_map_widget.py](src/motile_tracker/import_export/menus/prop_map_widget.py) (~200 lines)
**Class:** `PropertyMappingWidget(QWidget)`

Widget for mapping imported properties to track features.

**Features:**
- Map custom CSV columns to standard attributes
- Type conversion (string to float, int)
- Unit conversion (pixels to microns)
- Feature normalization

**Example:** Map CSV column "cell_area_pixels" to attribute "area" with conversion factor

##### [scale_widget.py](src/motile_tracker/import_export/menus/scale_widget.py) (~100 lines)
**Class:** `ScaleWidget(QWidget)`

Widget for configuring spatial/temporal scale.

**Inputs:**
- Pixel size in microns (Z, Y, X)
- Time interval (seconds per frame)
- Units (µm, nm, etc.)

**Purpose:** Convert pixel coordinates to physical units for accurate measurements

**Public exports (\_\_init\_\_.py):**
- `ImportDialog` - Main import dialog

**Supported Formats:**
- **CSV** - Custom format with flexible column mapping
- **GEFF** - XML-based graph format from Cell Tracking Challenge
- **Napari Labels** - Direct import from segmentation layers

### 5. Other Root Files

#### [example_data.py](src/motile_tracker/example_data.py) (~200 lines)

Provides sample datasets for demonstration and testing.

**Available Datasets:**

##### `Mouse_Embryo_Membrane()`
- 3D membrane tracking dataset
- Downloads from Zenodo (auto-cached)
- Dimensions: 3D+time
- ~50 MB download
- Use case: Demonstrate 3D tracking with divisions

##### `Fluo_N2DL_HeLa()`
- 2D cell tracking dataset
- From Cell Tracking Challenge
- Dimensions: 2D+time
- ~20 MB download
- Use case: Demonstrate 2D tracking workflow

##### `Fluo_N2DL_HeLa_crop()`
- Cropped version of HeLa dataset
- Smaller size for quick testing
- Use case: Fast demonstrations

**Features:**
- Uses `pooch` for dataset downloading and caching
- Returns as napari-compatible arrays
- Includes associated ground truth (where available)

#### [launcher.py](src/motile_tracker/launcher.py) (~50 lines)

Entry point for launching the plugin from napari.

**Functions:**
- `create_main_app_widget(viewer)` - Factory for MainApp widget
- `create_tree_widget(viewer)` - Factory for TreeWidget
- `register_example_data()` - Register sample datasets with napari

**Purpose:** Napari plugin registration hooks

#### [napari.yaml](src/motile_tracker/napari.yaml) (~50 lines)

Napari plugin manifest defining all plugin contributions.

**Registered Commands:**
- `motile_tracker.main_app` - Launch main application widget
- `motile_tracker.tree_widget` - Launch tree view widget
- `motile_tracker.mouse_embryo` - Load mouse embryo example
- `motile_tracker.hela` - Load HeLa example
- `motile_tracker.hela_crop` - Load cropped HeLa example

**Widgets:**
- Main widget appears in Plugins > Motile > Motile Main Widget
- Tree widget can be added independently

**Purpose:** Define plugin interface with napari

#### [\_\_init\_\_.py](src/motile_tracker/__init__.py)

Package initialization and public API exports.

**Exports:**
- From `application_menus`: MainApp, MenuWidget, EditingMenu
- From `data_views`: TracksViewer, TreeWidget, TrackPoints, TrackLabels, TrackGraph
- From `motile.backend`: MotileRun, SolverParams, solve
- From `import_export`: ImportDialog

**Purpose:** Define public API surface

#### [\_\_main\_\_.py](src/motile_tracker/__main__.py) (~30 lines)

Command-line entry point.

**Function:** `main()`

**Behavior:**
1. Launches napari viewer
2. Loads MainApp widget
3. Opens viewer window

**Usage:**
```bash
python -m motile_tracker
# or
motile_tracker  # if installed
```

**Purpose:** Allow running application from command line

---

## Summary of Source Folder Statistics

| Folder | Files | Lines of Code | Primary Purpose |
|--------|-------|---------------|-----------------|
| [application_menus/](src/motile_tracker/application_menus/) | 5 | ~411 | Top-level UI orchestration and menu management |
| [data_views/](src/motile_tracker/data_views/) | 33 | ~6,087 | Data visualization, coordination, and state management |
| [motile/](src/motile_tracker/motile/) | 11 | ~2,004 | Tracking solver backend and UI |
| [import_export/](src/motile_tracker/import_export/) | 11 | ~1,795 | Data import/export in multiple formats |
| **Total** | **60+** | **~10,297** | Complete tracking application |

---

## Key Classes and Their Relationships

```
MainApp (application_menus/)
    ├── MenuWidget
    │   ├── MotileWidget (motile/menus/)
    │   │   ├── RunEditor → solve() → MotileRun
    │   │   └── RunViewer
    │   ├── TracksList
    │   ├── EditingMenu
    │   ├── CollectionWidget
    │   └── LabelVisualizationWidget
    │
    ├── TreeWidget (data_views/views/tree_view/)
    │   └── pyqtgraph visualization
    │
    └── TracksViewer (data_views/views_coordinator/) ⭐ CENTRAL COORDINATOR
        ├── TracksLayerGroup
        │   ├── TrackPoints (napari.layers.Points)
        │   ├── TrackLabels (napari.layers.Labels)
        │   └── TrackGraph (napari.layers.Shapes)
        │
        ├── NodeSelectionList
        ├── TracksList
        └── CollectionWidget
```

---

**Available Datasets:**
- `Mouse_Embryo_Membrane()` - 3D membrane tracking (downloads from Zenodo)
- `Fluo_N2DL_HeLa()` - 2D cell tracking (from Cell Tracking Challenge)
- `Fluo_N2DL_HeLa_crop()` - Cropped 2D cell data

---

## Technology Stack

### Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| **napari** | ≥0.6.2 | Image viewer framework |
| **motile** | ≥0.3 | ILP-based tracking solver |
| **motile_toolbox** | 0.4.0 | Candidate graph construction & utilities |
| **funtracks** | ≥1.7.0-a2 | Track data model and controller |
| **numpy** | ≥2 | Numerical computing |
| **networkx** | - | Graph representation and algorithms |
| **Qt/QtPy** | ≥2.4 | GUI framework |
| **pydantic** | ≥2 | Data validation |
| **psygnal** | - | Signal/slot system |
| **scikit-image** | ≥0.25 | Image processing |
| **magicgui** | ≥0.10.1 | GUI generation from functions |

### Optional Performance Enhancements

| Extra | Library | Purpose |
|-------|---------|---------|
| `numba` | numba≥0.62.1 | JIT compilation for fast graph building |
| `gurobi` | gurobipy | Commercial solver (faster than open-source, requires license) |
| `gurobi12` | gurobipy≥12,<13 | Gurobi 12.x compatibility |
| `gurobi13` | gurobipy≥13,<14 | Gurobi 13.x compatibility |

### Development Tools

| Tool | Purpose |
|------|---------|
| **uv** | Dependency management |
| **ruff** | Code linting and formatting |
| **pytest** | Testing framework |
| **pytest-qt** | Qt testing |
| **sphinx** | Documentation generation |
| **pre-commit** | Git hooks for code quality |

---

## Data Flow

```
User Input (napari layer selection)
    ↓
RunEditor (configures parameters)
    ↓
solve() function
    ├→ _build_candidate_graph (motile_toolbox)
    ├→ construct_solver (motile library)
    └→ solver.solve() (returns networkx DiGraph)
    ↓
MotileRun (wraps solution)
    ↓
TracksViewer.tracks_updated signal
    ↓
Layer updates (TrackPoints, TrackLabels, TrackGraph)
    ↓
napari Visualization
```

---

## Key Design Patterns

1. **Singleton Pattern**
   - `TracksViewer.get_instance(viewer)` ensures single coordinator across application

2. **Signal/Slot Pattern**
   - psygnal signals for decoupled communication
   - Signals: `tracks_updated`, `mode_updated`, `center_node`, etc.

3. **MVC-like Architecture**
   - **Model:** TracksViewer + MotileRun
   - **View:** Qt widgets + napari layers
   - **Controller:** Signal connections and event handlers

4. **Factory Pattern**
   - Layer creation via `TracksLayerGroup`

5. **Pydantic Validation**
   - `SolverParams` for type-safe configuration

---

## Entry Points

### 1. Command Line
```bash
motile_tracker  # Starts napari with main widget loaded
```

### 2. Napari Plugin
- Manifest: [napari.yaml](src/motile_tracker/napari.yaml)
- Accessible via Plugins > Motile > Motile Main Widget
- Commands registered for MainApp, TreeWidget, and example data

### 3. Example Datasets
- File > Open Sample > Motile
- Loads sample 2D+time and 3D+time data

---

## Testing

### Test Structure
```
tests/
├── conftest.py                           # Shared fixtures
├── motile/
│   ├── backend/
│   │   ├── test_solver.py               # Solver functionality
│   │   └── test_motile_run.py           # Run serialization
│   └── menus/
│       └── test_run_editor.py           # UI components
└── import_export/
    ├── test_import_dialog.py            # Import dialog
    ├── test_export_dialog.py            # Export dialog
    └── test_export_solution_to_csv.py   # CSV export
```

### Running Tests
```bash
# Using justfile
just test

# Using pytest directly
pytest tests/

# With coverage
pytest --cov=motile_tracker tests/
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| [pyproject.toml](pyproject.toml) | Project metadata, dependencies, build config, tool settings (ruff, mypy) |
| [napari.yaml](src/motile_tracker/napari.yaml) | Napari plugin registration |
| [.pre-commit-config.yaml](.pre-commit-config.yaml) | Code quality checks |
| [justfile](justfile) | Common task shortcuts (test, start, docs-build) |
| [uv.lock](uv.lock) | Locked dependencies |

---

## Key Features

### Tracking Capabilities
- **Segmentation-based tracking:** Track objects from label images
- **Point-based tracking:** Track from point coordinates
- **Global optimization:** Uses ILP for optimal assignments
- **Chunked solving:** Handle large datasets with windowed approach
- **Cost customization:** Configure appearance, division, distance, and IOU costs

### Interactive Editing
- **Node operations:** Delete nodes, swap labels
- **Edge operations:** Break edges, add edges
- **Track management:** Start new tracks, merge tracks
- **Selection tools:** Multi-node selection
- **Undo/redo:** (via napari)

### Visualization
- **Lineage tree view:** Hierarchical track visualization
- **Track graph:** Edge visualization in spatial view
- **Color customization:** Colormap options
- **Orthogonal views:** 3D data exploration
- **Time navigation:** Scrub through time points

### Data Management
- **Import:** CSV, GEFF, napari layers
- **Export:** CSV, napari layers
- **Save/load runs:** Persist solver parameters and results
- **Collections:** Group tracks for analysis

---

## Development Workflow

### Setup
```bash
# Clone repository
git clone https://github.com/funkelab/motile_tracker.git
cd motile_tracker

# Install with uv
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Common Tasks
```bash
# Start application
just start

# Run tests
just test

# Build documentation
just docs-build

# Format code
ruff format src/

# Lint code
ruff check src/
```

### Release Process
1. Tag branch (e.g., `v1.2.3` or `v1.2.3-rc1`)
2. GitHub Actions automatically:
   - Pushes to PyPI
   - Creates GitHub release (draft if `-dev`, pre-release if `-rc`)
3. On release publish, creates installers for Linux, Mac, Windows

---

## File Statistics

- **Total Python Files:** ~65
- **Lines of Code:** ~9,000+ (excluding tests)
- **Main Modules:** 4 (application_menus, data_views, motile, import_export)
- **Test Files:** 8+
- **Documentation Pages:** 5+ RST files

---

## Documentation Structure

Located in [docs/source/](docs/source/):

| File | Content |
|------|---------|
| [index.rst](docs/source/index.rst) | Main documentation entry |
| [getting_started.rst](docs/source/getting_started.rst) | Installation and first steps |
| [motile.rst](docs/source/motile.rst) | Tracking solver usage |
| [editing.rst](docs/source/editing.rst) | Interactive editing guide |
| [tree_view.rst](docs/source/tree_view.rst) | Lineage tree visualization |
| [key_bindings.rst](docs/source/key_bindings.rst) | Keyboard shortcuts reference |

Built with Sphinx and published at https://funkelab.github.io/motile_tracker/

---

## Scripts

Example scripts in [scripts/](scripts/):

| Script | Purpose |
|--------|---------|
| [run_hela.py](scripts/run_hela.py) | Example tracking on HeLa dataset |
| [load_external_points.py](scripts/load_external_points.py) | Load point data from external sources |
| [view_external_tracks.py](scripts/view_external_tracks.py) | Visualize tracks from external data |
| [hela_example_tracks.csv](scripts/hela_example_tracks.csv) | Example CSV track data |

---

## Summary

Motile Tracker is a professional, well-architected scientific application that:

1. **Solves a real problem:** Provides global optimization for tracking in microscopy data using Integer Linear Programming
2. **User-friendly:** Interactive UI with napari integration, intuitive editing, and lineage tree visualization
3. **Extensible:** Modular design with clear separation of concerns across 4 main modules
4. **Well-tested:** Comprehensive test suite with pytest and pytest-qt
5. **Well-documented:** Sphinx documentation + inline docstrings + this comprehensive code map
6. **Modern Python:** Uses contemporary tools (uv, ruff, pydantic, psygnal, funtracks)
7. **Production-ready:** Stable release with CI/CD pipeline and GitHub releases

### Architecture Highlights

The codebase is organized into 60+ files with ~10,297 lines of code:

**Core Modules:**
- **application_menus/** (5 files, 411 lines) - Top-level UI orchestration
- **data_views/** (33 files, 6,087 lines) - Visualization, coordination, and state management
- **motile/** (11 files, 2,004 lines) - ILP solver backend and parameter management
- **import_export/** (11 files, 1,795 lines) - Data ingestion and output in multiple formats

**Key Components:**
- **TracksViewer** - Singleton coordinator managing all application state and signals
- **TracksLayerGroup** - Factory for napari layer management (Points, Labels, Graph)
- **TreeWidget** - Lineage tree visualization using pyqtgraph
- **solve()** - Core ILP solving pipeline with candidate graph construction
- **MotileRun** - Persistent container for tracking runs with full reproducibility

The architecture enables maintainability through:
- Clear separation between UI, coordination, visualization, and backend
- Signal-based decoupling using psygnal (tracks_updated, mode_updated, center_node)
- Type-safe configuration with Pydantic (SolverParams)
- Factory pattern for layer creation (TracksLayerGroup)
- Inheritance from funtracks.SolutionTracks for track data management
- Comprehensive testing with pytest and pytest-qt
- Professional development workflow with uv, ruff, and pre-commit hooks

### What This Document Provides

This comprehensive repository map includes:
- **Detailed file-by-file breakdown** of all 60+ source files
- **Class documentation** with key methods, signals, and attributes
- **Architecture diagrams** showing component relationships
- **Data flow explanations** from user input to visualization
- **Design pattern identification** (Singleton, Signal/Slot, MVC, Factory)
- **Usage examples** and entry points
- **Complete parameter reference** for the ILP solver
- **Import/export format specifications** (CSV, GEFF, napari layers)

Perfect for onboarding new developers, understanding the codebase architecture, or planning enhancements.

---

**Last Updated:** 2026-01-13
**Document Version:** 2.0 - Comprehensive Deep Dive
