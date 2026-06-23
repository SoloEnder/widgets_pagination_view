from __future__ import annotations

import logging
import typing

from PySide6 import QtWidgets

from .exceptions import InvalidWidgetIndexError, PageNotLoadedError, WidgetNotFoundError


class WidgetsPaginationView(QtWidgets.QWidget):
    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        max_loadables_pages_count: int,
        widgets_by_page_count: int,
        widgets: InPageWidgetsList,
        **config,
    ):
        super().__init__(parent)

        # Assigning arguments to attr
        self._widgets_by_page_count = widgets_by_page_count
        self.max_loadables_pages_count = max_loadables_pages_count
        self._widgets = widgets
        self.config = config

        # Setup logger
        self.logger = logging.getLogger()

        # Config variables
        self._switch_page_entry_enabled = self.config.get(
            "switch_page_entry_enabled", True
        )
        self._switch_page_buttons_enabled = self.config.get(
            "switch_page_buttons_enabled", True
        )

        self.pages_data = []
        self.pages_virtual_row = []
        self.loaded_pages = []
        self.pages_switch_history = []

        self.fixed_size_policy = QtWidgets.QSizePolicy()
        self.main_lyt = QtWidgets.QGridLayout()
        self.setLayout(self.main_lyt)

        # The stacked widget which handle the widgets
        self.pages_widgets_sw = QtWidgets.QStackedWidget(self)

        # Widgets for pages numbers buttons
        self.pages_numbers_widget = QtWidgets.QWidget(self)
        self.pages_numbers_widget_lyt = QtWidgets.QHBoxLayout(self.pages_numbers_widget)
        self.pages_numbers_widget.setLayout(self.pages_numbers_widget_lyt)
        self.pages_numbers_lyt_widgets: list[QtWidgets.QPushButton] = []

        # Widgets for jump to a specific page by giving its index
        self.jump_to_page_lb = QtWidgets.QLabel("Go to :")
        self.jump_to_page_lb.setSizePolicy(self.fixed_size_policy)
        self.jump_to_page_e = QtWidgets.QLineEdit("")
        self.jump_to_page_e.setSizePolicy(self.fixed_size_policy)
        self.jump_to_page_e.returnPressed.connect(
            lambda: self._jump_to_page(self.jump_to_page_e.text())
        )

        self.pages_numbers_widget_lyt.addWidget(self.jump_to_page_lb)
        self.pages_numbers_widget_lyt.addWidget(self.jump_to_page_e)

        self.main_lyt.addWidget(self.pages_widgets_sw, 0, 0)
        self.main_lyt.addWidget(self.pages_numbers_widget, 1, 0)

        self.generate_pages()
        self._apply_config()

    @property
    def widgets(self):
        """
        Getter of property 'widgets'
        """
        return self._widgets

    @widgets.setter
    def widgets(self, new_widgets: InPageWidgetsList):
        """
        Setter of property 'widgets'
        """

        for page_data in self.pages_data.copy():
            self.remove_page(page_data[0])

        self.pages_switch_history.clear()
        self._widgets = new_widgets
        self.generate_pages()

    @widgets.deleter
    def widgets(self):
        """
        Empty the widgets list
        """

        self._widgets = []

    @property
    def widgets_by_pages_count(self):
        return self._widgets_by_page_count

    @widgets_by_pages_count.setter
    def widgets_by_pages_count(self, new_value):
        """
        Setter of property 'widgets_by_pages_count'
        """

        self._widgets_by_page_count = new_value
        self.setup_pages_slices()
        self.generate_pages()
        self._widgets_by_page_count = new_value

    def _apply_config(self):
        for page_button in self.pages_numbers_lyt_widgets:
            page_button.setVisible(self._switch_page_buttons_enabled)

        self.jump_to_page_lb.setVisible(self._switch_page_entry_enabled)
        self.jump_to_page_e.setVisible(self._switch_page_entry_enabled)

    def _fill_virt_row(self):
        """
        Append 'None' to the 'pages_virtual_row' attribute for every page_data found in the 'pages_data' attribute\n
        All existing values in 'pages_virtual_row' will be erased
        """

        self.pages_virtual_row.clear()

        for page_data in self.pages_data:
            self.pages_virtual_row.append(None)

    def delete_widget(self, widget: InPageWidget):
        page_destroyed_index = None

        for page in self.loaded_pages.copy():
            self.unload_page(page)

        if isinstance(widget.index, int):
            self.logger.debug(f"Destroying widget with virtual index={widget.index} !")

            if self._widgets[widget.index] == widget:
                del self._widgets[widget.index]

            else:
                raise WidgetNotFoundError(widget)

            for widget in self._widgets[widget.index :]:
                if isinstance(widget.index, int) and widget.index >= 0:
                    widget.set_index(widget.index - 1)

                else:
                    raise InvalidWidgetIndexError(widget)

            self._shift_slice(-1, -1, "RIGHT")

        if self.pages_data[-1][1][0] == self.pages_data[-1][1][1]:
            page_destroyed_index = self.pages_data[-1][0]
            self.logger.debug(
                f"Removing page with virtual index={self.pages_data[-1][0]}"
            )
            self.remove_page(self.pages_data[-1][0], False)

            if len(self.pages_data) > 5:
                self._generate_pages_buttons([0, 1, 2, 3, 4, len(self.pages_data) - 1])

            else:
                self._generate_pages_buttons([i for i in range(len(self.pages_data))])

        pages_data_count = len(self.pages_data)

        if page_destroyed_index is not None and pages_data_count > 1:
            for i in self.pages_switch_history:
                if i != page_destroyed_index:
                    self.switch_to_page(i)
                    break

        elif pages_data_count > 1:
            self.switch_to_page(self.pages_switch_history[0])

        else:
            self.switch_to_page(0)

    def remove_page(
        self, page_index, re_setup: bool = True, ignore_unload_error: bool = True
    ):
        """
        Removes the page and its data at 'page_index' in the 'virtual_row' attribute

        Args:
        - page_index: the page index
        - re_setup: Wether or not call the 'setup_pages_slices' method after deleting the page.You should call it by yourself otherwise
        - ignore_unload_error: Whether ignore the my_exception.PageNotLoaded exception raised by the 'unload_page_with_index' method. Default to True
        """

        try:
            self.unload_page_with_index(page_index)

        except PageNotLoadedError:
            if not ignore_unload_error:
                raise

        del self.pages_data[page_index]
        del self.pages_virtual_row[page_index]

        if re_setup:
            self.setup_pages_slices()

    def _shift_slice(
        self,
        page_data_index: int,
        shift_value: int,
        shift_side: typing.Literal["LEFT", "RIGHT"],
    ):

        if shift_side == "RIGHT":
            pages_data = self.pages_data[page_data_index]
            pages_data[1] = (pages_data[1][0], pages_data[1][1] + shift_value)

        elif shift_side == "LEFT":
            pages_data = self.pages_data[page_data_index]
            pages_data[1] = (pages_data[1][0] + shift_value, pages_data[1][1])

        else:
            raise ValueError(
                f"Unkown value given for argument 'shift_side' : {shift_side}. Valid value : 'RIGHT', 'LEFT'"
            )

    def setup_pages_slices(self):
        current_page_index = 0
        slice_start = 0
        slice_end = 0
        page_data = []
        widgets_count = len(self._widgets)
        self.pages_data.clear()
        self.pages_virtual_row.clear()

        for index, widget in enumerate(self._widgets):
            widget.set_index(index)
            widget.set_pages_widgets_handler(self)

            if (index + 1) % self._widgets_by_page_count == 0:
                slice_start = slice_end
                slice_end = index + 1
                page_data = [current_page_index, (slice_start, slice_end)]
                current_page_index += 1
                self.pages_data.append(page_data.copy())
                self.pages_virtual_row.append(None)

        if slice_end != widgets_count:
            slice_start = slice_end
            slice_end = widgets_count
            page_data = [current_page_index, (slice_start, slice_end)]
            self.pages_data.append(page_data.copy())
            self.pages_virtual_row.append(None)

    def generate_pages(self):
        """
        Generate all pages widgets using the attribute 'pages_data'
        You should call the 'setup_pages_slices' method once before call this method
        """

        self.logger.debug(
            f"Loaded pages indexes={[page.virtual_index for page in self.loaded_pages]}"
        )
        for page in self.loaded_pages.copy():
            self.unload_page(page)

        self.setup_pages_slices()

        self.logger.info(f"Generating {self.max_loadables_pages_count} pages...")

        for page_data in self.pages_data[: self.max_loadables_pages_count]:
            self.new_page(page_data)

        pages_data_count = len(self.pages_data)

        if pages_data_count > 5:
            self._generate_pages_buttons([0, 1, 2, 3, 4, pages_data_count - 1])

        else:
            self._generate_pages_buttons([i for i in range(pages_data_count)])

        if len(self.pages_data) > 0:
            self.switch_to_page(0)

    def _generate_pages_buttons(self, pages_indexes: list | tuple):
        """
        Generates buttons for pages switching\n
        All previous button in the layout will be cleared !

        pages_indexes: the pages indexes used for pages switching (Note that the displayed index will be the given index+1)
        format_last_button: if True, a specific style will be applied to the last button
        """

        for widget in self.pages_numbers_lyt_widgets:
            self.pages_numbers_widget_lyt.removeWidget(widget)
            widget.deleteLater()

        self.pages_numbers_lyt_widgets.clear()

        for index in pages_indexes:
            button = QtWidgets.QPushButton(f"{index + 1}")
            button.clicked.connect(lambda qt_arg, i=index: self.switch_to_page(i))
            button.setSizePolicy(self.fixed_size_policy)
            self.pages_numbers_widget_lyt.addWidget(button)
            self.pages_numbers_lyt_widgets.append(button)

    def _jump_to_page(self, given_input):
        """
        Switch to the page given in 'given_input'\n
        Unlike switch_to_page(), this method takes a string as parameter, and evaluate if its a valid input\n
        Valid input requirements:
        - digit characters only
        - no space between characters
        - > 0 and < to 'pages_data' attribute
        Trying to call this method with an argument which doesn't follow these rule will result in a error window message raises
        """

        given_input = given_input.strip()

        if given_input.isdigit():
            given_input = int(given_input)

            if given_input > 0 and given_input <= len(self.pages_data):
                self.switch_to_page(given_input - 1)

            else:
                raise ValueError("Invalid page index !")

        else:
            raise ValueError("Invalid page index !")

    def get_widgets_with_slice(self, slice: tuple[int, int]) -> list[InPageWidget]:
        """
        Get and return all the widget which are contained inside 'slice'
        """
        return self._widgets[slice[0] : slice[1]]

    def new_page(self, page_data: list):
        """
        Creates and add to the stacked widgets a new 'page_data' object\n
        Equivalent to : 'self.add_page(self.create_pages(page_data))'
        """

        new_page = self.create_page(page_data)
        self.add_page(new_page)

    def create_page(self, page_data: list):
        """
        Create and return a new 'Page' object and return it
        """

        return Page(self, page_data[0], page_data[1])

    def add_page(self, page: Page):
        """
        Add 'page' to the stacked widgets
        """
        self.logger.debug(f"Adding page with index={page.virtual_index}")
        self.pages_widgets_sw.addWidget(page)
        self.pages_virtual_row[page.virtual_index] = page
        self.loaded_pages.append(page)

    def switch_to_page(self, index: int, make_page: bool = True):
        """
        Set the page displayed to the one's at 'index' int the 'pages_virtual_row' attribute

        Args:
        - index (int): the index of the page
        - make_page (bool, default to True): whether or not create the destination page if this is not the case

        Raises:
        - PagesNotLoadedError: if the destination page is not crated yet and make_page is equal to False
        """

        self.logger.debug(f"Switching to page with index={index}")

        if not len(self.pages_virtual_row) or index + 1 > len(self.pages_virtual_row):
            return

        dest_page = self.pages_virtual_row[index]

        if dest_page:
            self.pages_widgets_sw.setCurrentWidget(dest_page)
            self.pages_switch_history.insert(0, dest_page.virtual_index)

        else:
            if make_page:
                dest_page = self.create_page(self.pages_data[index])
                self.add_page(dest_page)
                self.pages_widgets_sw.setCurrentWidget(dest_page)
                self.pages_switch_history.insert(0, dest_page.virtual_index)

            else:
                raise PageNotLoadedError(index)
        self.smart_unload()

    def smart_unload(self):
        """
        This method check if the loaded pages count exceed the value of 'max_loadables_pages_count', and unload the exceeding pages if this is the case\n
        Pages to unload are determined by their position in the 'loaded_pages' attribute : first to last.
        """
        exceeding_pages = self.loaded_pages[: -self.max_loadables_pages_count]

        if exceeding_pages:
            self.logger.debug(
                f"Unloading {len(exceeding_pages)} exceedings pages, indexes={[exceeding_page.virtual_index for exceeding_page in exceeding_pages]}"
            )

            for exceeding_page in exceeding_pages:
                self.unload_page(exceeding_page)

    def unload_page_with_index(self, index: int):
        """
        Unloads the page at 'index' in the 'virtual_row' attribute\n
        Equivalent to call 'self.unload_page(self.virtual_row[index])'
        """

        page = self.pages_virtual_row[index]

        if page == None:
            raise PageNotLoadedError(index)

        else:
            self.unload_page(page)

    def unload_page(self, page: Page):
        """
        Removes 'page' from the widget which display them, and destroy it
        """

        try:
            self.loaded_pages.remove(page)

        except ValueError:
            raise PageNotLoadedError(page.virtual_index)

        self.pages_widgets_sw.removeWidget(page)
        self.pages_virtual_row[page.virtual_index] = None
        page.deleteLater()


