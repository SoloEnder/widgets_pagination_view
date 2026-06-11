
# widgets_pagination_view
This module contain the most used (and almost all) components of this package.

## `class` WidgetsPaginationView()
The `WidgetsPaginationView()` class is the class that handle your widgets, their placement, and all the logics behind.

### Publics Methods
#### `__init__(self, parent, max_loadables_pages_count, widgets_by_page_count, widgets, **config)`
- `parent: QtWidgets.QWidget` is a PySide6.QtWidgets.QWidget instance, usually the parent of this widget
- `max_loadables_pages_count: int` specifies the number of widgets's pages that can be loaded into memory simultaneously. A high value may cause the widget to slow down.
- `widgets_by_page_count: int` specifies the maximum number of widgets that can be displayed on each page. The program will attempt to distribute the number of widgets displayed on each page evenly according to this number.
- `**config: **kwargs` is used for pass additionall configuration arguments. There are two configuration arguments availables :
    - `switch_page_buttons_enabled: bool=True` indicate wheter or not to show buttons for change page at the bottom of the widget
    - `switch_page_entry_enabled: bool=True` indicate whether or not to show the field used for page switching

#### `set_widgets(self, widgets)`
This method replace all the current widgets by those given in the `widgets` argument, and refresh the whole widget
- `widgets: InPageWidgetsList`: the new widgets

#### `delete_widget(self, widget: InPageWidget)`
This method remove `widget` from the widgets. Raises a WidgetNotFoundError if `widget` does not exists in the WidgetsPaginationView.

#### `remove_page(self, page_index, re_setup: bool=True, ignore_unload_error: bool=True)`
Deletes the widgets page located at `page_index`
- `page_index: int`: The index of the page (given in the attibute 'virtual_index' of a `Page` instance)
- `re_setup: bool=True`: Indicates whether to call the `setup_pages_slices` method which distributes the widgets across the different pages
- `ignore_unload_error`: Since this method will attempt to unload the page with 'page_index', without checking if the page is actually loaded, this argument indicates whether to raise or ignore the `PageNotFoundError` exception raised when attempting to unload an unloaded page.

