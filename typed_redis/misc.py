class ClassWithParameter:
    """
    Adds a parameter to the class.

    This is necessary since Pydantic will "swallow" any extra parameters,
    but utilizing another class works instead.
    """

    model_name: str

    def __init_subclass__(cls, model_name: str | None = None, **kwargs: dict) -> None:
        """Initialize the subclass."""

        cls.model_name = model_name

        super().__init_subclass__(**kwargs)
