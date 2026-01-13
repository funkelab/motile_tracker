# Testing Strategy for Motile Tracker

**Current Coverage:** ~40%
**Target Coverage:** 75-85%
**Generated:** 2026-01-13

---

## Executive Summary

The motile_tracker repository has significant testing gaps, particularly in UI components and core coordination logic. This document outlines a comprehensive strategy to improve test coverage from ~40% to 75-85% while focusing on high-value, maintainable tests.

### Current State Analysis

**Test Files Inventory:**

**Existing Tests (15 files, 2,912 total lines):**

| Location | File | Lines | Coverage | Status |
|----------|------|-------|----------|--------|
| tests/ | conftest.py | 174 | N/A | Shared fixtures |
| tests/motile/backend/ | test_solver.py | 77 | Good | Covers solve(), chunked solving |
| tests/motile/backend/ | test_motile_run.py | 29 | Good | Basic save/load test |
| tests/motile/menus/ | test_run_editor.py | 9 | Minimal | Only 1 test! |
| tests/import_export/ | test_import_dialog.py | 490 | Good | Comprehensive |
| tests/import_export/ | test_export_dialog.py | 154 | Good | Export scenarios |
| tests/import_export/ | test_export_solution_to_csv.py | 176 | Good | CSV export |
| tests/import_export/ | test_geff_scale_widget.py | 103 | Good | GEFF import |
| data_views/_tests/ | conftest.py | 73 | N/A | TracksViewer fixtures |
| data_views/_tests/ | test_track_labels.py | 211 | Good | Paint/erase events |
| data_views/_tests/ | test_center_view.py | 437 | Good | View centering |
| data_views/_tests/ | test_force_operations.py | 422 | Good | Force mode operations |
| data_views/_tests/ | test_link_clipping_planes.py | 117 | Good | 3D clipping |
| data_views/_tests/ | test_ortho_views.py | 100 | Good | Orthogonal views |
| data_views/_tests/ | test_tree_widget_utils.py | 152 | Minimal | Only 1 test! |
| data_views/_tests/ | test_visualization_widget.py | 188 | Good | Label visualization |

**Well-Tested Modules (>70% coverage):**
- ✅ Import/Export (63-100%) - 917 lines of tests
- ✅ Motile Backend solve.py (71%) - 77 lines of tests
- ✅ MotileRun (70%) - 29 lines of tests
- ✅ SolverParams (93%) - covered by other tests
- ✅ Scale widgets (100%) - part of import tests

**Under-Tested Modules (<20% coverage):**

| Module | Coverage | Missing Lines (examples) | Status |
|--------|----------|--------------------------|--------|
| **editing_menu.py** | 9% | Lines 16-76, 81-85, 96-112 | ❌ CRITICAL |
| **tracks_viewer.py** | 16% | Most methods untested | ❌ CRITICAL |
| **track_graph.py** | 14% | Lines 39-72, 84-100, 107-142 | ❌ HIGH |
| **track_points.py** | 18% | Lines 61-116, 147-259 | ❌ HIGH |
| **track_labels.py** | 16% | Lines 57-121, 223-303 | ⚠️ Has tests but gaps |
| **tracks_layer_group.py** | 13% | Lines 25-139, 145-194 | ❌ HIGH |
| **tree_widget.py** | 12% | Almost completely untested | ❌ HIGH |
| **tree_widget_utils.py** | 7% | Only 1 test exists | ❌ HIGH |
| **groups.py** | 12% | Collections functionality | ❌ MEDIUM |
| **navigation_widget.py** | 8% | Lines 35-187 | ❌ MEDIUM |
| **run_editor.py** | Only 9 lines tested | Most functionality untested | ❌ HIGH |

**Key Observations:**
1. **Import/Export is well-tested** (490+ lines for import_dialog alone)
2. **data_views has good fixture setup** but limited test coverage
3. **Many files have 0 dedicated tests** (TracksViewer, TrackGraph, TrackPoints, Groups, etc.)
4. **Existing tests are high quality** - good patterns to follow
5. **test_run_editor.py has only 9 lines** - barely scratches the surface

---

## Testing Priorities (High to Low)

### Priority 1: CRITICAL - Core Coordination Layer

**Target: TracksViewer (currently 16%)**

**Why Critical:**
- Singleton coordinator - central to entire application
- Manages all state and signal routing
- Currently has only 16% coverage despite being ~600 lines

**What to Test:**
1. **Singleton behavior**
   - Multiple `get_instance()` calls return same instance
   - Cleanup between tests

2. **Track management**
   - `update_tracks()` with different modes (all, selected, track)
   - Track visibility toggling
   - Track loading from MotileRun

3. **Node selection**
   - Single node selection
   - Multi-node selection (shift-click behavior)
   - Selection clearing
   - Selection persistence across mode changes

4. **Graph editing operations**
   - `delete_node()` with and without force
   - `add_edge()` between valid/invalid nodes
   - `swap_node_label()`
   - Edge validation (e.g., no edges within same timepoint)

5. **Signal emissions**
   - `tracks_updated` when tracks change
   - `mode_updated` when display mode changes
   - `center_node` when centering requested
   - `update_track_id` when track ID modified

6. **Colormap and symbol map handling**
   - Track colors assigned consistently
   - Symbol shapes for node types (END, CONTINUE, SPLIT)

7. **Integration with layers**
   - TracksLayerGroup properly updated
   - Layer visibility synced with track visibility

**Test Approach:**
- Use `make_napari_viewer` fixture
- Mock external dependencies where appropriate
- Use the existing `reset_tracks_viewer` fixture
- Test both 2D and 3D graphs

**Estimated Tests:** 25-30 tests

---

### Priority 2: HIGH - Napari Layer Classes

**Target: TrackPoints, TrackLabels, TrackGraph (13-18%)**

**Why Important:**
- User-facing visualization components
- Complex interaction with napari
- Critical for correct display and interaction

#### A. TrackPoints (currently 18%)

**What to Test:**
1. **Initialization and data**
   - Points created from graph nodes
   - Positions correct in 2D and 3D
   - Colors match track IDs

2. **Styling**
   - Symbol shapes based on node type
   - Size based on node area
   - Face colors for selected nodes

3. **Time-based visibility**
   - Only current timepoint nodes visible
   - Visibility updates when time changes

4. **Click interactions**
   - Click selects node
   - Shift-click appends to selection
   - Ctrl/Cmd-click centers view

5. **Updates on track changes**
   - Points refresh when tracks updated
   - Selection highlighting persists

