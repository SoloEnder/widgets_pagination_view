
class InvalidWidgetIndexError(Exception):

    def __init__(self, widget, msg: str|None=None):
        """
        Exception usually raised when the index of a 'InPageWidget' instance is not valid
        """
        self.widget = widget
        self.msg = msg or f"Invalid index for widget '{self.widget}' : {widget.index} !"
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg
    
class PageNotLoadedError(Exception):

    def __init__(self, index, msg: str|None=None):
        """
        Exception usualy raised when trying to do something on a page which is not loaded yet
        
        Args:
        - index: the page virtual index
        """
        self.index = index
        self.msg = msg or f"Page at virtual index '{index} not loaded !"
        super().__init__(self.msg)

    def __str__(self) -> str:
        return self.msg