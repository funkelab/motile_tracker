# Testing Strategy for Motile Tracker

**Current Coverage:** 64% (Updated: 2026-01-13)
**Target Coverage:** 75-85%
**Generated:** 2026-01-13

---

## Executive Summary

After consolidating all tests into `/tests` directory and eliminating duplicate fixtures, coverage improved from ~40% to **64%**. This document outlines the remaining gaps and strategy to reach 75-85% coverage, focusing on UI widgets and tree view components.

### Current State Analysis (Updated)

**Test Organization:**
- ✅ **All tests consolidated** in `/tests` directory
- ✅ **Single conftest.py** with all fixtures
- ✅ **No duplicate fixtures** across test files
- 📊 **15 test files**, ~2,500 lines of tests
- 📊 **62 tests passing**, 1 xfailed

**Coverage by Category:**

| Category | Coverage | Status |
|----------|----------|--------|
| **Overall** | **64%** | 🟡 Good progress |
| Import/Export | 63-100% | ✅ Excellent |
| Motile Backend | 70-93% | ✅ Good |
| Visualization Layers | 76-95% | ✅ Good |
| Coordination Logic | 49-70% | 🟡 Decent |
| UI Menus/Widgets | 9-30% | ❌ Critical Gap |
| Tree View Components | 8-32% | ❌ Critical Gap |

**Well-Tested Modules (>70% coverage):**
- ✅ **visualization_widget.py** (94%) - Label visualization
- ✅ **contour_labels.py** (95%) - Contour rendering
- ✅ **track_graph.py** (94%) - Edge visualization
- ✅ **track_labels.py** (82%) - Paint/erase events
- ✅ **tracks_layer_group.py** (79%) - Layer management
- ✅ **ortho_views.py** (76%) - Orthogonal views
- ✅ **tracks_viewer.py** (70%) - Core coordinator ⬆️ from 16%!
- ✅ **Import/Export modules** (85-100%)
- ✅ **solve.py** (71%), **motile_run.py** (70%), **solver_params.py** (93%)

**Critical Gaps (<40% coverage - FOCUS HERE):**

| Module | Coverage | Lines | Status |
|--------|----------|-------|--------|
| **editing_menu.py** | 9% | 72 | ❌ CRITICAL - UI widget |
| **navigation_widget.py** | 8% | 86 | ❌ CRITICAL - Tree navigation |
| **tree_widget.py** | 12% | 375 | ❌ CRITICAL - 375 lines! |
| **tree_view_feature_widget.py** | 16% | 77 | ❌ HIGH - Feature coloring |
| **tree_view_mode_widget.py** | 19% | 34 | ❌ HIGH - Display modes |
| **params_editor.py** | 15% | 146 | ❌ HIGH - Solver params UI |
| **run_editor.py** | 23% | 132 | ❌ HIGH - Run configuration |
| **motile_widget.py** | 24% | 85 | 🟡 MEDIUM - Main widget |
| **run_viewer.py** | 24% | 81 | 🟡 MEDIUM - Run display |
| **params_viewer.py** | 21% | 49 | 🟡 MEDIUM - Param display |
| **tracks_list.py** | 34% | 125 | 🟡 MEDIUM - Track list UI |
| **param_values.py** | 30% | 32 | 🟡 MEDIUM - Value handling |
| **click_utils.py** | 30% | 16 | 🟡 MEDIUM - Click helpers |
| **flip_axes_widget.py** | 32% | 19 | 🟡 MEDIUM - Axis flipping |

**Medium Coverage (40-70% - Secondary Focus):**

| Module | Coverage | Lines | Notes |
|--------|----------|-------|-------|
| **track_points.py** | 47% | 143 | Needs interaction tests |
| **groups.py** | 49% | 254 | Group management logic |
| **node_selection_list.py** | 58% | 57 | Selection UI |
| **csv_import_widget.py** | 63% | 54 | CSV import UI |
| **geff_import_widget.py** | 64% | 68 | GEFF import UI |
| **tree_widget_utils.py** | 67% | 131 | Tree utilities |
| **segmentation_widgets.py** | 73% | 221 | Seg import UI |

**Key Achievements:**
1. ✅ **TracksViewer jumped from 16% to 70%** - excellent progress!
2. ✅ **All visualization layers now >75%** coverage
3. ✅ **Test consolidation successful** - single source of fixtures
4. ✅ **Import/export remains strong** (85-100%)