**Estimated Tests:** 12-15 tests

#### B. TrackLabels (currently 16%)

**What to Test:**
1. **Segmentation display**
   - Labels colored by track ID
   - Original segmentation preserved
   - Dynamic relabeling works

2. **Paint mode**
   - Painting creates new nodes
   - Painting updates existing nodes
   - Paint respects selected_label
   - Track ID assignment correct

3. **Erase mode**
   - Erasing removes nodes or reduces size
   - Complete erasure removes node from graph
   - Partial erasure updates node area

4. **Undo/redo**
   - Undo restores previous state
   - Multiple undo levels work
   - Graph stays consistent

5. **Label validation**
   - `_ensure_valid_label()` enforces time constraints
   - New labels properly created via `new_label()`

6. **3D support**
   - Works with 3D segmentation
   - Lazy loading with dask arrays

**Note:** Some tests exist (`test_track_labels.py`) but coverage is still low - expand existing tests

**Estimated Tests:** 15-20 tests (expand existing)

#### C. TrackGraph (currently 14%)

**What to Test:**
1. **Edge rendering**
   - Lines drawn between connected nodes
   - Edges colored by track ID
   - 2D and 3D edge display

2. **Time-based visibility**
   - Only relevant edges shown at current time
   - Edges update when time changes

3. **Edge selection**
   - Click on edge selects it
   - Selected edges highlighted

4. **Graph updates**
   - Edges refresh when graph changes
   - Adding/removing edges reflected

**Estimated Tests:** 10-12 tests

#### D. TracksLayerGroup (currently 13%)

**What to Test:**
1. **Layer lifecycle**
   - `set_tracks()` creates all layers
   - `add_napari_layers()` adds to viewer
   - `remove_napari_layers()` cleans up

2. **Layer coordination**
   - All three layers (points, labels, graph) created together
   - Layers stay synchronized

3. **Clipping planes (3D)**
   - `link_clipping_planes()` syncs across layers
   - Clipping affects all layers equally

4. **View centering**
   - `center_view()` centers camera on node
   - Works in 2D and 3D

**Estimated Tests:** 8-10 tests

---

### Priority 3: HIGH - Application Menu Widgets

**Target: EditingMenu, MenuWidget, VisualizationWidget (9-23%)**

**Why Important:**
- Primary user interaction point
- Orchestrates all operations
- Low coverage indicates untested workflows

#### A. EditingMenu (currently 9%)

**What to Test:**
1. **Button interactions**
   - Start New Track button creates new track
   - Delete Node button removes selected node(s)
   - Swap Node Label updates segmentation
   - Break Edge splits track
   - Add Edge connects nodes

2. **Force mode**
   - Force toggle enables/disables operations
   - Confirmation dialog shown for destructive ops
   - Operations succeed with force=True

3. **Button state management**
   - Buttons enabled/disabled based on selection
   - Track ID display updates correctly

4. **Error handling**
   - Invalid operations show error messages
   - User confirmation for destructive actions

**Estimated Tests:** 12-15 tests

#### B. MenuWidget (currently 23%)

**What to Test:**
1. **Tab management**
   - All tabs created and accessible
   - Tab switching works
   - Each tab contains correct widget

2. **Widget initialization**
   - MotileWidget initialized
   - TracksList initialized
   - EditingMenu initialized
   - CollectionWidget initialized
   - LabelVisualizationWidget initialized

3. **Signal connections**
   - TracksViewer signals connected
   - Tab updates respond to track changes

**Estimated Tests:** 8-10 tests

#### C. VisualizationWidget (currently 17%)

**What to Test:**
1. **Layer selection**
   - Dropdown populated with label layers
   - Selection updates visualization

2. **Display controls**
   - Contour mode toggle
   - Color/opacity sliders work
   - Changes applied to layer

**Estimated Tests:** 6-8 tests

---

### Priority 4: MEDIUM - Tree View Components

**Target: TreeWidget, tree utilities (7-19%)**

**Why Important:**
- Unique visualization feature
- Complex pyqtgraph integration
- Currently almost completely untested

#### A. TreeWidget (currently 12%)

**What to Test:**
1. **Tree rendering**
   - Tree layout created from graph
   - Nodes positioned correctly
   - Time on X-axis, tracks on Y-axis

2. **Interactions**
   - Click selects node
   - Shift-drag rectangle selects multiple
   - Zoom/pan controls work

3. **Feature coloring**
   - Nodes colored by feature values
   - Colormap applied correctly
   - Feature range adjustable

4. **Signal coordination**
   - Selection syncs with TracksViewer
   - Center node request works

**Estimated Tests:** 15-20 tests

#### B. TreeWidgetUtils (currently 7%)

**What to Test:**
1. **Tree extraction**
   - `extract_lineage_tree()` creates correct structure
   - Parent-child relationships preserved

2. **Track sorting**
   - `extract_sorted_tracks()` orders correctly
   - Sorting stable

3. **Feature extraction**
   - `get_features_from_tracks()` retrieves data
   - Missing features handled

4. **Layout computation**
   - `compute_tree_layout()` positions nodes
   - No overlaps
   - Space used efficiently

**Estimated Tests:** 10-12 tests

#### C. Tree View Controls (8-19%)

**Navigation, Mode, Feature widgets**

**What to Test:**
- Mode switching (all/selected/track)
- Feature dropdown population
- Axis flipping controls
- Zoom controls
- Center on node functionality

**Estimated Tests:** 12-15 tests combined

---

### Priority 5: MEDIUM - Groups and Collections

**Target: groups.py (currently 12%)**

**Why Important:**
- User workflow feature
- Data persistence
- Complex UI interactions

**What to Test:**
1. **Collection CRUD**
   - Create new collection
   - Add/remove tracks from collection
   - Delete collection
   - Rename collection

2. **Collection viewing**
   - View all tracks in collection
   - Collection selection updates visualization

3. **Persistence**
   - Collections saved with MotileRun
   - Collections loaded from saved run

4. **UI interactions**
   - List updates when collection changes
   - Multi-select in track list

**Estimated Tests:** 10-12 tests

---

### Priority 6: MEDIUM - Other Coordinators

**Target: TracksList, NodeSelectionList, key_binds, user_dialogs (16-27%)**

#### A. TracksList (currently 20%)

**What to Test:**
- List population from tracks
- Track selection (single and multi)
- View all/selected tracks buttons
- List updates when tracks change

**Estimated Tests:** 6-8 tests

#### B. NodeSelectionList (currently 27%)