class Page(QtWidgets.QWidget):
    def __init__(
        self,
        pages_widgets_handler: WidgetsPaginationView,
        virtual_index: int,
        widgets_slice: tuple[int, int],
    ):
        super().__init__(pages_widgets_handler)
        self.logger = logging.getLogger(__name__)
        self.pages_widgets_handler = pages_widgets_handler
        self._widgets_slice = widgets_slice
        self.virtual_index = virtual_index

        self.setProperty("role", "page")
        self.main_layout = QtWidgets.QGridLayout(self)
        self.setLayout(self.main_layout)

        self._widgets_container = QtWidgets.QWidget(self)
        self._widgets_container_layout = QtWidgets.QVBoxLayout(self._widgets_container)
        self._widgets_container.setLayout(self._widgets_container_layout)
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self._widgets_container)

        self.main_layout.addWidget(self.scroll_area, 3, 0)
        self.place_widgets()

        # if self.index == 0:
        #    self.default_shelf_widget = DefaultShelfWidget(
        #        self.books_handler.default_shelf,
        #        self.books_handler,
        #        self.qt_signals_handler,
        #    )

        #    self.shelfs_container_layout.addWidget(
        #        self.default_shelf_widget, QtCore.Qt.AlignmentFlag.AlignTop
        #    )

    def place_widgets(self):

        for widget in self.pages_widgets_handler.get_widgets_with_slice(
            self._widgets_slice
        ):
            self._widgets_container_layout.addWidget(widget)

    def deleteLater(self):
        for widget in self.pages_widgets_handler.get_widgets_with_slice(
            self._widgets_slice
        ):
            widget.setParent(None)

        return super().deleteLater()


class InPageWidget(QtWidgets.QWidget):
    def __init__(
        self,
        pages_widgets_handler: WidgetsPaginationView | None = None,
        index: int | None = None,
    ):
        super().__init__(None)
        self.index = index
        self.pages_widgets_handler = pages_widgets_handler

    def set_pages_widgets_handler(
        self, new_pages_widgets_handler: WidgetsPaginationView
    ):
        """
        Set the attribute 'pages_widgets_handler' to 'new_pages_widgets_handler''
        """

        self.pages_widgets_handler = new_pages_widgets_handler

    def set_index(self, new_index: int):
        """
        Set the attribute 'index' to 'new_index'
        """
        self.index = new_index


InPageWidgetsList = list[InPageWidget,]