**Remaining Gaps:**
1. ❌ **UI widgets mostly untested** - editing_menu (9%), tree widgets (8-32%)
2. ❌ **Motile menu widgets** - run_editor (23%), params_editor (15%)
3. 🟡 **Some interaction logic** - track_points (47%), groups (49%)

---

## Testing Priorities (Revised Based on 64% Coverage)

### Priority 1: CRITICAL - UI Widgets (Biggest Impact)

**Target: Get to 75% overall by fixing lowest-hanging fruit**

These modules have **very low coverage** and are **user-facing**, making them high-impact:

#### 1A. editing_menu.py (9% → Target: 70%)
**Lines:** 72 | **Gap:** ~65 untested lines | **Est. Tests:** 12-15

**Why Critical:**
- Primary UI for track editing
- Users interact with this constantly
- Only 9% coverage despite being central feature

**What to Test:**
- Button click handlers (delete, add edge, swap label, break edge)
- Force mode checkbox behavior
- Button enable/disable based on selection
- Track ID label updates
- Error dialogs

#### 1B. navigation_widget.py (8% → Target: 70%)
**Lines:** 86 | **Gap:** ~76 untested lines | **Est. Tests:** 10-12

**Why Critical:**
- Tree view navigation controls
- Only 8% coverage - almost untested!

**What to Test:**
- Previous/next track navigation
- Center on selection
- Zoom controls
- Time navigation
- Signal emissions

#### 1C. tree_widget.py (12% → Target: 70%)
**Lines:** 375 (LARGEST file!) | **Gap:** ~317 untested lines | **Est. Tests:** 20-25

**Why Critical:**
- 375 lines with only 12% coverage
- Core lineage tree visualization
- Complex pyqtgraph integration

**What to Test:**
- Tree layout computation
- Node positioning and rendering
- Click selection
- Rectangle selection
- Feature-based coloring
- Zoom/pan controls
- Signal coordination with tracks_viewer

### Priority 2: HIGH - Motile Menu Widgets

#### 2A. params_editor.py (15% → Target: 70%)
**Lines:** 146 | **Gap:** ~118 untested lines | **Est. Tests:** 15-18

**What to Test:**
- Parameter input widgets
- Validation and constraints
- Save/load parameter sets
- UI updates on value changes
- Pydantic validation integration

#### 2B. run_editor.py (23% → Target: 70%)
**Lines:** 132 | **Gap:** ~95 untested lines | **Est. Tests:** 15-20

**What to Test:**
- Run name input
- Layer selection dropdown
- Start tracking button
- Progress indication
- Validation (duplicate IDs, dataset size)
- Error handling
- MotileRun creation

#### 2C. Tree View Widgets (16-19% → Target: 70%)
- **tree_view_feature_widget.py** (16%) - Feature coloring controls
- **tree_view_mode_widget.py** (19%) - Display mode selection

**Est. Tests:** 8-10 each

### Priority 3: MEDIUM - Complete Medium Coverage Modules

#### 3A. track_points.py (47% → Target: 75%)
**Lines:** 143 | **Gap:** ~64 untested lines | **Est. Tests:** 8-10

**What's Missing:**
- Click interaction handlers
- Shift/Ctrl-click modifiers
- Symbol shape updates
- Size scaling based on area

#### 3B. groups.py (49% → Target: 75%)
**Lines:** 254 | **Gap:** ~119 untested lines | **Est. Tests:** 15-18

**What's Missing:**
- Group creation and management
- Track grouping/ungrouping
- Group persistence
- Color assignment to groups
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

---

## Action Plan: 64% → 75%+ Coverage

### Phase 1: Critical UI Widgets (Target: +6-8% coverage)

**Goal:** Test the three lowest-coverage, highest-impact modules
**Timeline:** 2-3 weeks
**Coverage Impact:** 64% → 70-72%

#### Week 1: editing_menu.py (9% → 70%)
**File:** `tests/application_menus/test_editing_menu.py`

**Tests to Add (12-15 tests):**
```python
class TestButtonInteractions:
    def test_delete_node_button_enabled_with_selection()
    def test_delete_node_button_disabled_no_selection()
    def test_delete_node_calls_tracks_viewer_delete()
    def test_add_edge_button_enabled_two_nodes_selected()
    def test_add_edge_button_disabled_one_node_selected()
    def test_add_edge_calls_tracks_viewer_create_edge()
    def test_swap_label_button_enabled_with_selection()
    def test_swap_label_calls_swap_node_label()
    def test_break_edge_button_behavior()
    def test_start_new_track_button()

class TestForceMode:
    def test_force_checkbox_toggles_force_flag()
    def test_force_mode_shows_confirmation_dialog()
    def test_force_mode_always_skips_dialog()

class TestTrackIDDisplay:
    def test_track_id_label_updates_on_selection()
    def test_track_id_label_clears_no_selection()
```