**What to Test:**
- `add_node()`, `remove_node()`, `clear()`
- `toggle_node()` behavior
- `list_updated` signal emission
- Selection order preservation
- Duplicate prevention

**Estimated Tests:** 8-10 tests

#### C. key_binds (currently 27%)

**What to Test:**
- Keybindings registered with napari
- Q key toggles display mode
- Click behaviors (select, append, center)
- Custom keybinds for operations

**Estimated Tests:** 6-8 tests

#### D. user_dialogs (currently 16%)

**What to Test:**
- `confirm_force_operation()` shows dialog
- Dialog returns correct value (Yes/No/Cancel)
- Different operation names displayed

**Estimated Tests:** 4-6 tests

---

### Priority 7: LOW - Well-Tested Modules

**Maintain existing coverage:**
- Import/Export (already well-tested)
- Solver (good coverage)
- MotileRun (decent coverage)

**Additional tests to consider:**
- Edge cases in CSV import
- Error handling in GEFF import
- More solver parameter combinations

**Estimated Tests:** 5-10 tests

---

## Learning from Existing Tests

### Excellent Examples to Follow

#### 1. test_track_labels.py (211 lines)
**What it does well:**
- Comprehensive paint event simulation
- Tests complete workflows (paint → update graph → verify)
- Uses `MockEvent` class for event simulation
- Tests undo/redo functionality
- Good use of assertions with explanatory comments

**Example pattern:**
```python
def test_paint_event(make_napari_viewer, graph_3d, segmentation_3d):
    """Test paint event processing with clear workflow steps"""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph=graph_3d, segmentation=segmentation_3d, ndim=4)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks=tracks, name="test")

    # 1) Test new label creation
    new_label(tracks_viewer.tracking_layers.seg_layer)
    assert tracks_viewer.tracking_layers.seg_layer.selected_label == 5

    # 2) Simulate paint event
    tracks_viewer.tracking_layers.seg_layer.mode = "paint"
    event_val = create_event_val(tp=3, z=(15, 20), y=(45, 50), x=(75, 80), ...)
    tracks_viewer.tracking_layers.seg_layer._on_paint(MockEvent(event_val))

    # 3) Verify results
    assert tracks_viewer.tracking_layers.seg_layer.data[3, 15, 45, 75] == 5
    assert tracks_viewer.tracks.get_track_id(5) == 4
```

**Why it's good:**
- Clear step-by-step structure
- Tests integration between multiple components
- Verifies both UI state and data model

#### 2. test_import_dialog.py (490 lines)
**What it does well:**
- Exhaustive coverage of import scenarios
- Tests error conditions and edge cases
- Good use of tmp_path fixture
- Tests both UI and backend logic
- Parametrized tests for different formats

**Example pattern:**
```python
@pytest.mark.parametrize("format_type", ["csv", "geff", "segmentation"])
def test_import_different_formats(format_type, tmp_path):
    # Test each import format
    pass
```

#### 3. test_force_operations.py (422 lines)
**What it does well:**
- Tests complex user interaction flows
- Mocks QMessageBox for dialogs
- Tests both success and failure paths
- Documents expected behavior in docstrings

**Example pattern:**
```python
def test_operation_with_confirmation(monkeypatch):
    """Test that operations requiring confirmation show dialog"""
    # Mock the dialog
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)

    # Perform operation
    result = tracks_viewer.delete_node(1, force=False)

    # Verify
    assert result is True
```

#### 4. test_solver.py (77 lines)
**What it does well:**
- Concise but comprehensive
- Tests both 2D and 3D
- Tests chunked solving variants
- Good validation of edge cases

**Example pattern:**
```python
def test_solve_2d(segmentation_2d, graph_2d):
    """Clean, focused test with fixtures"""
    params = SolverParams()
    params.appear_cost = None
    soln_graph = solve(params, segmentation_2d)
    assert set(soln_graph.nodes) == set(graph_2d.nodes)
```

### Patterns to Avoid (Anti-Patterns)

#### ❌ test_run_editor.py (9 lines - TOO MINIMAL)
```python
def test__has_duplicate_labels(segmentation_2d):
    assert not RunEditor._has_duplicate_ids(segmentation_2d)
    # Only tests one private method!
```

**What's wrong:**
- Only tests one private helper method
- Doesn't test main functionality
- Doesn't test UI interactions
- RunEditor is ~350 lines but has 9 lines of tests

#### ❌ test_tree_widget_utils.py (152 lines but only 1 test)
```python
def test_track_df(graph_2d):
    # One big test that does everything
    # Should be split into multiple focused tests
```

**What's wrong:**
- Only one test function despite 152 lines
- Test is doing too many things at once
- Hard to identify what failed if it breaks

---

## Testing Best Practices for This Codebase

### 1. Fixture Strategy

**Reuse existing fixtures:**
```python
# From tests/conftest.py
- segmentation_2d, segmentation_3d
- graph_2d, graph_3d

# From data_views/_tests/conftest.py
- reset_tracks_viewer (autouse for TracksViewer tests)
- graph_3d, segmentation_3d (data_views specific)
```

**Create new fixtures:**
```python
@pytest.fixture
def tracks_with_divisions(graph_2d):
    """Graph with division event for testing"""
    # Add division edges
    return modified_graph

@pytest.fixture
def napari_with_tracks(make_napari_viewer, graph_2d, segmentation_2d):
    """Pre-configured napari viewer with tracks loaded"""
    viewer = make_napari_viewer()
    tracks = SolutionTracks(graph_2d, segmentation_2d, ndim=3)
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(tracks, "test")
    return viewer, tracks_viewer
```

### 2. Mocking Strategy

**When to mock:**
- External I/O (file operations, network)
- Long-running operations (solver)
- User dialogs (QMessageBox)
- napari viewer methods when testing logic only

**When NOT to mock:**
- Core logic under test
- Simple data structures
- Fixtures (use real objects)

**Example:**
```python
# Good: Mock user dialog
def test_delete_with_confirmation(monkeypatch):
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    # test delete operation

# Good: Mock file I/O
def test_save_run(tmp_path, mocker):
    mocker.patch('motile_tracker.motile.backend.motile_run.save_json')
    # test save logic

# Bad: Don't mock what you're testing
def test_add_edge():
    # Don't mock TracksViewer.add_edge() when testing add_edge!
```

### 3. Qt Testing Patterns

