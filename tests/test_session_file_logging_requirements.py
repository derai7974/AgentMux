from __future__ import annotations

import tempfile
import threading
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import agentmux.pipeline as pipeline


class SessionFileLoggingRequirementsTests(unittest.TestCase):
    def test_dispatcher_fan_out_wakes_and_logs_created_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            wake_event = threading.Event()
            dispatcher = pipeline.SessionFileEventDispatcher()
            logger = pipeline.CreatedFilesLogListener(
                feature_dir / "created_files.log",
                now=lambda: datetime(2026, 3, 25, 18, 50, 7),
            )
            dispatcher.register(pipeline.build_transition_wake_listener(wake_event))
            dispatcher.register(logger.handle_event)

            dispatcher.publish(
                pipeline.SessionFileEvent(
                    event_type=pipeline.FILE_EVENT_CREATED,
                    relative_path="03_research/code-topic/request.md",
                )
            )

            self.assertTrue(wake_event.is_set())
            self.assertEqual(
                "2026-03-25 18:50:07  03_research/code-topic/request.md\n",
                (feature_dir / "created_files.log").read_text(encoding="utf-8"),
            )

    def test_modification_and_duplicate_created_events_are_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            dispatcher = pipeline.SessionFileEventDispatcher()
            logger = pipeline.CreatedFilesLogListener(
                feature_dir / "created_files.log",
                now=lambda: datetime(2026, 3, 25, 18, 50, 7),
            )
            dispatcher.register(logger.handle_event)

            created = pipeline.SessionFileEvent(
                event_type=pipeline.FILE_EVENT_CREATED,
                relative_path="context.md",
            )
            dispatcher.publish(created)
            dispatcher.publish(
                pipeline.SessionFileEvent(
                    event_type=pipeline.FILE_EVENT_ACTIVITY,
                    relative_path="context.md",
                )
            )
            dispatcher.publish(created)

            self.assertEqual(
                ["2026-03-25 18:50:07  context.md"],
                (feature_dir / "created_files.log").read_text(encoding="utf-8").splitlines(),
            )

    def test_moved_file_is_logged_at_destination_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            dispatcher = pipeline.SessionFileEventDispatcher()
            logger = pipeline.CreatedFilesLogListener(
                feature_dir / "created_files.log",
                now=lambda: datetime(2026, 3, 25, 18, 50, 7),
            )
            dispatcher.register(logger.handle_event)
            handler = pipeline.FeatureEventHandler(feature_dir, dispatcher)

            handler.on_any_event(
                SimpleNamespace(
                    event_type="moved",
                    is_directory=False,
                    src_path="/tmp/tmp-file.txt",
                    dest_path=str(feature_dir / "04_design" / "design.md"),
                )
            )

            self.assertEqual(
                ["2026-03-25 18:50:07  04_design/design.md"],
                (feature_dir / "created_files.log").read_text(encoding="utf-8").splitlines(),
            )

    def test_seed_existing_files_logs_in_deterministic_order_once(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            feature_dir = Path(td)
            (feature_dir / "b.txt").write_text("b", encoding="utf-8")
            (feature_dir / "a").mkdir()
            (feature_dir / "a" / "a.txt").write_text("a", encoding="utf-8")

            dispatcher = pipeline.SessionFileEventDispatcher()
            logger = pipeline.CreatedFilesLogListener(
                feature_dir / "created_files.log",
                now=lambda: datetime(2026, 3, 25, 18, 50, 7),
            )
            dispatcher.register(logger.handle_event)

            pipeline.seed_existing_files(feature_dir, dispatcher)
            pipeline.seed_existing_files(feature_dir, dispatcher)

            self.assertEqual(
                [
                    "2026-03-25 18:50:07  a/a.txt",
                    "2026-03-25 18:50:07  b.txt",
                ],
                (feature_dir / "created_files.log").read_text(encoding="utf-8").splitlines(),
            )


if __name__ == "__main__":
    unittest.main()