**Commands:**
```bash
# Create test file
touch tests/application_menus/test_editing_menu.py

# Implement tests
pytest tests/application_menus/test_editing_menu.py -v --cov=src/motile_tracker/application_menus/editing_menu.py --cov-report=term-missing

# Expected: 9% → 70% (+5 lines to overall coverage)
```

#### Week 2: tree_widget.py (12% → 65%)
**File:** `tests/data_views/views/tree_view/test_tree_widget.py`

**Tests to Add (20-25 tests):**
```python
class TestTreeRendering:
    def test_tree_created_from_tracks()
    def test_nodes_positioned_by_time()
    def test_tracks_positioned_by_track_id()
    def test_division_nodes_branched()
    def test_tree_updates_on_track_change()

class TestNodeSelection:
    def test_click_selects_node()
    def test_shift_click_rectangle_select()
    def test_selection_syncs_to_tracks_viewer()
    def test_clear_selection()

class TestFeatureVisualization:
    def test_nodes_colored_by_feature()
    def test_colormap_applied()
    def test_feature_value_range()
    def test_feature_legend()

class TestInteractions:
    def test_zoom_in_out()
    def test_pan_tree()
    def test_center_on_node()
    def test_hover_shows_info()

class TestSignals:
    def test_node_selected_signal()
    def test_center_node_signal()
    def test_time_changed_signal()
```

**Commands:**
```bash
touch tests/data_views/views/tree_view/test_tree_widget.py
pytest tests/data_views/views/tree_view/test_tree_widget.py -v --cov=src/motile_tracker/data_views/views/tree_view/tree_widget.py --cov-report=term-missing

# Expected: 12% → 65% (+15 lines to overall)
```

#### Week 3: navigation_widget.py (8% → 70%)
**File:** `tests/data_views/views/tree_view/test_navigation_widget.py`

**Tests to Add (10-12 tests):**
```python
class TestNavigationControls:
    def test_previous_track_button()
    def test_next_track_button()
    def test_first_track_button()
    def test_last_track_button()
    def test_navigation_wraps_around()

class TestCenterControls:
    def test_center_on_selected_node()
    def test_center_disabled_no_selection()

class TestZoomControls:
    def test_zoom_to_fit_tree()
    def test_zoom_to_selection()

class TestTimeControls:
    def test_time_slider_updates_view()
    def test_time_input_field()
```

**Commands:**
```bash
touch tests/data_views/views/tree_view/test_navigation_widget.py
pytest tests/data_views/views/tree_view/test_navigation_widget.py -v --cov=src/motile_tracker/data_views/views/tree_view/navigation_widget.py --cov-report=term-missing

# Expected: 8% → 70% (+5 lines to overall)
```

**Phase 1 Result:** 64% → 70-72% overall coverage

---

### Phase 2: Motile Widgets (Target: +3-4% coverage)

**Goal:** Test solver parameter and run configuration UIs
**Timeline:** 2 weeks
**Coverage Impact:** 70-72% → 73-76%

#### Week 4: run_editor.py (23% → 70%)
**File:** Expand `tests/motile/menus/test_run_editor.py` (currently only 7 lines!)

**Tests to Add (15-20 tests):**
```python
class TestUIComponents:
    def test_run_name_field_editable()
    def test_layer_dropdown_populated()
    def test_params_editor_displayed()
    def test_run_button_enabled_with_layer()

class TestRunExecution:
    def test_run_button_calls_solve()
    def test_progress_shown_during_solve()
    def test_success_emits_start_run_signal()
    def test_motile_run_created_correctly()

class TestValidation:
    def test_no_layer_shows_error()
    def test_duplicate_ids_warning()
    def test_large_dataset_warning()
    def test_invalid_params_prevented()

class TestErrorHandling:
    def test_solve_failure_shows_error()
    def test_exception_handled_gracefully()
```

**Commands:**
```bash
pytest tests/motile/menus/test_run_editor.py -v --cov=src/motile_tracker/motile/menus/run_editor.py --cov-report=term-missing

# Expected: 23% → 70% (+6 lines to overall)
```

#### Week 5: params_editor.py (15% → 65%)
**File:** `tests/motile/menus/test_params_editor.py`