**Use pytest-qt:**
```python
def test_button_click(qtbot, make_napari_viewer):
    viewer = make_napari_viewer()
    editing_menu = EditingMenu(viewer)

    # Use qtbot to interact with widgets
    qtbot.mouseClick(editing_menu.delete_node_btn, Qt.LeftButton)

    # Wait for signals
    with qtbot.waitSignal(tracks_viewer.tracks_updated, timeout=1000):
        # perform action that emits signal
        pass
```

**Test widget state:**
```python
def test_button_enabled_state():
    # Button disabled when no selection
    assert not editing_menu.delete_node_btn.isEnabled()

    # Button enabled after selection
    tracks_viewer.selected_nodes.add_node(1)
    assert editing_menu.delete_node_btn.isEnabled()
```

### 4. Signal Testing

**Test signal emissions:**
```python
def test_signal_emitted(qtbot):
    tracks_viewer = TracksViewer.get_instance(viewer)

    with qtbot.waitSignal(tracks_viewer.tracks_updated, timeout=1000):
        tracks_viewer.update_tracks(tracks, "test")
```

**Test signal connections:**
```python
def test_signal_connected():
    # Verify signal connected to slot
    assert tracks_viewer.tracks_updated.receivers > 0

    # Or use spy
    spy = QSignalSpy(tracks_viewer.tracks_updated)
    # perform action
    assert len(spy) == 1  # signal emitted once
```

### 5. Test Organization

**File structure:**
```
tests/
├── conftest.py                      # Shared fixtures
├── motile/
│   ├── backend/
│   │   ├── test_solve.py           # Existing
│   │   ├── test_motile_run.py      # Existing
│   │   └── test_solver_params.py   # NEW
│   └── menus/
│       ├── test_run_editor.py      # Existing (expand)
│       ├── test_motile_widget.py   # NEW
│       └── test_params_editor.py   # NEW
├── application_menus/
│   ├── test_editing_menu.py        # NEW
│   ├── test_menu_widget.py         # NEW
│   └── test_visualization_widget.py # NEW
├── data_views/
│   ├── conftest.py                 # Existing
│   ├── views_coordinator/
│   │   ├── test_tracks_viewer.py   # NEW (critical!)
│   │   ├── test_tracks_list.py     # NEW
│   │   ├── test_node_selection.py  # NEW
│   │   ├── test_groups.py          # NEW
│   │   └── test_key_binds.py       # NEW
│   ├── layers/
│   │   ├── test_track_points.py    # NEW
│   │   ├── test_track_labels.py    # Existing (expand)
│   │   ├── test_track_graph.py     # NEW
│   │   └── test_layer_group.py     # NEW
│   └── tree_view/
│       ├── test_tree_widget.py     # NEW
│       ├── test_tree_utils.py      # Existing (expand)
│       └── test_tree_controls.py   # NEW
└── import_export/
    └── [existing tests - maintain]
```

### 6. Test Naming Conventions

**Use descriptive names:**
```python
# Good
def test_delete_node_removes_from_graph():
def test_delete_node_with_force_removes_edges():
def test_add_edge_fails_within_same_timepoint():

# Bad
def test_delete():
def test_edge():
```

### 7. Parameterized Tests

**Use pytest.mark.parametrize for variations:**
```python
@pytest.mark.parametrize("ndim,expected_shape", [
    (3, (5, 100, 100)),  # 2D+time
    (4, (5, 100, 100, 100)),  # 3D+time
])
def test_segmentation_shapes(ndim, expected_shape):
    # test with both 2D and 3D
    pass

@pytest.mark.parametrize("mode", ["all", "selected", "track"])
def test_display_modes(mode):
    tracks_viewer.update_tracks(mode=mode, visible=[])
    # verify mode applied
```

---

## Implementation Roadmap

### Phase 1: Critical Foundation (Week 1-2)
**Goal: 50% coverage**

1. **TracksViewer comprehensive tests** (Priority 1)
   - 25-30 tests covering all methods
   - Signal emission verification
   - State management

2. **TrackLabels expansion** (Priority 2B)
   - Expand existing tests
   - Cover paint/erase modes
   - Undo/redo testing

3. **EditingMenu tests** (Priority 3A)
   - All button operations
   - Force mode
   - Error handling

**Deliverable:** Core coordination and editing fully tested

### Phase 2: Visualization Components (Week 3-4)
**Goal: 65% coverage**

1. **Napari Layers** (Priority 2A, 2C, 2D)
   - TrackPoints complete testing
   - TrackGraph testing
   - TracksLayerGroup testing

2. **Tree View Components** (Priority 4)
   - TreeWidget basic tests
   - TreeWidgetUtils tests
   - Control widget tests

**Deliverable:** Visualization components adequately tested

### Phase 3: Polish and Edge Cases (Week 5-6)
**Goal: 75-85% coverage**

1. **Remaining coordinators** (Priority 5-6)
   - Groups/Collections
   - TracksList
   - NodeSelectionList
   - Dialogs

2. **Menu widgets** (Priority 3B, 3C)
   - MenuWidget
   - VisualizationWidget

3. **Edge cases and integration**
   - Error paths
   - Boundary conditions
   - Multi-component workflows

**Deliverable:** Comprehensive test suite, 75%+ coverage

---

## Detailed Test Creation Guide

This section provides specific guidance for creating each test file, including exactly what to test and example test signatures.

### NEW FILE: tests/data_views/views_coordinator/test_tracks_viewer.py

**Target:** TracksViewer (currently 16%, ~600 lines)
**Estimated:** 25-30 tests

