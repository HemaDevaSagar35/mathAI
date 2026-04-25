from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_all_models() -> None:
    """Import all models so Alembic can detect them."""
    import app.models.user  # noqa: F401
    import app.models.book  # noqa: F401
    import app.models.profile  # noqa: F401
    import app.models.concept  # noqa: F401
    import app.models.plan  # noqa: F401
    import app.models.tidbit  # noqa: F401
    import app.models.lesson  # noqa: F401
    import app.models.proof  # noqa: F401
    import app.models.quiz  # noqa: F401
    import app.models.question  # noqa: F401
    import app.models.grading  # noqa: F401
    import app.models.progress  # noqa: F401
    import app.models.memory  # noqa: F401
