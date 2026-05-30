import unittest
from pathlib import Path
from unittest import mock

from slide_tui.app import ALL_CATEGORIES, UNCATEGORIZED, SlidePreviewer
from slide_tui.db import CategoryRow, SlideRow


def _row(slide_id: int, title: str, category: str) -> SlideRow:
    return SlideRow(
        id=slide_id,
        title=title,
        category=category,
        lock=0,
        version=0,
        sort_order=slide_id,
    )


def _previewer(rows: list[SlideRow]) -> SlidePreviewer:
    app = SlidePreviewer.__new__(SlidePreviewer)
    app.current_db = Path("/tmp/db.sqlite3")
    app.rows = rows
    app.categories = [ALL_CATEGORIES]
    app._category_index = 0
    app._slide_indices = {}
    app._slide_index = 0
    app.flash = None
    return app


class CategoryStateTests(unittest.TestCase):
    def test_sync_categories_combines_persisted_and_slide_categories(self):
        app = _previewer([
            _row(1, "One", "Talks"),
            _row(2, "Two", ""),
        ])

        with mock.patch(
            "slide_tui.db.list_categories",
            return_value=[CategoryRow("Demo", 0), CategoryRow("Talks", 1)],
        ):
            app._sync_categories()

        self.assertEqual(app.categories, [ALL_CATEGORIES, "Demo", "Talks", UNCATEGORIZED])

    def test_visible_rows_follow_current_category(self):
        app = _previewer([
            _row(1, "One", "Talks"),
            _row(2, "Two", "Demo"),
            _row(3, "Three", ""),
        ])
        with mock.patch("slide_tui.db.list_categories", return_value=[]):
            app._sync_categories()

        app._category_index = app.categories.index("Demo")
        self.assertEqual([row.id for row in app._visible_rows()], [2])

        app._category_index = app.categories.index(UNCATEGORIZED)
        self.assertEqual([row.id for row in app._visible_rows()], [3])

    def test_move_category_wraps(self):
        app = _previewer([_row(1, "One", "Talks")])
        with mock.patch("slide_tui.db.list_categories", return_value=[]):
            app._sync_categories()

        app._move_category(-1)
        self.assertEqual(app._current_category(), "Talks")
        app._move_category(1)
        self.assertEqual(app._current_category(), ALL_CATEGORIES)


if __name__ == "__main__":
    unittest.main()