```python
# Test file structure
"""
Comprehensive tests for TracksViewer - the central coordinator singleton.
Tests cover initialization, track management, selection, editing, and signals.
"""

import pytest
import networkx as nx
from motile_tracker.data_views.views_coordinator.tracks_viewer import TracksViewer

class TestTracksViewerSingleton:
    def test_get_instance_creates_singleton(make_napari_viewer):
        """Verify singleton pattern - same instance returned"""

    def test_get_instance_without_viewer_raises_error():
        """Verify error when no viewer provided"""

    def test_singleton_persists_state(make_napari_viewer):
        """Verify state maintained across get_instance calls"""

class TestTrackManagement:
    def test_update_tracks_all_mode(make_napari_viewer, graph_2d, segmentation_2d):
        """Test loading tracks in 'all' display mode"""

    def test_update_tracks_selected_mode(make_napari_viewer, graph_2d):
        """Test 'selected' mode only shows selected tracks"""

    def test_update_tracks_track_mode(make_napari_viewer, graph_2d):
        """Test 'track' mode shows single track"""

    def test_update_tracks_emits_signal(qtbot, make_napari_viewer):
        """Verify tracks_updated signal emitted"""

    def test_tracks_visibility_toggled(make_napari_viewer, graph_2d):
        """Test toggling track visibility"""

class TestNodeSelection:
    def test_add_node_to_selection(make_napari_viewer, graph_2d):
        """Test selecting a single node"""

    def test_add_multiple_nodes(make_napari_viewer, graph_2d):
        """Test multi-node selection"""

    def test_clear_selection(make_napari_viewer, graph_2d):
        """Test clearing all selections"""

    def test_selection_persists_across_time_changes(make_napari_viewer):
        """Verify selection maintained when changing timepoint"""

class TestGraphEditing:
    def test_delete_node_simple(make_napari_viewer, graph_2d):
        """Test deleting a node without force"""

    def test_delete_node_with_force(make_napari_viewer, graph_2d):
        """Test force delete with confirmation"""

    def test_delete_node_updates_graph(make_napari_viewer, graph_2d):
        """Verify node removed from graph"""

    def test_add_edge_valid(make_napari_viewer, graph_2d):
        """Test adding edge between valid nodes"""

    def test_add_edge_same_time_fails(make_napari_viewer, graph_2d):
        """Verify edge within same timepoint rejected"""

    def test_swap_node_label(make_napari_viewer, graph_2d, segmentation_2d):
        """Test swapping segmentation label"""

    def test_editing_emits_signals(qtbot, make_napari_viewer):
        """Verify appropriate signals emitted on edits"""

class TestColormapAndSymbols:
    def test_colormap_assigned_to_tracks(make_napari_viewer, graph_2d):
        """Verify each track gets a color"""

    def test_symbol_map_for_node_types(make_napari_viewer):
        """Test END/CONTINUE/SPLIT node symbols"""

class TestLayerIntegration:
    def test_layers_created_on_track_load(make_napari_viewer, graph_2d):
        """Verify TracksLayerGroup initialized"""

    def test_layers_updated_on_track_change(make_napari_viewer):
        """Test layers refresh when tracks modified"""
```

**Implementation notes:**
- Use `reset_tracks_viewer` fixture (autouse)
- Mock confirmation dialogs with `monkeypatch`
- Test both 2D and 3D where applicable
- Use `qtbot.waitSignal()` for signal testing

---

### NEW FILE: tests/application_menus/test_editing_menu.py

**Target:** EditingMenu (currently 9%, ~150 lines)
**Estimated:** 12-15 tests

```python
"""
Tests for EditingMenu - the track editing UI widget.
Tests button interactions, force mode, and error handling.
"""

class TestButtonInteractions:
    def test_start_new_track_button(make_napari_viewer, qtbot):
        """Test Start New Track button creates new track"""

    def test_delete_node_button_single(make_napari_viewer, qtbot, graph_2d):
        """Test Delete Node with single selection"""

    def test_delete_node_button_multiple(make_napari_viewer, qtbot):
        """Test Delete Node with multiple selections"""

    def test_swap_label_button(make_napari_viewer, qtbot):
        """Test Swap Node Label updates segmentation"""

    def test_break_edge_button(make_napari_viewer, qtbot):
        """Test Break Edge splits track"""

    def test_add_edge_button(make_napari_viewer, qtbot):
        """Test Add Edge connects two nodes"""

class TestForceMode:
    def test_force_toggle_enables_operations(make_napari_viewer):
        """Test force checkbox enables/disables operations"""

    def test_force_delete_shows_confirmation(make_napari_viewer, monkeypatch):
        """Verify confirmation dialog shown for force delete"""

    def test_force_operation_succeeds(make_napari_viewer, monkeypatch):
        """Test operation succeeds with force=True"""

class TestButtonStates:
    def test_buttons_disabled_no_selection(make_napari_viewer):
        """Verify buttons disabled when nothing selected"""

    def test_buttons_enabled_with_selection(make_napari_viewer, graph_2d):
        """Verify buttons enabled after node selection"""

    def test_track_id_display_updates(make_napari_viewer, graph_2d):
        """Test track ID label updates on selection"""

class TestErrorHandling:
    def test_invalid_operation_shows_error(make_napari_viewer, monkeypatch):
        """Test error message shown for invalid operations"""
```

---

### NEW FILE: tests/data_views/views/layers/test_track_points.py

**Target:** TrackPoints (currently 18%, ~400 lines)
**Estimated:** 12-15 tests

```python
"""
Tests for TrackPoints layer - points layer displaying node positions.
"""

class TestInitializationAndData:
    def test_points_created_from_graph(make_napari_viewer, graph_2d):
        """Verify points layer created with correct data"""

    def test_positions_correct_2d(make_napari_viewer, graph_2d):
        """Test 2D node positions"""

    def test_positions_correct_3d(make_napari_viewer, graph_3d):
        """Test 3D node positions"""

    def test_colors_match_track_ids(make_napari_viewer, graph_2d):
        """Verify point colors from colormap"""

class TestStyling:
    def test_symbol_shapes_by_node_type(make_napari_viewer, graph_with_division):
        """Test END=x, CONTINUE=disc, SPLIT=triangle"""

    def test_size_based_on_area(make_napari_viewer, graph_2d):
        """Verify point size reflects node area"""

    def test_selected_nodes_highlighted(make_napari_viewer, graph_2d):
        """Test face color changes for selected nodes"""

class TestTimeBasedVisibility:
    def test_only_current_time_visible(make_napari_viewer, graph_2d):
        """Verify only current timepoint nodes shown"""

    def test_visibility_updates_on_time_change(make_napari_viewer, graph_2d):
        """Test points update when viewer time changes"""

class TestClickInteractions:
    def test_click_selects_node(make_napari_viewer, qtbot, graph_2d):
        """Test clicking point selects node"""

    def test_shift_click_appends_selection(make_napari_viewer, qtbot):
        """Test shift-click adds to selection"""

    def test_ctrl_click_centers_view(make_napari_viewer, qtbot):
        """Test ctrl/cmd-click centers camera"""

class TestUpdates:
    def test_points_refresh_on_track_change(make_napari_viewer, graph_2d):
        """Verify points update when tracks modified"""
```

---

### NEW FILE: tests/data_views/views/layers/test_track_graph.py

**Target:** TrackGraph (currently 14%, ~300 lines)
**Estimated:** 10-12 tests