**Tests to Add (15-18 tests):**
```python
class TestParameterWidgets:
    def test_float_parameter_widget()
    def test_int_parameter_widget()
    def test_bool_parameter_widget()
    def test_enum_parameter_widget()

class TestValidation:
    def test_min_max_constraints()
    def test_invalid_input_rejected()
    def test_pydantic_validation()

class TestParameterSets:
    def test_load_parameter_set()
    def test_save_parameter_set()
    def test_reset_to_defaults()

class TestUIUpdates:
    def test_param_change_updates_ui()
    def test_dependent_params_update()
```

**Commands:**
```bash
touch tests/motile/menus/test_params_editor.py
pytest tests/motile/menus/test_params_editor.py -v --cov=src/motile_tracker/motile/menus/params_editor.py --cov-report=term-missing

# Expected: 15% → 65% (+7 lines to overall)
```

**Phase 2 Result:** 70-72% → 76-78% overall coverage

---

### Phase 3: Polish & Fill Gaps (Target: +2-3% coverage)

**Goal:** Complete medium-coverage modules to >70%
**Timeline:** 1-2 weeks
**Coverage Impact:** 76-78% → 78-80%

#### Week 6-7: Quick Wins

**3A. track_points.py (47% → 75%)**
- Add click handler tests
- Test shift/ctrl modifiers
- Test symbol shapes and sizing

**3B. Tree view widgets (16-32% → 70%)**
- tree_view_feature_widget.py
- tree_view_mode_widget.py
- flip_axes_widget.py

**3C. groups.py (49% → 70%)**
- Group creation/deletion
- Track grouping operations
- Color management

**Commands:**
```bash
# Expand existing test_track_points.py
pytest tests/data_views/views/layers/test_track_points.py -v

# Create tree view widget tests
touch tests/data_views/views/tree_view/test_tree_view_widgets.py
pytest tests/data_views/views/tree_view/test_tree_view_widgets.py -v

# Expand groups tests
touch tests/data_views/views_coordinator/test_groups.py
pytest tests/data_views/views_coordinator/test_groups.py -v
```

**Phase 3 Result:** 76-78% → 78-80% overall coverage

---

## Summary: Reaching 75%+ Coverage

### Coverage Trajectory

| Phase | Modules Tested | Coverage Target | Timeline |
|-------|----------------|-----------------|----------|
| **Current** | Base consolidation done | 64% | ✅ Complete |
| **Phase 1** | editing_menu, tree_widget, navigation_widget | 70-72% | 3 weeks |
| **Phase 2** | run_editor, params_editor | 76-78% | 2 weeks |
| **Phase 3** | track_points, groups, tree widgets | 78-80% | 2 weeks |
| **TOTAL** | 9-12 new test files | **78-80%** | **7 weeks** |

### Expected Line Coverage Gains

| Module | Current | Target | Lines Gained | Overall Impact |
|--------|---------|--------|--------------|----------------|
| editing_menu.py | 9% | 70% | ~44 lines | +0.9% |
| tree_widget.py | 12% | 65% | ~199 lines | +3.9% |
| navigation_widget.py | 8% | 70% | ~53 lines | +1.0% |
| run_editor.py | 23% | 70% | ~62 lines | +1.2% |
| params_editor.py | 15% | 65% | ~73 lines | +1.4% |
| track_points.py | 47% | 75% | ~40 lines | +0.8% |
| groups.py | 49% | 70% | ~53 lines | +1.0% |
| Tree widgets (3) | 16-32% | 70% | ~80 lines | +1.5% |
| **TOTAL** | | | **~604 lines** | **+11.7%** |

**Final Coverage:** 64% + 11.7% = **75.7%** ✅ TARGET MET!

### Quick Start Commands

```bash
# Check current coverage
pytest tests/ --cov=src/motile_tracker --cov-report=term-missing

# Start with Phase 1 - editing_menu
touch tests/application_menus/test_editing_menu.py
# Implement tests following patterns from existing tests
pytest tests/application_menus/test_editing_menu.py -v

# Continue with tree_widget (biggest impact)
touch tests/data_views/views/tree_view/test_tree_widget.py
pytest tests/data_views/views/tree_view/test_tree_widget.py -v

# Monitor progress
pytest tests/ --cov=src/motile_tracker --cov-report=html
open htmlcov/index.html
```

### Success Criteria

- ✅ Overall coverage >75%
- ✅ No modules <40% coverage
- ✅ All UI widgets >60% coverage
- ✅ All visualization layers >70% coverage
- ✅ All tests passing
- ✅ No duplicate fixtures

**Timeline:** 7 weeks to reach 75-80% coverage