```python
"""
Tests for TrackGraph layer - shapes layer displaying edges.
"""

class TestEdgeRendering:
    def test_lines_drawn_between_nodes(make_napari_viewer, graph_2d):
        """Verify edges rendered as lines"""

    def test_edges_colored_by_track(make_napari_viewer, graph_2d):
        """Test edge colors match track colormap"""

    def test_2d_edge_display(make_napari_viewer, graph_2d):
        """Test 2D edge visualization"""

    def test_3d_edge_display(make_napari_viewer, graph_3d):
        """Test 3D edge visualization"""

class TestTimeBasedVisibility:
    def test_only_relevant_edges_shown(make_napari_viewer, graph_2d):
        """Verify only current time edges visible"""

    def test_edges_update_on_time_change(make_napari_viewer, graph_2d):
        """Test edge visibility updates with time"""

class TestEdgeSelection:
    def test_click_selects_edge(make_napari_viewer, qtbot, graph_2d):
        """Test clicking edge selects it"""

    def test_selected_edges_highlighted(make_napari_viewer, graph_2d):
        """Verify selected edge highlighting"""

class TestGraphUpdates:
    def test_edges_refresh_on_add(make_napari_viewer, graph_2d):
        """Test adding edge updates display"""

    def test_edges_refresh_on_remove(make_napari_viewer, graph_2d):
        """Test removing edge updates display"""
```

---

### NEW FILE: tests/data_views/views/layers/test_layer_group.py

**Target:** TracksLayerGroup (currently 13%, ~200 lines)
**Estimated:** 8-10 tests

```python
"""
Tests for TracksLayerGroup - factory managing all track layers.
"""

class TestLayerLifecycle:
    def test_set_tracks_creates_all_layers(make_napari_viewer, graph_2d):
        """Verify points, labels, and graph layers created"""

    def test_add_napari_layers(make_napari_viewer, graph_2d):
        """Test layers added to viewer"""

    def test_remove_napari_layers(make_napari_viewer, graph_2d):
        """Test cleanup removes all layers"""

class TestLayerCoordination:
    def test_all_layers_created_together(make_napari_viewer, graph_2d):
        """Verify synchronous layer creation"""

    def test_layers_stay_synchronized(make_napari_viewer, graph_2d):
        """Test layers update together"""

class TestClippingPlanes3D:
    def test_link_clipping_planes(make_napari_viewer, graph_3d):
        """Test clipping plane synchronization"""

    def test_clipping_affects_all_layers(make_napari_viewer, graph_3d):
        """Verify clipping applied uniformly"""

class TestViewCentering:
    def test_center_view_on_node_2d(make_napari_viewer, graph_2d):
        """Test camera centering in 2D"""

    def test_center_view_on_node_3d(make_napari_viewer, graph_3d):
        """Test camera centering in 3D"""
```

---

### EXPAND: tests/motile/menus/test_run_editor.py

**Target:** RunEditor (currently 9 lines!, ~350 lines source)
**Estimated:** 15-20 new tests

```python
"""
Expanded tests for RunEditor - configuring and starting tracking runs.
Current file has only 1 test - needs comprehensive coverage.
"""

class TestUIComponents:
    def test_run_name_field_editable(make_napari_viewer):
        """Test run name can be set"""

    def test_layer_selection_dropdown_populated(make_napari_viewer):
        """Verify layer dropdown shows available layers"""

    def test_params_editor_initialized(make_napari_viewer):
        """Test SolverParamsEditor present"""

class TestRunExecution:
    def test_run_tracking_button_starts_solve(make_napari_viewer, mocker):
        """Test clicking Run Tracking calls solve()"""

    def test_progress_bar_shown_during_solve(make_napari_viewer, qtbot):
        """Verify progress indication during solving"""

    def test_start_run_signal_emitted(make_napari_viewer, qtbot):
        """Test start_run signal emitted on completion"""

    def test_motile_run_created_correctly(make_napari_viewer, mocker):
        """Verify MotileRun object created with correct params"""

class TestValidation:
    def test_no_layer_selected_shows_error(make_napari_viewer):
        """Test error when no segmentation selected"""

    def test_duplicate_labels_warning(make_napari_viewer, monkeypatch):
        """Test warning for duplicate IDs across time"""

    def test_large_dataset_warning(make_napari_viewer, monkeypatch):
        """Test warning for large datasets"""

    def test_invalid_parameters_prevented(make_napari_viewer):
        """Test Pydantic validation catches bad params"""

class TestErrorHandling:
    def test_solve_failure_shows_error(make_napari_viewer, mocker):
        """Test error message on solve failure"""

    def test_solver_exception_handled(make_napari_viewer, mocker):
        """Test graceful handling of solver exceptions"""
```

---

### NEW FILE: tests/data_views/views/tree_view/test_tree_widget.py

**Target:** TreeWidget (currently 12%, ~800 lines)
**Estimated:** 15-20 tests

```python
"""
Tests for TreeWidget - lineage tree visualization using pyqtgraph.
"""

class TestTreeRendering:
    def test_tree_layout_from_graph(make_napari_viewer, graph_with_division):
        """Verify tree structure extracted correctly"""

    def test_nodes_positioned_correctly(make_napari_viewer, graph_2d):
        """Test node positions in tree layout"""

    def test_time_on_x_axis(make_napari_viewer, graph_2d):
        """Verify X-axis represents time"""

    def test_tracks_on_y_axis(make_napari_viewer, graph_2d):
        """Verify Y-axis represents track IDs"""

class TestInteractions:
    def test_click_selects_node(make_napari_viewer, qtbot, graph_2d):
        """Test clicking node in tree selects it"""

    def test_shift_drag_rectangle_select(make_napari_viewer, qtbot):
        """Test rectangle selection with shift-drag"""

    def test_zoom_controls_work(make_napari_viewer, qtbot):
        """Test zoom in/out"""

    def test_pan_controls_work(make_napari_viewer, qtbot):
        """Test panning tree view"""

class TestFeatureColoring:
    def test_color_by_feature(make_napari_viewer, graph_with_features):
        """Test nodes colored by feature values"""

    def test_colormap_applied(make_napari_viewer, graph_with_features):
        """Verify colormap selection works"""

    def test_feature_range_adjustable(make_napari_viewer):
        """Test feature value range slider"""

class TestSignalCoordination:
    def test_selection_syncs_with_tracks_viewer(make_napari_viewer, qtbot):
        """Verify selection synchronized"""

    def test_center_node_request(make_napari_viewer, qtbot):
        """Test center_node signal emitted"""
```

---

### EXPAND: tests/data_views/views/tree_view/test_tree_widget_utils.py

**Current:** 152 lines but only 1 test
**Target:** 10-12 tests

```python
"""
Expand tree_widget_utils tests - currently only has test_track_df.
Need to split into multiple focused tests.
"""

class TestTreeExtraction:
    def test_extract_lineage_tree_structure(graph_with_division):
        """Test tree structure extraction"""

    def test_parent_child_relationships_preserved(graph_with_division):
        """Verify edges maintained correctly"""

    def test_extract_lineage_tree_handles_gaps(graph_with_gaps):
        """Test handling of time gaps in tracks"""

class TestTrackSorting:
    def test_extract_sorted_tracks(graph_2d):
        """Test track sorting (split from existing test)"""

    def test_sorted_tracks_stable(graph_2d):
        """Verify sorting is stable"""

    def test_sort_by_track_id(graph_2d):
        """Test sorting by track ID"""

class TestFeatureExtraction:
    def test_get_features_from_tracks(graph_with_features):
        """Test feature data extraction"""

    def test_missing_features_handled(graph_2d):
        """Test handling of missing feature data"""

    def test_custom_features_extracted(graph_with_custom_attrs):
        """Test custom attribute extraction"""

class TestLayoutComputation:
    def test_compute_tree_layout(graph_with_division):
        """Test node position calculation"""

    def test_layout_no_overlaps(graph_with_division):
        """Verify no node overlaps in layout"""

    def test_layout_efficient_space_use(graph_2d):
        """Test space utilization"""
```

---

## Measurement and CI Integration

### Coverage Targets by Module

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| application_menus/ | 9-23% | 70% | High |
| data_views/views_coordinator/ | 12-27% | 75% | Critical |
| data_views/views/layers/ | 13-30% | 70% | High |
| data_views/views/tree_view/ | 7-32% | 60% | Medium |
| motile/backend/ | 70-93% | 85% | Low |
| motile/menus/ | 24% | 65% | Medium |
| import_export/ | 63-100% | 80% | Low |
| **Overall** | **40%** | **75%** | - |

### CI/CD Integration

**Add to GitHub Actions workflow:**
```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=motile_tracker --cov-report=term --cov-report=xml tests/

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
    fail_ci_if_error: true

- name: Check coverage threshold
  run: |
    coverage report --fail-under=70
```

**Add coverage badge to README:**
```markdown
[![codecov](https://codecov.io/gh/funkelab/motile_tracker/branch/main/graph/badge.svg)](https://codecov.io/gh/funkelab/motile_tracker)
```

---

## Anti-Patterns to Avoid

### 1. ❌ Don't Test Implementation Details
```python
# Bad: Testing private method implementation
def test_internal_cache_structure():
    assert tracks_viewer._cache == {}  # Don't test private state

# Good: Test observable behavior
def test_tracks_cached_after_load():
    tracks_viewer.update_tracks(tracks, "test")
    # Second load should be faster (integration test)
```

### 2. ❌ Don't Test Third-Party Libraries
```python
# Bad: Testing networkx
def test_networkx_adds_edge():
    graph = nx.DiGraph()
    graph.add_edge(1, 2)
    assert (1, 2) in graph.edges  # This tests networkx, not our code

# Good: Test our usage of networkx
def test_add_edge_updates_visualization():
    tracks_viewer.add_edge(1, 2)
    # Test that our layer is updated
```

### 3. ❌ Don't Write Brittle Tests
```python
# Bad: Hardcoded coordinates
def test_node_at_exact_position():
    assert tracks_viewer.nodes[1]['pos'] == [50.00000001, 50.00000001]

# Good: Use tolerance
def test_node_near_expected_position():
    pos = tracks_viewer.nodes[1]['pos']
    np.testing.assert_allclose(pos, [50, 50], atol=0.1)
```

### 4. ❌ Don't Create Dependent Tests
```python
# Bad: Tests depend on execution order
def test_1_create_track():
    global track_id
    track_id = create_track()

def test_2_modify_track():
    modify_track(track_id)  # Depends on test_1!

# Good: Independent tests
@pytest.fixture
def track_id():
    return create_track()

def test_create_track(track_id):
    assert track_id is not None

def test_modify_track(track_id):
    modify_track(track_id)
```

---

## Success Metrics

### Quantitative Goals
- ✅ Overall coverage: 75-85%
- ✅ All critical modules (TracksViewer, EditingMenu) >70%
- ✅ No module below 50%
- ✅ All new PRs maintain >70% coverage for changed files

### Qualitative Goals
- ✅ Tests run in <2 minutes
- ✅ Tests are maintainable (don't break with refactoring)
- ✅ Tests document expected behavior
- ✅ Bugs found in production get regression tests

### Documentation
- ✅ Testing guide in CONTRIBUTING.md
- ✅ Fixture documentation in conftest.py
- ✅ Example tests for common patterns

---

## Resources and References

**Pytest Fixtures:**
- https://docs.pytest.org/en/stable/fixture.html
- https://docs.pytest.org/en/stable/how-to/parametrize.html

**pytest-qt:**
- https://pytest-qt.readthedocs.io/
- https://pytest-qt.readthedocs.io/en/latest/signals.html

**Napari Testing:**
- https://napari.org/stable/developers/testing.html
- `make_napari_viewer` fixture

**Coverage:**
- https://coverage.readthedocs.io/
- https://pytest-cov.readthedocs.io/

**Mocking:**
- https://docs.python.org/3/library/unittest.mock.html
- https://pytest-mock.readthedocs.io/

---

## Conclusion

This testing strategy prioritizes:
1. **Critical paths first** - TracksViewer, core editing
2. **User-facing features** - UI widgets, visualization
3. **Maintainability** - Clear patterns, good fixtures
4. **Incremental progress** - 40% → 50% → 65% → 75%

The phased approach allows for steady progress while maintaining existing functionality. Each phase delivers value and can be deployed independently.

**Next Steps:**
1. Review and approve this strategy
2. Set up coverage reporting in CI
3. Begin Phase 1 with TracksViewer tests
4. Track progress weekly
5. Adjust priorities based on bug reports and user feedback

---

**Estimated Effort:**
- **Total new tests:** ~180-220 tests
- **Phase 1 (Critical):** ~40-50 tests (2 weeks)
- **Phase 2 (Visualization):** ~60-80 tests (2 weeks)
- **Phase 3 (Polish):** ~50-70 tests (2 weeks)
- **Integration & cleanup:** 1 week

**Total timeline:** 6-7 weeks for comprehensive test suite achieving 75%+ coverage

---

## Implementation Workflow

### Step-by-Step Process for Each Test File

Follow this workflow when implementing tests:

#### 1. Setup Phase
```bash
# Create the test file
touch tests/path/to/test_module.py

# Run tests to verify setup
pytest tests/path/to/test_module.py -v
```

#### 2. Write Test Skeletons
```python
# Start with test class structure and method signatures
class TestFeatureName:
    def test_specific_behavior():
        pytest.skip("Not implemented yet")

    def test_another_behavior():
        pytest.skip("Not implemented yet")
```

**Why:** This lets you see the test structure and get early feedback

#### 3. Implement Tests One-by-One
```python
# Implement the first test
class TestFeatureName:
    def test_specific_behavior(make_napari_viewer, graph_2d):
        viewer = make_napari_viewer()
        # ... actual implementation
        assert expected == actual

    def test_another_behavior():
        pytest.skip("Not implemented yet")
```

#### 4. Run and Verify
```bash
# Run just this test file
pytest tests/path/to/test_module.py -v

# Check coverage for this module
pytest tests/path/to/test_module.py --cov=motile_tracker.module_name --cov-report=term-missing

# Look for uncovered lines and add tests
```

#### 5. Iterate
- Write test
- Run test
- Check coverage
- Identify gaps
- Add more tests
- Repeat

### Daily Development Pattern

**Morning:** Pick a test file from the priority list
```bash
# Example: Starting with TracksViewer
cp TESTING_STRATEGY.md /tmp/strategy_reference.md
touch tests/data_views/views_coordinator/test_tracks_viewer.py
```

**During Day:** Implement test classes one at a time
```bash
# Implement TestTracksViewerSingleton
pytest tests/data_views/views_coordinator/test_tracks_viewer.py::TestTracksViewerSingleton -v

# Then implement TestTrackManagement
pytest tests/data_views/views_coordinator/test_tracks_viewer.py::TestTrackManagement -v
```

**End of Day:** Commit progress
```bash
git add tests/data_views/views_coordinator/test_tracks_viewer.py
git commit -m "test: add TracksViewer singleton and track management tests

- Implemented TestTracksViewerSingleton (3 tests)
- Implemented TestTrackManagement (5 tests)
- Coverage for TracksViewer increased from 16% to 35%"
```

### Debugging Failed Tests

**Pattern 1: Test fails unexpectedly**
```bash
# Run with verbose output
pytest tests/path/to/test.py::test_name -vvs

# Add breakpoint in test
def test_something():
    import pdb; pdb.set_trace()
    # ... test code
```

**Pattern 2: Coverage not improving**
```bash
# See exactly which lines are covered
pytest tests/ --cov=motile_tracker --cov-report=html
open htmlcov/index.html  # View in browser

# Look at the specific module
open htmlcov/motile_tracker_module_name_py.html
```

**Pattern 3: Fixtures not working**
```bash
# List available fixtures
pytest --fixtures

# Show fixture setup for a test
pytest tests/test_file.py::test_name --setup-show
```

### Code Review Checklist

Before submitting PR:
- [ ] All tests pass locally
- [ ] Coverage increased for modified module
- [ ] Test names are descriptive
- [ ] Tests are independent (can run in any order)
- [ ] Used appropriate fixtures
- [ ] Mocked external dependencies
- [ ] Tested both success and failure paths
- [ ] Added docstrings to test classes
- [ ] No skipped tests remaining (unless intentional)
- [ ] Ran `ruff format` on test files

### Example PR Description Template

```markdown
## Tests: [Module Name]

Implements comprehensive test coverage for [module name].

### Changes
- Created `tests/path/to/test_module.py` ([X] tests)
- Expanded existing test coverage in [file]
- Added new fixtures: [fixture_name]

### Coverage Impact
- **Before:** X%
- **After:** Y%
- **Change:** +Z%

### Tests Added
#### TestClassName1 (N tests)
- test_feature_a
- test_feature_b

#### TestClassName2 (M tests)
- test_feature_c
- test_feature_d

### Testing Notes
[Any special considerations, tricky tests, or areas needing review]

### Checklist
- [x] All tests pass
- [x] Coverage increased
- [x] Tests follow patterns from TESTING_STRATEGY.md
- [x] Code formatted with ruff
```

---

## Quick Reference: Common Test Patterns

### Pattern: Testing Singleton
```python
def test_singleton(make_napari_viewer):
    viewer = make_napari_viewer()
    instance1 = TracksViewer.get_instance(viewer)
    instance2 = TracksViewer.get_instance(viewer)
    assert instance1 is instance2
```

### Pattern: Testing Signal Emission
```python
def test_signal_emitted(qtbot, make_napari_viewer):
    viewer = make_napari_viewer()
    tracks_viewer = TracksViewer.get_instance(viewer)

    with qtbot.waitSignal(tracks_viewer.tracks_updated, timeout=1000):
        tracks_viewer.update_tracks(tracks, "test")
```

### Pattern: Testing Button Click
```python
def test_button_click(qtbot, make_napari_viewer):
    viewer = make_napari_viewer()
    menu = EditingMenu(viewer)

    qtbot.mouseClick(menu.delete_btn, Qt.LeftButton)
    # Assert expected behavior
```

### Pattern: Mocking User Dialog
```python
def test_with_confirmation(monkeypatch, make_napari_viewer):
    monkeypatch.setattr(QMessageBox, 'question',
                       lambda *args: QMessageBox.Yes)

    # Perform operation that requires confirmation
    result = tracks_viewer.delete_node(1, force=True)
    assert result is True
```

### Pattern: Testing Error Handling
```python
def test_invalid_operation():
    with pytest.raises(InvalidActionError, match="Cannot add edge"):
        tracks_viewer.add_edge(1, 1)  # Same node
```

### Pattern: Parametrized Tests
```python
@pytest.mark.parametrize("mode", ["all", "selected", "track"])
def test_display_modes(mode, make_napari_viewer):
    viewer = make_napari_viewer()
    tracks_viewer = TracksViewer.get_instance(viewer)
    tracks_viewer.update_tracks(mode=mode, visible=[])
    assert tracks_viewer.mode == mode
```

### Pattern: Testing 2D and 3D
```python
@pytest.mark.parametrize("graph_fixture,ndim", [
    ("graph_2d", 3),
    ("graph_3d", 4),
])
def test_both_dimensions(graph_fixture, ndim, request, make_napari_viewer):
    graph = request.getfixturevalue(graph_fixture)
    # Test with both 2D and 3D
```

**Total timeline:** 6-7 weeks for comprehensive test suite achieving 75%+ coverage
